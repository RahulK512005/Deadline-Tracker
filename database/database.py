"""SQLite database access layer for Deadline Tracker."""
import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

DB_FILENAME = "deadlines.db"


def get_db_path() -> str:
    """Get absolute path to SQLite database."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, DB_FILENAME)


@contextmanager
def get_connection(db_path: Optional[str] = None):
    """Context manager for SQLite connections with row dict factory and WAL mode."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None):
    """Initialize database tables and indexes if they do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Deadlines table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                type TEXT NOT NULL,
                deadline_date TEXT NOT NULL,
                deadline_time TEXT,
                description TEXT,
                confidence TEXT DEFAULT 'high',
                source_document TEXT DEFAULT 'manual',
                source_text TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Settings table for user preferences and persistent configuration
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # Performance indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deadlines_date ON deadlines (deadline_date);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deadlines_completed ON deadlines (completed);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deadlines_subject ON deadlines (subject);"
        )


def execute_insert(sql: str, params: Tuple = (), db_path: Optional[str] = None) -> int:
    """Execute INSERT query and return newly created row ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid


def execute_query(sql: str, params: Tuple = (), db_path: Optional[str] = None) -> int:
    """Execute UPDATE or DELETE query and return number of affected rows."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount


def fetch_all(sql: str, params: Tuple = (), db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Execute query and return list of dictionaries."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def fetch_one(sql: str, params: Tuple = (), db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Execute query and return a single row dictionary or None."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def get_setting(key: str, default: Optional[str] = None, db_path: Optional[str] = None) -> Optional[str]:
    """Retrieve setting value by key."""
    sql = "SELECT value FROM user_settings WHERE key = ?;"
    row = fetch_one(sql, (key,), db_path)
    return row["value"] if row else default


def set_setting(key: str, value: str, db_path: Optional[str] = None):
    """Store or update setting value by key."""
    from datetime import datetime
    now_iso = datetime.now().isoformat()
    sql = """
    INSERT INTO user_settings (key, value, updated_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
    """
    execute_query(sql, (key, str(value), now_iso), db_path)

