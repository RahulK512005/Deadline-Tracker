"""Date parsing, formatting, calculations, and greeting helpers."""
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
import re
from dateutil import parser


def parse_to_standard_date(raw_date_str: str, default_year: Optional[int] = None) -> Optional[str]:
    """
    Parse a raw date string into strict YYYY-MM-DD format.
    Handles various formats like '2026-10-15', '15 Oct 2026', 'October 15', '15/10/2026', etc.
    If year is missing and default_year is provided, supplies default_year or current year.
    Returns None if date cannot be confidently parsed.
    """
    if not raw_date_str or not isinstance(raw_date_str, str):
        return None

    cleaned = raw_date_str.strip()
    if not cleaned or cleaned.lower() in ("null", "none", "unknown", "n/a", "tbd"):
        return None

    # Check for direct YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", cleaned):
        try:
            datetime.strptime(cleaned, "%Y-%m-%d")
            return cleaned
        except ValueError:
            return None

    # Attempt dateutil parser with fuzzy matching
    try:
        current_year = default_year or date.today().year
        # Default day to 1, default month to current, default year to current_year
        default_dt = datetime(current_year, 1, 1)
        dt = parser.parse(cleaned, default=default_dt, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        pass

    # Try non-dayfirst
    try:
        current_year = default_year or date.today().year
        default_dt = datetime(current_year, 1, 1)
        dt = parser.parse(cleaned, default=default_dt, dayfirst=False)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        return None


def format_display_date(date_str: str, include_weekday: bool = False) -> str:
    """Format YYYY-MM-DD into readable string like 'Oct 15, 2026' or 'Mon, Oct 15, 2026'."""
    if not date_str:
        return "No Date"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if include_weekday:
            return dt.strftime("%a, %b %d, %Y")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def get_days_remaining(date_str: str, ref_date: Optional[date] = None) -> Optional[int]:
    """Calculate days between ref_date (default: today) and deadline date."""
    if not date_str:
        return None
    if ref_date is None:
        ref_date = date.today()
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (d - ref_date).days
    except ValueError:
        return None


def get_time_of_day_greeting() -> str:
    """Return greeting string based on local time."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Good night"


def calculate_reminder_dates(deadline_date_str: str) -> Dict[str, Optional[str]]:
    """
    Calculate trigger dates for standard academic reminders:
    - 7 days before
    - 3 days before
    - 1 day before
    - On due date
    """
    try:
        d = datetime.strptime(deadline_date_str, "%Y-%m-%d").date()
        return {
            "7_days_before": (d - timedelta(days=7)).strftime("%Y-%m-%d"),
            "3_days_before": (d - timedelta(days=3)).strftime("%Y-%m-%d"),
            "1_day_before": (d - timedelta(days=1)).strftime("%Y-%m-%d"),
            "due_date": d.strftime("%Y-%m-%d"),
        }
    except ValueError:
        return {
            "7_days_before": None,
            "3_days_before": None,
            "1_day_before": None,
            "due_date": None,
        }
