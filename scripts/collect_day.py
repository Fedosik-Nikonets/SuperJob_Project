"""Сбор вакансий SuperJob с записью результата запуска в SQLite."""

import argparse
import json
import os
import sqlite3
import sys
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from requests import RequestException, Session

from superjob_project.db.storage import init_db, save_vacancy
from superjob_project.source import (
    IncompleteWindowError,
    SuperJobSource,
    Vacancy,
    make_session,
)

BASE = "https://api.superjob.ru/2.0"
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "vacancies.sqlite"
FILTERS = [{"catalogues": 33, "town": 4}]


def automatic_window(
    conn: sqlite3.Connection, filters: dict[str, int], now: int
) -> tuple[int, int]:
    filter_json = json.dumps(filters, sort_keys=True, separators=(",", ":"))
    rows = conn.execute(
        """
        SELECT n_errors,
               json_extract(params, '$.t_from'),
               json_extract(params, '$.t_to')
        FROM snapshots
        WHERE json_extract(params, '$.mode') = 'auto'
          AND json_extract(params, '$.source') = ?
          AND json_extract(params, '$.filters') = ?
        ORDER BY run_id DESC
        """,
        (SuperJobSource.name, filter_json),
    ).fetchall()

    last_end = max((end for errors, _, end in rows if errors == 0), default=None)

    for errors, start, end in rows:
        if errors and (last_end is None or start == last_end):
            return start, end

    start = now - 86400 if last_end is None else last_end
    return start, now


def run_filter(
    conn: sqlite3.Connection,
    session: Session,
    filters: dict[str, int],
    window: tuple[int, int],
    mode: str,
) -> bool:
    t_from, t_to = window
    started_at = datetime.now(UTC).isoformat()
    source = SuperJobSource(session, BASE, limit=500, pause=0.6, filters=filters)
    vacancies: dict[int, Vacancy] = {}
    error_message = None

    try:
        for vacancy in source.fetch(t_from, t_to):
            vacancies[vacancy.id] = vacancy
    except (IncompleteWindowError, RequestException) as error:
        error_message = str(error)

    params = {
        "source": source.name,
        "filters": filters,
        "mode": mode,
        "t_from": t_from,
        "t_to": t_to,
        "error": error_message,
    }

    with conn:
        n_new = 0
        if error_message is None:
            n_new = sum(save_vacancy(conn, vacancy) for vacancy in vacancies.values())

        conn.execute(
            """
            INSERT INTO snapshots (
                started_at, finished_at, params, n_found, n_new, n_errors
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                started_at,
                datetime.now(UTC).isoformat(),
                json.dumps(params, ensure_ascii=False, sort_keys=True),
                len(vacancies),
                n_new,
                int(error_message is not None),
            ),
        )

    with_salary = sum(1 for v in vacancies.values() if v.salary_from or v.salary_to)
    print(
        f"{filters} | {t_from}–{t_to} | получено: {len(vacancies)} | "
        f"новых: {n_new} | с зарплатой: {with_salary} | запросов: {source.requests_made}"
    )
    if error_message is not None:
        print(f"{filters} | {error_message}", file=sys.stderr)
    return error_message is None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--from-ts", type=int)
    parser.add_argument("--to-ts", type=int)
    args = parser.parse_args()

    if (args.from_ts is None) != (args.to_ts is None):
        parser.error("Укажи --from-ts и --to-ts вместе")
    if args.from_ts is not None and args.from_ts >= args.to_ts:
        parser.error("--from-ts должен быть меньше --to-ts")

    load_dotenv()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    mode = "auto" if args.from_ts is None else "manual"
    had_error = False

    with closing(sqlite3.connect(args.db)) as conn:
        init_db(conn)

        with make_session(os.environ["SUPERJOB_KEY"]) as session:
            for filters in FILTERS:
                if mode == "manual":
                    window = (args.from_ts, args.to_ts)
                else:
                    window = automatic_window(conn, filters, now)

                if window[0] < window[1] and not run_filter(conn, session, filters, window, mode):
                    had_error = True

    return int(had_error)


if __name__ == "__main__":
    raise SystemExit(main())
