"""
SQLite persistence for conversation history.
Maintains turns(id, session_id, ts, lang, role, text, intent)
"""

import os
import sqlite3
import time
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.environ.get("DB_PATH", "data/team_j.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or os.environ.get("DB_PATH", DEFAULT_DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None):
    """Initialize database tables."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    ts REAL NOT NULL,
                    lang TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL,
                    intent TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_ts ON turns(session_id, ts)")
    finally:
        conn.close()

def add_turn(
    session_id: str,
    lang: str,
    role: str,
    text: str,
    intent: Optional[str] = None,
    db_path: Optional[str] = None
) -> int:
    """Record a single turn (user or assistant) in SQLite."""
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO turns (session_id, ts, lang, role, text, intent)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, time.time(), lang, role, text, intent)
            )
            return cur.lastrowid
    finally:
        conn.close()

def get_history(session_id: str, limit: int = 6, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve the last N turns for a session in chronological order."""
    if not session_id:
        return []
    conn = get_connection(db_path)
    try:
        cur = conn.execute(
            """
            SELECT id, session_id, ts, lang, role, text, intent
            FROM turns
            WHERE session_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (session_id, limit)
        )
        rows = cur.fetchall()
        # Return in ascending order (oldest to newest)
        return [dict(row) for row in reversed(rows)]
    finally:
        conn.close()
