# ГЛАВНАЯ ЛОГИКА ФАЙЛА:
# Это входная точка FastAPI-приложения. Файл связывает три слоя между собой:
#   1. services/arxiv_client.py — ходит в arXiv API и отдает сырые статьи (/papers/raw)
#   2. services/analyzer.py     — детерминированно считает relevance score (/papers/analyze)
#   3. services/llm_client.py   — просит LLM объяснить уже готовый анализ (/papers/llm-report)
# Каждый следующий endpoint переиспользует предыдущий (llm-report вызывает analyze,
# analyze вызывает raw), поэтому вся цепочка данных всегда идет через один и тот же
# детерминированный анализатор — LLM ничего не считает и не выдумывает сама.

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemas import LLMReportResponse, PapersAnalysis, PapersRawResponse
from services.analyzer import analyze_papers
from services.arxiv_client import ArxivClientError, fetch_papers
from services.llm_client import LLMClientError, generate_llm_report

PROJECT_NAME = "AI Research Paper Scout"

# Сколько лучших (по relevance) статей отдаем в промпт LLM — чтобы не раздувать
# запрос к модели, если max_results большой (например, 50).
TOP_PAPERS_FOR_LLM = 5

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title=PROJECT_NAME, version="1.0.0")
# Раздаем статику (html/css/js) напрямую из FastAPI, без отдельного frontend-сервера.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    # Открываем UI по корневому адресу вместо стандартной FastAPI-заглушки.
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    # Проверка живости сервиса для Docker healthcheck / мониторинга.
    return {
        "status": "ok",
        "service": "ai-research-paper-scout",
        "version": "1.0.0",
    }


@app.get("/papers/raw", response_model=PapersRawResponse)
async def papers_raw(
    query: str = Query(..., min_length=1, max_length=200),
    max_results: int = Query(10, ge=1, le=50),
) -> PapersRawResponse:
    # Просто отдает нормализованные данные из arXiv без какой-либо аналитики.
    try:
        return await fetch_papers(query=query, max_results=max_results)
    except ArxivClientError as exc:
        # Любая проблема с внешним API (timeout, битый XML, network error)
        # превращается в понятный 502 для клиента, а не в 500 с трейсбеком.
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/papers/analyze", response_model=PapersAnalysis)
async def papers_analyze(
    query: str = Query(..., min_length=1, max_length=200),
    max_results: int = Query(10, ge=1, le=50),
) -> PapersAnalysis:
    # Сначала получаем сырые данные, затем прогоняем их через детерминированный
    # анализатор (relevance score, keywords, signals, risks).
    raw = await papers_raw(query=query, max_results=max_results)
    return analyze_papers(raw)


@app.get("/papers/llm-report", response_model=LLMReportResponse)
async def papers_llm_report(
    query: str = Query(..., min_length=1, max_length=200),
    max_results: int = Query(10, ge=1, le=50),
) -> LLMReportResponse:
    # Берем готовый детерминированный анализ и просим LLM пересказать его
    # простым языком — сама LLM данные не ищет и score не считает.
    analysis = await papers_analyze(query=query, max_results=max_results)
    prompt = _build_llm_prompt(analysis)

    try:
        report = await generate_llm_report(prompt)
    except LLMClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LLMReportResponse(
        query=analysis.query,
        paper_count=analysis.paper_count,
        average_relevance=analysis.average_relevance,
        llm_report=report,
    )


def _build_llm_prompt(analysis: PapersAnalysis) -> str:
    # Обрезаем список статей до топ-N по relevance — LLM объясняет только их.
    top = analysis.model_copy(update={"papers": analysis.papers[:TOP_PAPERS_FOR_LLM]})

    # Промпт явно запрещает LLM придумывать данные (авторов, ссылки, даты) и
    # заново считать score — вся фактура берется только из ANALYSIS_JSON.
    return (
        "You are an AI research reading assistant for a student.\n"
        "You do not fetch papers and you do not calculate relevance scores.\n"
        "You only explain the deterministic analysis produced by backend code.\n"
        "Use only paper details present in ANALYSIS_JSON.\n"
        "Never invent authors, titles, links, dates, or claims.\n"
        "If a detail is missing, say that it is missing.\n"
        "Use clear, simple language.\n\n"
        "For the papers in ANALYSIS_JSON, explain:\n"
        "1. What each paper is about\n"
        "2. What problem each paper solves\n"
        "3. Why each paper could be useful for a student\n"
        "4. Which paper is the easiest starting point and why\n"
        "5. Which keywords are worth exploring next\n\n"
        f"ANALYSIS_JSON:\n{top.model_dump_json(indent=2)}"
    )
