# AI Research Paper Scout

Сервис на FastAPI, который ищет статьи в arXiv, детерминированно считает relevance score, выделяет ключевые слова, сигналы и риски, а затем просит LLM объяснить результат простым языком.

## Структура проекта

```text
main.py                   FastAPI app, endpoints, LLM prompt
schemas.py                Pydantic-схемы (Paper, ScoredPaper, Analysis, ...)
services/arxiv_client.py  запрос к arXiv API + парсинг Atom XML
services/analyzer.py      детерминированный relevance-анализатор
services/llm_client.py    LLM-провайдеры (mock, openai_compatible, ollama, cohere, alemplus)
static/                   vanilla JS UI (index.html, styles.css, app.js)
Dockerfile                образ для запуска через Docker
.env.example              шаблон переменных окружения
```

## Setup (локально)

```bash
cd student_projects/02_arxiv_paper_scout
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # mock-режим работает без ключей
uvicorn main:app --reload --port 8000
```

UI: <http://localhost:8000>

## Setup (Docker)

```bash
docker build -t paper-scout .
docker run --rm -p 8000:8000 --env-file .env paper-scout
```

## Endpoints

```text
GET /health                                   статус сервиса
GET /papers/raw?query=rag&max_results=10      нормализованные данные arXiv
GET /papers/analyze?query=rag&max_results=10  детерминированный relevance-анализ
GET /papers/llm-report?query=rag&max_results=10  человекочитаемый отчет от LLM
```

Параметры: `query` (1–200 символов), `max_results` (1–50, по умолчанию 10).

## Scoring rules (детерминированные, 0–100)

| Компонент       | Макс. баллы | Правило                                                        |
| --------------- | ----------- | -------------------------------------------------------------- |
| Title match     | 40          | доля терминов запроса, найденных в title                        |
| Summary match   | 30          | доля терминов запроса, найденных в summary                      |
| Category match  | 15          | термин запроса встречается в какой-либо категории arXiv         |
| Freshness       | 15          | ≤1 года — 15, ≤3 лет — 10, ≤5 лет — 5, старше — 0               |

Термины запроса — токены в lowercase без стоп-слов и слов короче 2 символов. Дополнительно считаются `average_relevance`, `top_keywords` (частотные слова из title+summary), `signals` и `risks`.

## LLM setup

LLM только объясняет готовый анализ: prompt содержит `ANALYSIS_JSON` с топ-5 статьями и явно запрещает выдумывать авторов, ссылки, даты и утверждения. LLM не ходит в arXiv и не считает score.

Провайдер выбирается через `LLM_PROVIDER` в `.env`:

- `mock` (по умолчанию) — работает без API key, формирует отчет из данных анализа;
- `openai_compatible` — любой сервер с `/v1/chat/completions` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`);
- `ollama` — локальный Ollama (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`);
- `cohere` — Cohere v2 chat (`COHERE_API_KEY`, `COHERE_MODEL`);
- `alemplus` — AlemPlus OpenAI-compatible API (`ALEMPLUS_*`).

## Обработка ошибок

- Timeout запроса к arXiv настраивается через `ARXIV_REQUEST_TIMEOUT_SECONDS` (по умолчанию 10s).
- Network errors, HTTP ≥ 400, некорректный XML и не-Atom ответы → `502` с понятным `detail`.
- Пустой результат — валидный ответ: `returned=0`, в analyze появляется risk "arXiv returned no papers".
- Отсутствующие поля entry нормализуются (пустые списки, `null`-даты, "Untitled").
- UI показывает loading state (кнопки disabled) и error state (красный статус-бар).

## Limitations

- Relevance — keyword-based: не понимает синонимы и не оценивает научное качество статьи.
- `search_query=all:{query}` — простой полнотекстовый поиск без фильтров по категориям и датам.
- arXiv API имеет rate limits; кэширования нет, каждый запрос идет в API заново.
- Mock-режим не является настоящей LLM — он только переформатирует данные анализа.
- Стоп-слова только английские; запросы на других языках скорятся хуже.
