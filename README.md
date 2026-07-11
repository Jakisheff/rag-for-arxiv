# AI Engineering API Lab

Это учебная лабораторная работа по AI Engineering.

Главный паттерн:

```text
внешний API -> FastAPI backend -> детерминированный анализ -> объяснение от LLM -> browser UI
```

Ключевая идея: LLM не принимает основное решение. Backend считает score, risk или relevance обычным Python-кодом, а LLM только объясняет уже готовый результат человеческим языком.

## Что есть в репозитории

1. `demo_github_repo_health_assistant` — полностью рабочее demo преподавателя.
2. `student_projects/*` — постановки задач для студентов плюс минимальный starter-код.

В student-проектах уже есть только `main.py` с `/` и `/health`, `requirements.txt` и `.env.example`. Все остальное студенты проектируют и реализуют сами: services, schemas, raw/analyze/llm endpoints, UI, Dockerfile и README своего решения.

## Demo преподавателя

`demo_github_repo_health_assistant` показывает полный эталонный flow:

```text
GitHub REST API -> FastAPI -> deterministic health_score -> LLM report -> UI
```

Пример:

```text
owner=fastapi
repo=fastapi
```

## Варианты студенческих проектов

1. `student_projects/01_hacker_news_trend_radar`
   Hacker News Trend Radar: анализ трендов по Hacker News.

2. `student_projects/02_arxiv_paper_scout`
   AI Research Paper Scout: поиск и объяснение arXiv-статей.

3. `student_projects/03_weather_risk_assistant`
   Weather Risk Assistant: детерминированная оценка погодного риска.

Каждая папка содержит `README.md` с ТЗ и минимальный FastAPI starter. Это не готовый skeleton: бизнес-логика, UI, LLM adapter, Dockerfile и структура сервисов остаются задачей студента.

## Запуск demo без Docker

```bash
cd demo_github_repo_health_assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Windows:

```bash
cd demo_github_repo_health_assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Открыть:

```text
http://localhost:8000
```

## Запуск demo через Docker

Сначала создайте `.env` для demo:

```bash
cd demo_github_repo_health_assistant
cp .env.example .env
cd ..
```

Запуск из корня репозитория:

```bash
docker compose up --build demo
```

Открыть:

```text
http://localhost:8000
```

Остановить:

```bash
docker compose down
```

## Настройка LLM-провайдера

Demo поддерживает:

```text
LLM_PROVIDER=mock
LLM_PROVIDER=openai_compatible
LLM_PROVIDER=ollama
LLM_PROVIDER=cohere
LLM_PROVIDER=alemplus
```

Режим по умолчанию:

```env
LLM_PROVIDER=mock
```

Для студенческих проектов поддержка `.env` и LLM providers является частью задания.

Важно:

```text
LLM не считает итоговый score/risk/relevance.
Backend считает его детерминированно.
LLM только объясняет результат человеческим языком.
```

## Что студент должен сдать

1. Полную папку проекта с кодом.
2. Самостоятельно доработанную структуру проекта.
3. FastAPI backend.
4. Vanilla JS UI.
5. External API integration.
6. Deterministic analyzer.
7. LLM report endpoint.
8. `.env.example`.
9. `Dockerfile`.
10. README своего проекта.
11. Скриншот UI.
12. Скриншот raw endpoint.
13. Скриншот analyze endpoint.
14. Скриншот LLM report endpoint.
15. Краткое объяснение: где внешний API, где deterministic logic, где LLM.

## Критерии готовности

1. Проект запускается локально.
2. Проект запускается через Docker.
3. UI открывается.
4. `/health` работает.
5. Raw endpoint возвращает реальные данные.
6. Analyze endpoint считает deterministic result.
7. LLM report endpoint объясняет result.
8. Mock mode работает без API key.
9. Ошибки API и LLM обработаны понятно.
10. README содержит setup, endpoints, rules, limitations.
