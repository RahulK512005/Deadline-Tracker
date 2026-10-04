"""Notification service supporting Telegram, Email, and extensible to WhatsApp."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os
from typing import Tuple, Optional, Dict, Any


def format_phone_number(raw_phone: str, default_country_code: str = "+91") -> str:
    """Format and sanitize phone number, ensuring international E.164 format."""
    if not raw_phone:
        return ""
    clean = "".join(ch for ch in str(raw_phone).strip() if ch.isdigit() or ch == "+")
    if not clean:
        return ""
    if clean.startswith("+"):
        return clean
    if len(clean) == 10:
        return f"{default_country_code}{clean}"
    if len(clean) == 12 and clean.startswith("91"):
        return f"+{clean}"
    return f"+{clean}"


def get_secret_or_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve secret from SQLite user settings, Streamlit secrets, or environment variable."""
    try:
        from database.database import get_setting
        val = get_setting(key.lower())
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


class NotificationService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def send_telegram(
        self,
        message: str,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Send a notification via Telegram Bot API.
        Returns (success: bool, status_message: str).
        """
        token = bot_token or self.config.get("telegram_bot_token") or get_secret_or_env("TELEGRAM_BOT_TOKEN")
        target_chat = chat_id or self.config.get("telegram_chat_id") or get_secret_or_env("TELEGRAM_CHAT_ID")

        if not token or not str(token).strip():
            return False, "Telegram Bot Token is missing. Please configure it in Settings."
        if not target_chat or not str(target_chat).strip():
            return False, "Telegram Chat ID is missing. Please configure it in Settings."

        clean_token = str(token).strip()
        clean_chat = str(target_chat).strip()
        url = f"https://api.telegram.org/bot{clean_token}/sendMessage"

        payload = {
            "chat_id": clean_chat,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            resp = requests.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                return True, "Telegram message sent successfully."
            else:
                err_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                desc = err_data.get("description", resp.text)
                return False, f"Telegram API error ({resp.status_code}): {desc}"
        except requests.exceptions.RequestException as e:
            return False, f"Telegram connection failed: {str(e)}"

    def send_email(
        self,
        subject: str,
        body_text: str,
        to_email: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: bool = True
    ) -> Tuple[bool, str]:
        """
        Send an email notification via SMTP.
        Returns (success: bool, status_message: str).
        """
        smtp_host = host or self.config.get("email_host") or get_secret_or_env("EMAIL_HOST")
        smtp_port = port or self.config.get("email_port") or get_secret_or_env("EMAIL_PORT", "587")
        user = username or self.config.get("email_username") or get_secret_or_env("EMAIL_USERNAME")
        pwd = password or self.config.get("email_password") or get_secret_or_env("EMAIL_PASSWORD")
        recipient = to_email or self.config.get("email_to") or user or get_secret_or_env("EMAIL_FROM")
        sender = from_email or self.config.get("email_from") or user

        if not smtp_host:
            return False, "SMTP Host is missing. Please configure it in Settings."
        if not user or not pwd:
            return False, "Email credentials (username or password) are missing. Please configure them in Settings."
        if not recipient:
            return False, "Recipient email is missing."

        try:
            port_num = int(smtp_port)
        except ValueError:
            port_num = 587

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        try:
            if port_num == 465:
                server = smtplib.SMTP_SSL(smtp_host, port_num, timeout=12.0)
            else:
                server = smtplib.SMTP(smtp_host, port_num, timeout=12.0)
                if use_tls:
                    server.starttls()

            server.login(user, pwd)
            server.sendmail(sender, [recipient], msg.as_string())
            server.quit()
            return True, f"Email delivered successfully to {recipient}."
        except smtplib.SMTPAuthenticationError:
            return False, "SMTP Authentication failed. Please verify your email and password."
        except Exception as e:
            return False, f"Email delivery failed: {str(e)}"

    def send_twilio_message(
        self,
        message: str,
        to_number: Optional[str] = None,
        from_number: Optional[str] = None,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        is_whatsapp: bool = False
    ) -> Tuple[bool, str]:
        """
        Send SMS or WhatsApp notification via Twilio REST API.
        Returns (success: bool, status_message: str).
        """
        sid = (
            account_sid
            or self.config.get("twilio_account_sid")
            or get_secret_or_env("TWILIO_ACCOUNT_SID")
            or get_secret_or_env("twilio_account_sid")
        )
        token = (
            auth_token
            or self.config.get("twilio_auth_token")
            or get_secret_or_env("TWILIO_AUTH_TOKEN")
            or get_secret_or_env("twilio_auth_token")
        )
        from_num = (
            from_number
            or self.config.get("twilio_from_number")
            or get_secret_or_env("TWILIO_PHONE_NUMBER")
            or get_secret_or_env("TWILIO_WHATSAPP_FROM")
            or ("+14155238886" if is_whatsapp else "")
        )
        to_num = (
            to_number
            or self.config.get("twilio_to_number")
            or get_secret_or_env("TWILIO_TO_NUMBER")
            or get_secret_or_env("twilio_to_number")
        )

        if not sid or not str(sid).strip():
            return False, "Twilio Account SID is missing. Please configure it in Settings or secrets.toml."
        if not token or not str(token).strip():
            return False, "Twilio Auth Token is missing. Please configure it in Settings or secrets.toml."
        if not from_num or not str(from_num).strip():
            return False, "Twilio Sender/From phone number is missing."
        if not to_num or not str(to_num).strip():
            return False, "Recipient phone number is missing."

        clean_sid = str(sid).strip()
        clean_token = str(token).strip()

        # Format and normalize phone numbers
        formatted_from = format_phone_number(str(from_num).replace("whatsapp:", ""))
        formatted_to = format_phone_number(str(to_num).replace("whatsapp:", ""))

        if is_whatsapp:
            target_from = f"whatsapp:{formatted_from}"
            target_to = f"whatsapp:{formatted_to}"
        else:
            target_from = formatted_from
            target_to = formatted_to

        url = f"https://api.twilio.com/2010-04-01/Accounts/{clean_sid}/Messages.json"
        payload = {
            "From": target_from,
            "To": target_to,
            "Body": message
        }

        try:
            resp = requests.post(url, data=payload, auth=(clean_sid, clean_token), timeout=12.0)
            if resp.status_code in (200, 201):
                data = resp.json()
                msg_sid = data.get("sid", "N/A")
                channel = "WhatsApp" if is_whatsapp else "SMS"
                return True, f"Twilio {channel} notification queued successfully (SID: {msg_sid}) to {target_to}."
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                return False, f"Twilio API error ({resp.status_code}): {err_msg}"
        except requests.exceptions.RequestException as e:
            return False, f"Twilio connection failed: {str(e)}"

    def send_whatsapp(
        self,
        message: str,
        to_number: Optional[str] = None,
        from_number: Optional[str] = None,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, str]:
        """
        Send a WhatsApp notification using Twilio WhatsApp API.
        """
        to_num = to_number or kwargs.get("to_wa") or kwargs.get("phone")
        from_num = from_number or kwargs.get("from_wa")
        sid = account_sid or kwargs.get("account_sid")
        token = auth_token or kwargs.get("auth_token")

        return self.send_twilio_message(
            message=message,
            to_number=to_num,
            from_number=from_num,
            account_sid=sid,
            auth_token=token,
            is_whatsapp=True
        )

    def send_sms(
        self,
        message: str,
        to_number: Optional[str] = None,
        from_number: Optional[str] = None,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        **kwargs
    ) -> Tuple[bool, str]:
        """
        Send a standard SMS text notification via Twilio.
        """
        to_num = to_number or kwargs.get("phone")
        from_num = from_number
        sid = account_sid or kwargs.get("account_sid")
        token = auth_token or kwargs.get("auth_token")

        return self.send_twilio_message(
            message=message,
            to_number=to_num,
            from_number=from_num,
            account_sid=sid,
            auth_token=token,
            is_whatsapp=False
        )
