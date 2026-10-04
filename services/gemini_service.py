"""Gemini Multimodal AI Service for Deadline Extraction and Academic Assistance."""
import json
import re
import os
from typing import List, Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from prompts.prompts import SYSTEM_EXTRACTION_PROMPT, AI_ASSISTANT_SYSTEM_PROMPT
from utils.validators import validate_deadline_dict

# Cache clients in memory by API key
_CLIENT_CACHE: Dict[str, genai.Client] = {}


def get_api_key(provided_key: Optional[str] = None) -> Optional[str]:
    """Retrieve Gemini API key from parameter, Streamlit secrets, or environment variable."""
    if provided_key and provided_key.strip():
        return provided_key.strip()

    # Try Streamlit secrets
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        pass

    # Try environment variables
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    return None


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """Return a cached Google GenAI Client instance."""
    resolved_key = get_api_key(api_key)
    if not resolved_key:
        raise ValueError(
            "Gemini API Key is not configured. Please add GEMINI_API_KEY to .streamlit/secrets.toml "
            "or enter it in the application Settings."
        )

    if resolved_key not in _CLIENT_CACHE:
        _CLIENT_CACHE[resolved_key] = genai.Client(api_key=resolved_key)
    return _CLIENT_CACHE[resolved_key]


def clean_json_response(raw_text: str) -> str:
    """Strip markdown backticks, explanations, or surrounding characters to isolate valid JSON."""
    if not raw_text:
        return ""

    cleaned = raw_text.strip()

    # Strip markdown ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()

    # If still not starting with [ or {, locate the outermost brackets
    if not (cleaned.startswith("[") or cleaned.startswith("{")):
        start_bracket = cleaned.find("[")
        end_bracket = cleaned.rfind("]")
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            cleaned = cleaned[start_bracket : end_bracket + 1]
        else:
            start_brace = cleaned.find("{")
            end_brace = cleaned.rfind("}")
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                cleaned = cleaned[start_brace : end_brace + 1]

    return cleaned


def parse_extracted_items(raw_json_str: str, source_doc: str = "document") -> List[Dict[str, Any]]:
    """Parse JSON string into a list of normalized deadline dictionaries."""
    cleaned = clean_json_response(raw_json_str)
    if not cleaned:
        return []

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback regex search for JSON objects
        json_objects = re.findall(r"\{[^{}]*\}", cleaned)
        data = []
        for obj_str in json_objects:
            try:
                data.append(json.loads(obj_str))
            except Exception:
                continue

    if isinstance(data, dict):
        # In case model returned {"deadlines": [...]} or single item
        if "deadlines" in data and isinstance(data["deadlines"], list):
            data = data["deadlines"]
        elif "events" in data and isinstance(data["events"], list):
            data = data["events"]
        else:
            data = [data]

    if not isinstance(data, list):
        return []

    normalized_items = []
    for item in data:
        if not isinstance(item, dict):
            continue
        item["source_document"] = source_doc
        is_valid, _, norm_dict = validate_deadline_dict(item)
        if is_valid:
            normalized_items.append(norm_dict)

    return normalized_items


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def test_connection(self) -> Tuple[bool, str]:
        """Test whether the configured Gemini API key is valid and accessible."""
        try:
            client = get_gemini_client(self.api_key)
            # Lightweight test call using gemini-2.5-flash or gemini-1.5-flash
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Ping. Respond with 'PONG'.",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            if response and response.text:
                return True, "Gemini API connected successfully."
            return False, "Received empty response from Gemini."
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "INVALID_ARGUMENT" in err_msg:
                return False, "Invalid Gemini API key. Please check your credentials."
            return False, f"Gemini connection failed: {err_msg}"

    def extract_deadlines(
        self,
        file_bytes: bytes,
        mime_type: str,
        filename: str = "document"
    ) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
        """
        Multimodal deadline extraction from uploaded document/image bytes.
        Supports images (PNG, JPEG, WEBP) and PDFs.
        """
        if not file_bytes:
            return False, "No file content received.", []

        try:
            client = get_gemini_client(self.api_key)

            # Determine appropriate Part
            part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[part, SYSTEM_EXTRACTION_PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature for factual precision
                ),
            )

            if not response or not response.text:
                return False, "Gemini couldn't analyze this document. Please try a clearer image.", []

            items = parse_extracted_items(response.text, source_doc=filename)
            if not items:
                return True, "Analysis complete, but no academic deadlines could be identified with high confidence.", []

            return True, None, items

        except Exception as e:
            err_str = str(e)
            if "API_KEY_INVALID" in err_str:
                return False, "Gemini API key is invalid. Please verify your key in Settings.", []
            elif "RESOURCE_EXHAUSTED" in err_str:
                return False, "Gemini API rate limit exceeded. Please wait a moment and try again.", []
            else:
                return False, f"Extraction failed: {err_str}", []

    def answer_assistant_query(
        self,
        user_query: str,
        deadlines_context: str
    ) -> Tuple[bool, str]:
        """
        AI Assistant that answers questions strictly using real database deadline context.
        """
        if not user_query.strip():
            return False, "Please enter a question."

        try:
            client = get_gemini_client(self.api_key)

            full_prompt = f"""{AI_ASSISTANT_SYSTEM_PROMPT}

CURRENT DATABASE DEADLINES CONTEXT:
{deadlines_context}

STUDENT QUESTION:
{user_query.strip()}

Remember: If the requested deadline is not in the context, clearly tell the student it is not recorded."""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config=types.GenerateContentConfig(temperature=0.2),
            )

            if response and response.text:
                return True, response.text.strip()
            return False, "I couldn't generate an answer. Please try again."

        except Exception as e:
            return False, f"Assistant error: {str(e)}"
