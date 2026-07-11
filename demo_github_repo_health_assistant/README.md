# GitHub Repo Health Assistant

Это demo-проект преподавателя для AI Engineering API Lab.

Приложение получает данные о публичном GitHub-репозитории через GitHub REST API, считает deterministic health score в Python и просит LLM-провайдера объяснить результат простым языком.

Важно:

```text
LLM не считает итоговый score/risk/relevance.
Backend считает его детерминированно.
LLM только объясняет результат человеческим языком.
```

## Архитектура

```text
GitHub REST API
        ↓
FastAPI backend
        ↓
health_score / deterministic analysis
        ↓
LLM report
        ↓
Browser UI
```

## Установка без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Запуск без Docker

```bash
uvicorn main:app --reload
```

Открыть:

```text
http://localhost:8000
```

## Запуск через Docker

Из этой папки:

```bash
cp .env.example .env
docker build -t github-repo-health-assistant .
docker run --rm --env-file .env -p 8000:8000 github-repo-health-assistant
```

Или из корня репозитория:

```bash
docker compose up --build demo
```

Открыть:

```text
http://localhost:8000
```

## Настройка LLM-провайдера (LLM Provider Setup)

Режим по умолчанию — `mock`, поэтому demo работает без API-ключа.

### 1. Режим mock

```env
LLM_PROVIDER=mock
```

Отчет будет начинаться с:

```text
[MOCK LLM REPORT]
```

### 2. Режим OpenAI-compatible

Используйте любого провайдера с OpenAI Chat Completions-compatible API.

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=http://localhost:8001/v1
LLM_API_KEY=your_key_here
LLM_MODEL=your_model_here
```

Backend вызывает:

```text
{LLM_BASE_URL}/chat/completions
```

### 3. Режим Ollama

Установите Ollama и скачайте модель:

```bash
ollama pull llama3.1
```

Настройка:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

Backend вызывает:

```text
{OLLAMA_BASE_URL}/api/chat
```

### 4. Режим Cohere

Настройка:

```env
LLM_PROVIDER=cohere
COHERE_API_KEY=your_cohere_key_here
COHERE_MODEL=command-a-03-2025
```

Backend вызывает Cohere v2 Chat API и читает `message.content`.

### 5. Режим AlemPlus

AlemPlus используется как OpenAI-compatible provider.

Настройка:

```env
LLM_PROVIDER=alemplus
ALEMPLUS_BASE_URL=https://llm.alem.ai/v1
ALEMPLUS_API_KEY=your_alemplus_key_here
ALEMPLUS_MODEL=gemma4
```

Backend вызывает:

```text
{ALEMPLUS_BASE_URL}/chat/completions
```

с авторизацией:

```text
Authorization: Bearer {ALEMPLUS_API_KEY}
```

Если AlemPlus недоступен или возвращает ошибку, API вернет понятное сообщение об ошибке и не упадет.

## API эндпоинты

### `GET /health`

Возвращает статус сервиса.

### `GET /repo/raw?owner=fastapi&repo=fastapi`

Получает полезные raw-поля репозитория из GitHub.

### `GET /repo/analyze?owner=fastapi&repo=fastapi`

Получает данные из GitHub и считает deterministic health score.

Правила scoring:

```text
Base score: 0
+20 если stars >= 1000
+15 если forks >= 100
+15 если есть license
+15 если есть description
+10 если есть topics
+20 если repo обновлялся за последние 180 дней
-10 если open issues > 1000
-20 если open issues > 3000
Итоговый score ограничивается от 0 до 100.
```

Правила grade:

```text
0-39: weak
40-69: moderate
70-100: strong
```

### `GET /repo/llm-report?owner=fastapi&repo=fastapi`

Берет deterministic analysis result и просит выбранный LLM provider объяснить его.

## Использование UI

1. Введите `owner=fastapi`.
2. Введите `repo=fastapi`.
3. Нажмите `Fetch Raw Data`.
4. Нажмите `Analyze Repo`.
5. Нажмите `Generate LLM Report`.

## Пример demo flow

1. Запустите сервер.
2. Откройте `http://localhost:8000`.
3. Введите `owner=fastapi` и `repo=fastapi`.
4. Нажмите `Fetch Raw Data`.
5. Нажмите `Analyze Repo`.
6. Нажмите `Generate LLM Report`.

## Ограничения

1. GitHub ограничивает количество unauthenticated requests. Для увеличения лимита задайте `GITHUB_TOKEN`.
2. Score специально простой, чтобы студенты поняли идею за 2 часа.
3. LLM report может ошибаться, если реальная модель игнорирует инструкции. Source of truth — backend analysis.
4. База данных не используется; каждый запрос получает свежие данные.
