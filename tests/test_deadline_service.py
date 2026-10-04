"""Comprehensive unit tests for Deadline Tracker critical logic."""
import os
import tempfile
import pytest
from datetime import date, timedelta
from database.database import init_db
from services.deadline_service import DeadlineService
from services.digest_service import DigestService
from utils.date_utils import parse_to_standard_date, get_days_remaining, calculate_reminder_dates
from models.deadline import Deadline, UrgencyLevel, DeadlineType


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def deadline_service(temp_db):
    return DeadlineService(db_path=temp_db)


def test_date_parsing():
    """Test parsing varied date formats into YYYY-MM-DD."""
    assert parse_to_standard_date("2026-10-15") == "2026-10-15"
    assert parse_to_standard_date("15 Oct 2026") == "2026-10-15"
    assert parse_to_standard_date("October 15, 2026") == "2026-10-15"
    assert parse_to_standard_date("15/10/2026") == "2026-10-15"
    assert parse_to_standard_date("invalid-text") is None
    assert parse_to_standard_date("") is None
    assert parse_to_standard_date("TBD") is None


def test_days_remaining():
    """Test days remaining calculation against reference dates."""
    today = date(2026, 10, 3)
    assert get_days_remaining("2026-10-03", ref_date=today) == 0
    assert get_days_remaining("2026-10-04", ref_date=today) == 1
    assert get_days_remaining("2026-10-10", ref_date=today) == 7
    assert get_days_remaining("2026-10-01", ref_date=today) == -2


def test_deadline_creation(deadline_service):
    """Test 1: deadline creation."""
    success, err, dl = deadline_service.create_deadline({
        "title": "DBMS Assignment 2",
        "subject": "DBMS",
        "type": "Assignment",
        "date": "2026-10-15",
        "deadline_time": "23:59",
        "description": "Submit via portal",
        "confidence": "high",
        "source_document": "syllabus.pdf",
    })
    assert success is True
    assert err is None
    assert dl is not None
    assert dl.id is not None
    assert dl.title == "DBMS Assignment 2"
    assert dl.subject == "DBMS"
    assert dl.deadline_date == "2026-10-15"
    assert dl.deadline_time == "23:59"
    assert dl.completed is False


def test_due_today_and_overdue_detection(deadline_service):
    """Test 4 & 5: Overdue detection and Due Today detection."""
    ref = date(2026, 10, 3)

    # Overdue
    deadline_service.create_deadline({
        "title": "Overdue Lab Report",
        "subject": "Physics",
        "type": "Lab",
        "date": "2026-10-01",
    })

    # Due Today
    deadline_service.create_deadline({
        "title": "Today's Quiz",
        "subject": "Math",
        "type": "Quiz",
        "date": "2026-10-03",
    })

    # Tomorrow
    deadline_service.create_deadline({
        "title": "Tomorrow Presentation",
        "subject": "English",
        "type": "Presentation",
        "date": "2026-10-04",
    })

    # This Week
    deadline_service.create_deadline({
        "title": "Week Project",
        "subject": "CS",
        "type": "Project",
        "date": "2026-10-08",
    })

    overdue = deadline_service.get_overdue_deadlines(ref_date=ref)
    assert len(overdue) == 1
    assert overdue[0].title == "Overdue Lab Report"
    assert overdue[0].get_urgency(ref) == UrgencyLevel.OVERDUE

    due_today = deadline_service.get_due_today(ref_date=ref)
    assert len(due_today) == 1
    assert due_today[0].title == "Today's Quiz"
    assert due_today[0].get_urgency(ref) == UrgencyLevel.DUE_TODAY

    tomorrow = deadline_service.get_due_tomorrow(ref_date=ref)
    assert len(tomorrow) == 1
    assert tomorrow[0].title == "Tomorrow Presentation"
    assert tomorrow[0].get_urgency(ref) == UrgencyLevel.TOMORROW

    this_week = deadline_service.get_due_this_week(ref_date=ref)
    assert len(this_week) == 1
    assert this_week[0].title == "Week Project"


def test_duplicate_detection(deadline_service):
    """Test 6: Duplicate detection."""
    deadline_service.create_deadline({
        "title": "OS Internal Assessment",
        "subject": "OS",
        "date": "2026-10-20",
    })

    # Exact duplicate search
    duplicates = deadline_service.find_possible_duplicates("OS Internal Assessment", "OS", "2026-10-20")
    assert len(duplicates) == 1

    # Case-insensitive duplicate search
    duplicates_case = deadline_service.find_possible_duplicates("os internal assessment", "os", "2026-10-20")
    assert len(duplicates_case) == 1

    # Non-duplicate
    no_duplicates = deadline_service.find_possible_duplicates("Different Exam", "OS", "2026-10-20")
    assert len(no_duplicates) == 0


def test_digest_generation():
    """Test 7: Digest generation."""
    ref = date(2026, 10, 3)

    today_item = Deadline(
        title="DBMS Assignment",
        subject="DBMS",
        type="Assignment",
        deadline_date="2026-10-03",
    )
    tomorrow_item = Deadline(
        title="OS Lab Record",
        subject="OS",
        type="Lab",
        deadline_date="2026-10-04",
    )
    week_item = Deadline(
        title="CN Project",
        subject="CN",
        type="Project",
        deadline_date="2026-10-09",
    )

    digest = DigestService.generate_text_digest(
        upcoming_deadlines=[today_item, tomorrow_item, week_item],
        overdue_deadlines=[],
        student_name="Rahul",
        ref_date=ref
    )

    assert "📚 Deadline Tracker" in digest
    assert "Hello Rahul" in digest
    assert "🔴 Due Today:" in digest
    assert "DBMS Assignment" in digest
    assert "🟠 Tomorrow:" in digest
    assert "OS Lab Record" in digest
    assert "🟡 This Week:" in digest
    assert "CN Project" in digest
    assert "Stay ahead of your submissions." in digest


def test_mark_completed_and_stats(deadline_service):
    """Test completing a deadline and stats update."""
    ref = date(2026, 10, 3)
    _, _, dl = deadline_service.create_deadline({
        "title": "Complete me",
        "subject": "AI",
        "date": "2026-10-03",
    })

    stats_before = deadline_service.get_statistics(ref_date=ref)
    assert stats_before["due_today"] == 1
    assert stats_before["completed"] == 0

    deadline_service.mark_completed(dl.id, completed=True)

    stats_after = deadline_service.get_statistics(ref_date=ref)
    assert stats_after["due_today"] == 0
    assert stats_after["completed"] == 1


def test_reminder_date_calculation():
    """Test 7-day, 3-day, 1-day, and due date reminder offsets."""
    reminders = calculate_reminder_dates("2026-10-15")
    assert reminders["7_days_before"] == "2026-10-08"
    assert reminders["3_days_before"] == "2026-10-12"
    assert reminders["1_day_before"] == "2026-10-14"
    assert reminders["due_date"] == "2026-10-15"
