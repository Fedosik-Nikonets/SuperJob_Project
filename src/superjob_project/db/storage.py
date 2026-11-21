import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from superjob_project.source import Vacancy


def init_db(conn: sqlite3.Connection) -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    conn.executescript(schema_path.read_text(encoding="utf-8"))


def save_vacancy(conn: sqlite3.Connection, vacancy: Vacancy) -> int:
    date_published = datetime.fromtimestamp(vacancy.published, UTC).isoformat()
    first_seen_at = datetime.now(UTC).isoformat()

    cursor = conn.execute(
        """
                INSERT INTO vacancies (
                    source, id, profession, payment_from, payment_to,
                    date_published, first_seen_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, id) DO NOTHING
                """,
        (
            vacancy.source,
            vacancy.id,
            vacancy.title,
            vacancy.salary_from,
            vacancy.salary_to,
            date_published,
            first_seen_at,
        ),
    )
    return cursor.rowcount
