"""
database.py — SQLite layer for Thoth Research Dashboard.

Tables:
  research_events  — records of work-item verdicts
  todo_projects    — personal todo projects
  todo_tasks       — personal todo tasks (nested under projects)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "research.db"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS research_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id         TEXT    NOT NULL,
    work_title      TEXT    NOT NULL,
    module          TEXT    NOT NULL,
    direction       TEXT    NOT NULL,
    verdict         TEXT    NOT NULL,
    conclusion_text TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_research_events_created ON research_events(created_at);

CREATE TABLE IF NOT EXISTS todo_projects (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS todo_tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES todo_projects(id),
    description  TEXT    NOT NULL,
    due_label    TEXT,
    due_date     TEXT,
    completed    INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_todo_tasks_project ON todo_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_todo_tasks_completed ON todo_tasks(completed);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(_CREATE_SQL)
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(research_events)").fetchall()}
        if "task_id" in columns and "work_id" not in columns:
            conn.execute("ALTER TABLE research_events ADD COLUMN work_id TEXT")
            conn.execute("UPDATE research_events SET work_id = task_id WHERE work_id IS NULL")
        if "task_title" in columns and "work_title" not in columns:
            conn.execute("ALTER TABLE research_events ADD COLUMN work_title TEXT")
            conn.execute("UPDATE research_events SET work_title = task_title WHERE work_title IS NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_research_events_work ON research_events(work_id)")
