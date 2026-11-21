import sqlite3
from contextlib import closing

from superjob_project.db.storage import init_db, save_vacancy
from superjob_project.source import Vacancy


def test_save_vacancy_skips_duplicate():
    vacancy = Vacancy(
        source="superjob",
        id=42,
        title="Data Engineer",
        salary_from=None,
        salary_to=150_000,
        published=1_700_000_000,
    )

    with closing(sqlite3.connect(":memory:")) as conn:
        init_db(conn)

        with conn:
            first = save_vacancy(conn, vacancy)
            second = save_vacancy(conn, vacancy)

        count = conn.execute("SELECT COUNT(*) FROM vacancies").fetchone()[0]

    assert (first, second, count) == (1, 0, 1)
