"""SQLite database management for Literature Manager."""

import sqlite3
import os
from pathlib import Path
from typing import Optional


def get_default_db_path() -> str:
    """Get the default database file path in user's app data directory."""
    if os.name == "nt":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        db_dir = os.path.join(app_data, "LiteratureManager")
    else:
        db_dir = os.path.join(os.path.expanduser("~"), ".literaturemanager")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "library.db")


class Database:
    """Manages the SQLite database connection and schema."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_default_db_path()
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open a connection and initialize the schema."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self):
        """Create all tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '',
                authors TEXT NOT NULL DEFAULT '',
                year INTEGER,
                journal TEXT NOT NULL DEFAULT '',
                doi TEXT,
                pmid TEXT,
                abstract TEXT NOT NULL DEFAULT '',
                pdf_path TEXT,
                status_id INTEGER,
                priority TEXT NOT NULL DEFAULT 'None'
                    CHECK(priority IN ('High', 'Medium', 'Low', 'None')),
                notes TEXT NOT NULL DEFAULT '',
                date_added TEXT NOT NULL DEFAULT (datetime('now')),
                date_modified TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (status_id) REFERENCES statuses(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#4a86c8'
            );

            CREATE TABLE IF NOT EXISTS paper_tags (
                paper_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (paper_id, tag_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL DEFAULT '#888888',
                sort_order INTEGER NOT NULL DEFAULT 0
            );
        """)

        # Insert default statuses if table is empty
        count = cursor.execute("SELECT COUNT(*) FROM statuses").fetchone()[0]
        if count == 0:
            defaults = [
                ("In Queue", "#5bc0de", 0),
                ("Reading", "#f0ad4e", 1),
                ("Read", "#5cb85c", 2),
                ("Discard", "#d9534f", 3),
            ]
            cursor.executemany(
                "INSERT INTO statuses (name, color, sort_order) VALUES (?, ?, ?)",
                defaults,
            )

        self.conn.commit()

    def execute(self, sql: str, params=None):
        """Execute a single SQL statement and return the cursor."""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()
