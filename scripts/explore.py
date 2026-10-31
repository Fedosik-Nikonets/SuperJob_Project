"""Разведка API SuperJob: какие поля приходят, total и лимит выдачи.

Выяснено 31.10.2026: на странице не больше 40 вакансий (count урезается до 40),
страницы отдаются, пока page * count < 500 — максимум 520 за один поиск.
Подробности — в заметке проекта 1 в Obsidian.
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()
BASE = "https://api.superjob.ru/2.0"
session = requests.Session()
session.headers["X-Api-App-Id"] = os.environ["SUPERJOB_KEY"]


def get(**params):
    r = session.get(f"{BASE}/vacancies/", params=params, timeout=15)
    if not r.ok:
        print("ОШИБКА", r.status_code, r.text[:300])
        return None
    return r.json()

data = get(count=1, town=4)
vac = data["objects"][0]
print("поля вакансии:", sorted(vac.keys()))
for key in ["id", "profession", "payment_from", "payment_to", "currency",
            "date_published", "town", "firm_name"]:
    print(f"  {key}: {vac.get(key)!r}")

print("\ntotal без фильтров:", data["total"])

collected = 0
for page in range(15):
    d = get(count=40, page=page, town=4)
    if d is None:
        print(f"страница {page}: ошибка")
        break
    collected += len(d["objects"])
    print(f"страница {page}: {len(d['objects'])}, more={d['more']}")
    if not d["more"]:
        break
    time.sleep(0.5)
print("всего удалось получить:", collected)