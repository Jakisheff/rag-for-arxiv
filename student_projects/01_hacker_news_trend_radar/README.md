# Проект 1: Hacker News Trend Radar

## Идея

Сделайте с нуля AI Engineering сервис, который анализирует top stories из Hacker News и объясняет, какие технические темы сейчас набирают внимание.

В этой папке есть минимальный starter: `main.py` с `/` и `/health`, `requirements.txt` и `.env.example`. Все остальное вы проектируете сами: backend structure, services, schemas, frontend, Dockerfile и финальный README.

## Что уже дано

```text
main.py          минимальный FastAPI app
requirements.txt базовые зависимости
.env.example     стартовые переменные окружения
README.md        это ТЗ
```

Starter не содержит готовой Hacker News integration, analyzer, LLM client, UI или Dockerfile.

## Product goal

Пользователь вводит `topic` и `limit`, например:

```text
topic=ai
limit=30
```

Сервис должен:

1. Получить top stories из Hacker News API.
2. Отобрать истории, связанные с выбранной темой.
3. Детерминированно посчитать `trend_score`.
4. Показать raw data, analysis result и LLM explanation в UI.
5. Объяснить студенту, какие 3 материала стоит прочитать первыми.

## External API

Используйте Hacker News Firebase API:

```text
https://hacker-news.firebaseio.com/v0/topstories.json
https://hacker-news.firebaseio.com/v0/item/{id}.json
```

## Минимальные endpoints

```text
GET /health
GET /hn/raw?limit=30
GET /hn/analyze?topic=ai&limit=30
GET /hn/llm-report?topic=ai&limit=30
```

## Обязательные TODO для реализации

1. Расширить минимальный FastAPI starter до полноценного backend.
2. Самостоятельно спроектировать структуру `services`, `schemas`, `static`.
3. Создать light UI без React/Vite/Next/Tailwind.
4. Настроить static file serving из FastAPI.
5. Проверить и при необходимости расширить `/health`.
6. Подключить Hacker News API.
7. Добавить timeout для каждого external API request.
8. Обработать timeout, network error, 404 и non-200 responses.
9. Получить top story IDs.
10. Скачать details для каждой story.
11. Отфильтровать `deleted`, `dead`, пустые и не-story payloads.
12. Нормализовать raw data в свои Pydantic schemas.
13. Реализовать `/hn/raw`.
14. Придумать deterministic topic relevance rules.
15. Учесть title match, score, comments, freshness и повторяющиеся keywords.
16. Посчитать `trend_score` в диапазоне `0-100`.
17. Добавить `grade`: `weak | moderate | strong`.
18. Сформировать `signals`.
19. Сформировать `risks` или `limitations`.
20. Реализовать `/hn/analyze`.
21. Написать LLM prompt, где модели запрещено считать `trend_score`.
22. Поддержать `LLM_PROVIDER=mock`.
23. Поддержать минимум один реальный provider: `ollama`, `openai_compatible`, `cohere` или `alemplus`.
24. Реализовать `/hn/llm-report`.
25. Показать в UI raw JSON, cards, stories list, signals, risks и LLM report.
26. Добавить loading states и error states.
27. Сделать `.env.example`.
28. Сделать Dockerfile.
29. Проверить запуск через Docker.
30. Обновить README своего проекта.

## LLM role

LLM должна объяснить:

1. Какие темы встречаются часто.
2. Почему это может быть трендом.
3. Какие 3 истории самые релевантные.
4. Что студенту прочитать первым.
5. Какие ограничения есть у анализа.

LLM не должна:

```text
fetch Hacker News data
calculate trend_score
invent missing story data
replace deterministic analyzer
```

## Acceptance criteria

1. Проект запускается локально.
2. Проект запускается через Docker.
3. UI открывается в браузере.
4. `/health` возвращает `200`.
5. `/hn/raw` возвращает реальные HN данные.
6. `/hn/analyze` возвращает deterministic `trend_score`.
7. `/hn/llm-report` возвращает human-readable report.
8. Demo работает в `mock` mode без API key.
9. Error handling виден и в API, и в UI.
10. README объясняет setup, endpoints, scoring rules, LLM setup и limitations.
