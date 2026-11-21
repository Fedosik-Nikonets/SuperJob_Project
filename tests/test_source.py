from unittest.mock import Mock

import pytest
from requests import Session

from superjob_project.source import IncompleteWindowError, SuperJobSource, collect


def test_collect_raises_when_window_is_incomplete(monkeypatch):
    def fake_get(url, *, params, **_kwargs):
        assert url == "https://example.invalid/vacancies/"
        assert params["catalogues"] == 33
        assert params["town"] == 4

        start = params["page"] * params["count"]
        end = min(start + params["count"], 520)
        response = Mock()
        response.json.return_value = {
            "total": 650,
            "more": end < 520,
            "objects": [
                {
                    "id": vacancy_id,
                    "profession": "Data Engineer",
                    "payment_from": 0,
                    "payment_to": 150_000,
                    "date_published": 300,
                }
                for vacancy_id in range(start, end)
            ],
        }
        return response

    with Session() as session:
        monkeypatch.setattr(session, "get", fake_get)
        source = SuperJobSource(
            session,
            "https://example.invalid",
            pause=0,
            filters={"catalogues": 33, "town": 4},
        )

        with pytest.raises(IncompleteWindowError) as caught:
            collect(source, 0, 600)

    assert caught.value.expected == 650
    assert caught.value.received == 520
