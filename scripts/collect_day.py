"""Сбор вакансий за последние сутки по одной отрасли и сверка с total."""
import os
import time

from dotenv import load_dotenv

from superjob_project.source import SuperJobSource, collect, make_session

load_dotenv()
BASE = "https://api.superjob.ru/2.0"
session = make_session(os.environ["SUPERJOB_KEY"])

source = SuperJobSource(session, BASE, limit=500, pause=0.6, filters={"catalogues":33, "town":4})

t_to = int(time.time())
t_from = t_to - 86400
vacancies = collect(source, t_from, t_to)
total = source._search(date_published_from = t_from, date_published_to = t_to)["total"]

print("собрано:", len(vacancies))
print("total за то же окно:", total)
print("запросов:", source.requests_made)
with_salary = [v for v in vacancies.values() if v.salary_from or v.salary_to]
print("с указанной зарплатой:", len(with_salary))

