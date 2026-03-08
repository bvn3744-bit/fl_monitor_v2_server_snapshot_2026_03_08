"""Работа с SQLite базой данных."""

import sqlite3
from datetime import datetime


def init_db(db_path: str) -> None:
    """Создаёт базу данных и таблицу processed_projects если их нет."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_projects (
            project_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            processed_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def is_processed(db_path: str, project_id: str) -> bool:
    """Проверяет, существует ли project_id в базе."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT 1 FROM processed_projects WHERE project_id = ?",
        (project_id,),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def save_processed(db_path: str, project: dict) -> None:
    """Сохраняет обработанный проект."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO processed_projects (project_id, url, title, processed_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            project["project_id"],
            project["url"],
            project["title"],
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
