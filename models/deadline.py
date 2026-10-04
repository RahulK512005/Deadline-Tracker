"""Deadline data model with validation, serialization, and status helpers."""
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional, Dict, Any
from enum import Enum


class DeadlineType(str, Enum):
    ASSIGNMENT = "Assignment"
    EXAM = "Exam"
    QUIZ = "Quiz"
    PROJECT = "Project"
    LAB = "Lab"
    PRESENTATION = "Presentation"
    SUBMISSION = "Submission"
    EVENT = "Event"
    OTHER = "Other"

    @classmethod
    def normalize(cls, val: str) -> str:
        if not val:
            return cls.OTHER.value
        val_clean = val.strip().capitalize()
        for member in cls:
            if member.value.lower() == val_clean.lower():
                return member.value
        return cls.OTHER.value


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def normalize(cls, val: str) -> str:
        if not val:
            return cls.MEDIUM.value
        v = val.strip().lower()
        if v in ("high", "medium", "low"):
            return v
        return cls.MEDIUM.value


class UrgencyLevel(str, Enum):
    OVERDUE = "Overdue"
    DUE_TODAY = "Due Today"
    TOMORROW = "Tomorrow"
    THIS_WEEK = "This Week"
    UPCOMING = "Upcoming"
    COMPLETED = "Completed"


@dataclass
class Deadline:
    title: str
    subject: str
    deadline_date: str  # YYYY-MM-DD
    type: str = DeadlineType.ASSIGNMENT.value
    deadline_time: Optional[str] = None  # HH:MM
    description: Optional[str] = ""
    confidence: str = ConfidenceLevel.HIGH.value
    source_document: Optional[str] = "manual"
    source_text: Optional[str] = ""
    completed: bool = False
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        # Normalize type and confidence
        self.type = DeadlineType.normalize(self.type)
        self.confidence = ConfidenceLevel.normalize(self.confidence)
        if self.description is None:
            self.description = ""
        if self.source_text is None:
            self.source_text = ""

    def get_parsed_date(self) -> Optional[date]:
        """Return Python datetime.date object from deadline_date string."""
        if not self.deadline_date:
            return None
        try:
            return datetime.strptime(self.deadline_date, "%Y-%m-%d").date()
        except ValueError:
            return None

    def days_remaining(self, ref_date: Optional[date] = None) -> int:
        """Calculate days remaining from reference date (default: today)."""
        if ref_date is None:
            ref_date = date.today()
        parsed = self.get_parsed_date()
        if parsed is None:
            return 999
        return (parsed - ref_date).days

    def get_urgency(self, ref_date: Optional[date] = None) -> UrgencyLevel:
        """Categorize urgency strictly based on date calculations."""
        if self.completed:
            return UrgencyLevel.COMPLETED
        
        days = self.days_remaining(ref_date)
        if days < 0:
            return UrgencyLevel.OVERDUE
        elif days == 0:
            return UrgencyLevel.DUE_TODAY
        elif days == 1:
            return UrgencyLevel.TOMORROW
        elif 2 <= days <= 7:
            return UrgencyLevel.THIS_WEEK
        else:
            return UrgencyLevel.UPCOMING

    def is_overdue(self, ref_date: Optional[date] = None) -> bool:
        if self.completed:
            return False
        return self.days_remaining(ref_date) < 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Add dynamic fields for easy UI rendering
        data["days_remaining"] = self.days_remaining()
        data["urgency"] = self.get_urgency().value
        return data

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "Deadline":
        """Construct Deadline instance from SQLite row dictionary."""
        return cls(
            id=row.get("id"),
            title=row.get("title", ""),
            subject=row.get("subject", ""),
            type=row.get("type", DeadlineType.ASSIGNMENT.value),
            deadline_date=row.get("deadline_date", ""),
            deadline_time=row.get("deadline_time"),
            description=row.get("description", "") or "",
            confidence=row.get("confidence", ConfidenceLevel.HIGH.value),
            source_document=row.get("source_document", "manual"),
            source_text=row.get("source_text", "") or "",
            completed=bool(row.get("completed", 0)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
