import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(frozen=True)
class Vacancy:
    source: str
    id: int
    title: str
    salary_from: int | None
    salary_to: int | None
    published: int


class VacancySource(Protocol):
    def fetch(self, t_from: int, t_to: int) -> Iterator[Vacancy]: ...


class IncompleteWindowError(RuntimeError):
    def __init__(self, t_from: int, t_to: int, expected: int, received: int) -> None:
        self.t_from = t_from
        self.t_to = t_to
        self.expected = expected
        self.received = received
        super().__init__(
            f"Неполное окно {t_from}–{t_to}: получено {received} из {expected} вакансий"
        )


class SuperJobSource:
    """Источник вакансий: API SuperJob."""

    name = "superjob"

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        limit: int = 500,
        pause: float = 0.6,
        filters: dict[str, Any] | None = None,
    ) -> None:
        self.session = session
        self.base_url = base_url
        self.limit = limit
        self.pause = pause
        self.filters = filters or {}
        self.requests_made = 0

    def _search(self, **params: Any) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/vacancies/",
            params={"count": 40, **self.filters, **params},
            timeout=15,
        )
        response.raise_for_status()
        self.requests_made += 1
        time.sleep(self.pause)
        result: dict[str, Any] = response.json()
        return result

    def _parse(self, raw: dict[str, Any]) -> Vacancy:
        return Vacancy(
            source=self.name,
            id=raw["id"],
            title=raw["profession"],
            salary_from=raw["payment_from"] or None,  # в API ноль означает «не указано»
            salary_to=raw["payment_to"] or None,
            published=raw["date_published"],
        )

    def fetch(self, t_from: int, t_to: int) -> Iterator[Vacancy]:
        params = {"date_published_from": t_from, "date_published_to": t_to}
        first = self._search(**params, page=0)
        expected = first["total"]

        if expected > self.limit and t_to - t_from > 600:
            mid = (t_from + t_to) // 2
            combined_ids: set[int] = set()

            for start, end in ((t_from, mid), (mid, t_to)):
                for vacancy in self.fetch(start, end):
                    combined_ids.add(vacancy.id)
                    yield vacancy

            if len(combined_ids) < expected:
                raise IncompleteWindowError(t_from, t_to, expected, len(combined_ids))
            return
        data = first
        page = 0
        seen_ids: set[int] = set()

        while True:
            for raw in data["objects"]:
                vacancy = self._parse(raw)
                seen_ids.add(vacancy.id)
                yield vacancy
            if not data["more"]:
                break
            page += 1
            data = self._search(**params, page=page)
        if len(seen_ids) < expected:
            raise IncompleteWindowError(t_from, t_to, expected, len(seen_ids))


def collect(source: VacancySource, t_from: int, t_to: int) -> dict[int, Vacancy]:
    """Собрать вакансии за период. Функция не знает, откуда они берутся."""
    return {v.id: v for v in source.fetch(t_from, t_to)}


def make_session(api_key: str, retries: int = 3, backoff: float = 1.0) -> requests.Session:
    """Сессия с ключом и автоматическими повторами."""
    session = requests.Session()
    session.headers.update({"X-Api-App-Id": api_key})
    retry = Retry(
        total=retries,  # сколько раз повторять
        backoff_factor=backoff,  # паузы между повторами растут вдвое
        status_forcelist=[429, 500, 502, 503, 504],  # при каких кодах повторять
        allowed_methods=["GET"],  # какие методы безопасно повторять
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
