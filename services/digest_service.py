"""Digest service for generating academic deadline summaries for students."""
from datetime import date
from typing import List, Optional
from models.deadline import Deadline, UrgencyLevel
from utils.date_utils import format_display_date


class DigestService:
    @staticmethod
    def generate_text_digest(
        upcoming_deadlines: List[Deadline],
        overdue_deadlines: Optional[List[Deadline]] = None,
        student_name: str = "Student",
        ref_date: Optional[date] = None
    ) -> str:
        """
        Generate a concise, beautifully formatted plain text / markdown digest.
        Follows prompt specification:
        📚 Deadline Tracker
        You have X upcoming academic deadlines.
        🔴 Due Today
        ...
        🟠 Tomorrow
        ...
        🟡 This Week
        ...
        🔵 Upcoming
        ...
        Stay ahead of your submissions.
        """
        ref = ref_date or date.today()
        overdue = overdue_deadlines or []
        total_upcoming = len(upcoming_deadlines)

        lines = ["📚 Deadline Tracker"]
        lines.append(f"Hello {student_name},")

        if total_upcoming == 0 and len(overdue) == 0:
            lines.append("You have no pending academic deadlines. Great job staying ahead!")
            return "\n\n".join(lines)

        if total_upcoming == 1:
            lines.append("You have 1 upcoming academic deadline.")
        else:
            lines.append(f"You have {total_upcoming} upcoming academic deadlines.")

        # Group deadlines by urgency
        due_today = []
        due_tomorrow = []
        due_this_week = []
        due_later = []

        for d in upcoming_deadlines:
            urgency = d.get_urgency(ref)
            if urgency == UrgencyLevel.DUE_TODAY:
                due_today.append(d)
            elif urgency == UrgencyLevel.TOMORROW:
                due_tomorrow.append(d)
            elif urgency == UrgencyLevel.THIS_WEEK:
                due_this_week.append(d)
            elif urgency == UrgencyLevel.UPCOMING:
                due_later.append(d)

        # Overdue section
        if overdue:
            lines.append(f"⚠️ Overdue ({len(overdue)}):")
            for d in overdue:
                date_str = format_display_date(d.deadline_date)
                days_past = abs(d.days_remaining(ref))
                time_str = f" at {d.deadline_time}" if d.deadline_time else ""
                lines.append(f"• {d.title} [{d.subject}] - Due: {date_str}{time_str} ({days_past}d overdue)")

        # Due Today
        if due_today:
            lines.append("🔴 Due Today:")
            for d in due_today:
                time_str = f" by {d.deadline_time}" if d.deadline_time else ""
                lines.append(f"• {d.title} [{d.subject}] ({d.type}){time_str}")

        # Tomorrow
        if due_tomorrow:
            lines.append("🟠 Tomorrow:")
            for d in due_tomorrow:
                date_str = format_display_date(d.deadline_date)
                time_str = f" by {d.deadline_time}" if d.deadline_time else ""
                lines.append(f"• {d.title} [{d.subject}] - Due: {date_str}{time_str}")

        # This Week
        if due_this_week:
            lines.append("🟡 This Week:")
            for d in due_this_week:
                date_str = format_display_date(d.deadline_date, include_weekday=True)
                lines.append(f"• {d.title} [{d.subject}] - Due: {date_str}")

        # Upcoming
        if due_later:
            lines.append("🔵 Upcoming:")
            for d in due_later[:5]:  # limit to top 5 to keep digest concise
                date_str = format_display_date(d.deadline_date)
                lines.append(f"• {d.title} [{d.subject}] - Due: {date_str}")
            if len(due_later) > 5:
                lines.append(f"• ... and {len(due_later) - 5} more")

        lines.append("Stay ahead of your submissions.")
        return "\n\n".join(lines)
