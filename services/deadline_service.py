"""Deadline service for business logic, CRUD operations, duplicate checks, and metrics."""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from models.deadline import Deadline, UrgencyLevel, DeadlineType
from database.database import (
    execute_insert,
    execute_query,
    fetch_all,
    fetch_one,
    get_db_path,
)
from utils.validators import validate_deadline_dict, sanitize_text


class DeadlineService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()

    def create_deadline(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Deadline]]:
        """Validate and create a new deadline record."""
        is_valid, error_msg, normalized = validate_deadline_dict(data)
        if not is_valid:
            return False, error_msg, None

        now_iso = datetime.now().isoformat()
        sql = """
        INSERT INTO deadlines (
            title, subject, type, deadline_date, deadline_time,
            description, confidence, source_document, source_text,
            completed, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            normalized["title"],
            normalized["subject"],
            normalized["type"],
            normalized["deadline_date"],
            normalized.get("deadline_time"),
            normalized.get("description", ""),
            normalized.get("confidence", "high"),
            normalized.get("source_document", "manual"),
            normalized.get("source_text", ""),
            1 if normalized.get("completed", False) else 0,
            now_iso,
            now_iso,
        )
        new_id = execute_insert(sql, params, self.db_path)
        created = self.get_deadline(new_id)
        return True, None, created

    def get_deadline(self, deadline_id: int) -> Optional[Deadline]:
        """Retrieve a single deadline by its ID."""
        sql = "SELECT * FROM deadlines WHERE id = ?;"
        row = fetch_one(sql, (deadline_id,), self.db_path)
        return Deadline.from_row(row) if row else None

    def get_all_deadlines(
        self,
        include_completed: bool = True,
        subject: Optional[str] = None,
        deadline_type: Optional[str] = None,
        search_query: Optional[str] = None,
        sort_order: str = "ASC"
    ) -> List[Deadline]:
        """Fetch deadlines with optional filters and sorting."""
        conditions = []
        params: List[Any] = []

        if not include_completed:
            conditions.append("completed = 0")

        if subject and subject != "All Subjects":
            conditions.append("subject = ?")
            params.append(subject)

        if deadline_type and deadline_type != "All Types":
            conditions.append("type = ?")
            params.append(deadline_type)

        if search_query:
            term = f"%{search_query.strip()}%"
            conditions.append("(title LIKE ? OR description LIKE ? OR subject LIKE ?)")
            params.extend([term, term, term])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_dir = "DESC" if sort_order.upper() == "DESC" else "ASC"
        sql = f"SELECT * FROM deadlines {where_clause} ORDER BY deadline_date {order_dir}, id ASC;"

        rows = fetch_all(sql, tuple(params), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_upcoming_deadlines(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get all active (incomplete) deadlines due on or after ref_date."""
        ref = ref_date or date.today()
        ref_str = ref.strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date >= ?
        ORDER BY deadline_date ASC, deadline_time ASC;
        """
        rows = fetch_all(sql, (ref_str,), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_due_today(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get active deadlines due today."""
        ref = ref_date or date.today()
        ref_str = ref.strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date = ?
        ORDER BY deadline_time ASC, id ASC;
        """
        rows = fetch_all(sql, (ref_str,), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_due_tomorrow(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get active deadlines due tomorrow."""
        ref = ref_date or date.today()
        tomorrow_str = (ref + timedelta(days=1)).strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date = ?
        ORDER BY deadline_time ASC, id ASC;
        """
        rows = fetch_all(sql, (tomorrow_str,), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_due_this_week(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get active deadlines due between 2 and 7 days from ref_date."""
        ref = ref_date or date.today()
        start_str = (ref + timedelta(days=2)).strftime("%Y-%m-%d")
        end_str = (ref + timedelta(days=7)).strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date >= ? AND deadline_date <= ?
        ORDER BY deadline_date ASC, deadline_time ASC;
        """
        rows = fetch_all(sql, (start_str, end_str), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_due_later(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get active deadlines due beyond 7 days from ref_date."""
        ref = ref_date or date.today()
        later_str = (ref + timedelta(days=8)).strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date >= ?
        ORDER BY deadline_date ASC, deadline_time ASC;
        """
        rows = fetch_all(sql, (later_str,), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_overdue_deadlines(self, ref_date: Optional[date] = None) -> List[Deadline]:
        """Get active deadlines that are past due date."""
        ref = ref_date or date.today()
        ref_str = ref.strftime("%Y-%m-%d")
        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date < ?
        ORDER BY deadline_date ASC;
        """
        rows = fetch_all(sql, (ref_str,), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def get_completed_deadlines(self) -> List[Deadline]:
        """Get all completed deadlines."""
        sql = "SELECT * FROM deadlines WHERE completed = 1 ORDER BY deadline_date DESC;"
        rows = fetch_all(sql, (), self.db_path)
        return [Deadline.from_row(row) for row in rows]

    def update_deadline(self, deadline_id: int, data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Deadline]]:
        """Update an existing deadline record."""
        existing = self.get_deadline(deadline_id)
        if not existing:
            return False, f"Deadline with id {deadline_id} does not exist.", None

        merged = existing.to_dict()
        for k, v in data.items():
            if v is not None:
                merged[k] = v

        is_valid, error_msg, normalized = validate_deadline_dict(merged)
        if not is_valid:
            return False, error_msg, None

        now_iso = datetime.now().isoformat()
        sql = """
        UPDATE deadlines SET
            title = ?, subject = ?, type = ?, deadline_date = ?, deadline_time = ?,
            description = ?, confidence = ?, source_document = ?, source_text = ?,
            completed = ?, updated_at = ?
        WHERE id = ?;
        """
        params = (
            normalized["title"],
            normalized["subject"],
            normalized["type"],
            normalized["deadline_date"],
            normalized.get("deadline_time"),
            normalized.get("description", ""),
            normalized.get("confidence", existing.confidence),
            normalized.get("source_document", existing.source_document),
            normalized.get("source_text", existing.source_text),
            1 if normalized.get("completed", False) else 0,
            now_iso,
            deadline_id,
        )
        execute_query(sql, params, self.db_path)
        updated = self.get_deadline(deadline_id)
        return True, None, updated

    def delete_deadline(self, deadline_id: int) -> bool:
        """Delete deadline by ID."""
        sql = "DELETE FROM deadlines WHERE id = ?;"
        rows_deleted = execute_query(sql, (deadline_id,), self.db_path)
        return rows_deleted > 0

    def mark_completed(self, deadline_id: int, completed: bool = True) -> bool:
        """Toggle or mark completion status for a deadline."""
        now_iso = datetime.now().isoformat()
        sql = "UPDATE deadlines SET completed = ?, updated_at = ? WHERE id = ?;"
        rows_updated = execute_query(sql, (1 if completed else 0, now_iso, deadline_id), self.db_path)
        return rows_updated > 0

    def find_possible_duplicates(
        self,
        title: str,
        subject: str,
        deadline_date: str,
        exclude_id: Optional[int] = None
    ) -> List[Deadline]:
        """
        Detect possible duplicate deadlines.
        Key: normalized title + subject + deadline_date.
        """
        norm_title = sanitize_text(title).lower()
        norm_subject = sanitize_text(subject).lower()

        # Query items on the same date
        sql = "SELECT * FROM deadlines WHERE deadline_date = ?;"
        rows = fetch_all(sql, (deadline_date,), self.db_path)

        duplicates = []
        for r in rows:
            if exclude_id and r["id"] == exclude_id:
                continue
            r_title = sanitize_text(r["title"]).lower()
            r_subject = sanitize_text(r["subject"]).lower()

            # Exact match or title contains
            if r_title == norm_title and r_subject == norm_subject:
                duplicates.append(Deadline.from_row(r))
            elif norm_title in r_title or r_title in norm_title:
                if norm_subject == r_subject:
                    duplicates.append(Deadline.from_row(r))

        return duplicates

    def get_statistics(self, ref_date: Optional[date] = None) -> Dict[str, int]:
        """Calculate statistics for dashboard cards."""
        ref = ref_date or date.today()
        upcoming = len(self.get_upcoming_deadlines(ref))
        due_today = len(self.get_due_today(ref))
        due_this_week = len(self.get_due_tomorrow(ref)) + len(self.get_due_this_week(ref))
        overdue = len(self.get_overdue_deadlines(ref))
        completed = len(self.get_completed_deadlines())

        return {
            "total_upcoming": upcoming,
            "due_today": due_today,
            "due_this_week": due_this_week,
            "overdue": overdue,
            "completed": completed,
        }

    def check_heavy_workload(self, ref_date: Optional[date] = None, threshold: int = 4, days_window: int = 3) -> Tuple[bool, int, List[Deadline]]:
        """
        Workload detection:
        If user has `threshold` (default 4) or more deadlines within `days_window` (default 3 days),
        returns (is_heavy, count, deadlines_list).
        """
        ref = ref_date or date.today()
        end_ref = ref + timedelta(days=days_window)
        ref_str = ref.strftime("%Y-%m-%d")
        end_str = end_ref.strftime("%Y-%m-%d")

        sql = """
        SELECT * FROM deadlines 
        WHERE completed = 0 AND deadline_date >= ? AND deadline_date <= ?
        ORDER BY deadline_date ASC;
        """
        rows = fetch_all(sql, (ref_str, end_str), self.db_path)
        deadlines = [Deadline.from_row(r) for r in rows]
        is_heavy = len(deadlines) >= threshold
        return is_heavy, len(deadlines), deadlines

    def get_distinct_subjects(self) -> List[str]:
        """Return list of distinct subjects for dropdown filters."""
        sql = "SELECT DISTINCT subject FROM deadlines WHERE subject != '' ORDER BY subject ASC;"
        rows = fetch_all(sql, (), self.db_path)
        return [r["subject"] for r in rows]
