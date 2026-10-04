"""Input validation and sanitization utilities."""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import re
from utils.date_utils import parse_to_standard_date


def sanitize_text(text: Optional[str]) -> str:
    """Clean and strip extraneous whitespace and unwanted characters."""
    if not text:
        return ""
    # Strip null bytes and normalize whitespace
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text))
    return cleaned.strip()


def validate_date_string(date_str: str) -> bool:
    """Validate that date_str is exactly YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_deadline_dict(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate and normalize a raw deadline dictionary (e.g. from Gemini or UI form).
    Returns (is_valid, error_message, normalized_dict).
    """
    title = sanitize_text(data.get("title"))
    subject = sanitize_text(data.get("subject"))
    raw_date = str(data.get("date") or data.get("deadline_date") or "").strip()

    if not title:
        return False, "Title is required.", {}

    if not subject:
        # Default subject to General if missing
        subject = "General"

    standard_date = parse_to_standard_date(raw_date)
    if not standard_date:
        return False, f"Could not determine a valid date for deadline '{title}'. Raw date was '{raw_date}'.", {}

    deadline_type = sanitize_text(data.get("type")) or "Assignment"
    confidence = sanitize_text(data.get("confidence")).lower() or "high"
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"

    time_val = sanitize_text(data.get("deadline_time") or data.get("time"))
    if time_val:
        # Normalize HH:MM if possible
        time_match = re.match(r"^(\d{1,2}):(\d{2})$", time_val)
        if time_match:
            time_val = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        else:
            time_val = None
    else:
        time_val = None

    normalized = {
        "title": title,
        "subject": subject,
        "type": deadline_type.capitalize(),
        "deadline_date": standard_date,
        "deadline_time": time_val,
        "description": sanitize_text(data.get("description")),
        "confidence": confidence,
        "source_document": sanitize_text(data.get("source_document")) or "manual",
        "source_text": sanitize_text(data.get("source_text")),
        "completed": bool(data.get("completed", False)),
    }

    if "id" in data and data["id"] is not None:
        try:
            normalized["id"] = int(data["id"])
        except (ValueError, TypeError):
            pass

    return True, None, normalized
