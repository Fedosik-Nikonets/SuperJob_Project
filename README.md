# Зарплаты в IT по вакансиям SuperJob

Сбор вакансий с API SuperJob, анализ зарплат и модель, которая предсказывает зарплату по описанию вакансии.

**Статус:** этап 1 — сбор данных.

## Что уже сделано
- Клиент API SuperJob: пагинация, ретраи при 429/5xx, пауза между запросами.
- Обход лимита выдачи: API отдаёт не больше 520 вакансий на поиск (40 на страницу), поэтому период делится на окна по дате публикации, пока каждое не влезет в лимит.
- Сверка с `total`: за сутки по IT в Москве собрано 82 из 82.

## Запуск

Нужны Python 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Fedosik-Nikonets/SuperJob_Project.git
cd SuperJob_Project
uv sync
cp .env.example .env    # и вписать ключ
```

Ключ API — Secret key приложения на [api.superjob.ru](https://api.superjob.ru).

Сбор вакансий за последние сутки:
```bash
uv run python scripts/collect_day.py
```

## Структура
```
src/superjob_project/source.py   — клиент API и сборщик
scripts/explore.py               — разведка API: поля, total, лимит выдачи
scripts/collect_day.py           — сбор за сутки и сверка с total
```

## План
- [x] Клиент API и сбор за период
- [ ] Хранение в SQLite, запись без дублей, ежедневный запуск
- [ ] Тесты, ruff, mypy, CI
- [ ] EDA: распределение зарплат, город, опыт, отрасль
- [ ] Модель: линейная регрессия → градиентный бустинг, валидация
- [ ] Сервис на FastAPI в Docker

## Стек
Python, requests, SQLite, pandas, scikit-learn, FastAPI, Docker, uv