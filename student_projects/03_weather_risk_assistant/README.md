# Проект 3: Weather Risk Assistant

## Идея

Сделайте с нуля AI Engineering сервис, который получает погоду по координатам, детерминированно оценивает риск и объясняет результат простым языком.

В этой папке есть минимальный starter: `main.py` с `/` и `/health`, `requirements.txt` и `.env.example`. Все остальное вы проектируете сами: backend structure, services, schemas, frontend, Dockerfile и финальный README.

## Что уже дано

```text
main.py          минимальный FastAPI app
requirements.txt базовые зависимости
.env.example     стартовые переменные окружения
README.md        это ТЗ
```

Starter не содержит готового Open-Meteo client, analyzer, LLM client, UI или Dockerfile.

## Product goal

Пользователь вводит координаты:

```text
lat=51.16
lon=71.47
```

Сервис должен:

1. Получить текущую погоду через Open-Meteo.
2. Нормализовать температуру, ветер, осадки и дополнительные факторы.
3. Детерминированно посчитать `risk_level`.
4. Показать signals и recommendations.
5. Попросить LLM объяснить риск человеческим языком.

## External API

Используйте Open-Meteo API:

```text
https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation
```

Можно добавить дополнительные поля, если они улучшают анализ.

## Минимальные endpoints

```text
GET /health
GET /weather/raw?lat=51.16&lon=71.47
GET /weather/analyze?lat=51.16&lon=71.47
GET /weather/llm-report?lat=51.16&lon=71.47
```

## Обязательные TODO для реализации

1. Расширить минимальный FastAPI starter до полноценного backend.
2. Самостоятельно спроектировать структуру `services`, `schemas`, `static`.
3. Создать light UI без frontend build tools.
4. Настроить static file serving из FastAPI.
5. Проверить и при необходимости расширить `/health`.
6. Подключить Open-Meteo API.
7. Добавить request timeout.
8. Обработать invalid coordinates.
9. Обработать network errors и non-200 responses.
10. Нормализовать units.
11. Описать Pydantic schemas.
12. Реализовать `/weather/raw`.
13. Реализовать deterministic risk rules.
14. Добавить cold risk: `temperature < -20`.
15. Добавить heat risk: `temperature > 35`.
16. Добавить wind risk: `wind_speed > 50`.
17. Добавить precipitation risk: `precipitation > 10`.
18. Добавить combined risk: multiple risks -> `high`.
19. One risk -> `medium`.
20. No risks -> `low`.
21. Добавить `signals`.
22. Добавить `recommendations`.
23. Добавить explainable thresholds в response.
24. Реализовать `/weather/analyze`.
25. Составить LLM prompt, где модели запрещено менять `risk_level`.
26. Поддержать `LLM_PROVIDER=mock`.
27. Поддержать минимум один реальный provider.
28. Реализовать `/weather/llm-report`.
29. Показать в UI weather cards, signals, recommendations, raw JSON и LLM report.
30. Добавить loading/error states.
31. Сделать `.env.example`.
32. Сделать Dockerfile.
33. Проверить запуск через Docker.
34. Обновить README своего проекта.

## LLM role

LLM должна объяснить:

1. Текущий `risk_level`.
2. Главные погодные факторы.
3. Почему риск low/medium/high.
4. Простую рекомендацию.
5. Какие данные могли бы улучшить оценку.

LLM не должна:

```text
fetch weather data
calculate risk_level
override deterministic thresholds
invent weather values
replace backend analyzer
```

## Acceptance criteria

1. Проект запускается локально.
2. Проект запускается через Docker.
3. UI открывается в браузере.
4. `/health` возвращает `200`.
5. `/weather/raw` возвращает реальные Open-Meteo данные.
6. `/weather/analyze` возвращает deterministic risk analysis.
7. `/weather/llm-report` возвращает human-readable report.
8. Demo работает в `mock` mode без API key.
9. Invalid coordinates и API errors обработаны понятно.
10. README объясняет setup, endpoints, risk rules, LLM setup и limitations.
