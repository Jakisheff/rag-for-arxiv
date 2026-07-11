from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict

from schemas import LLMReportResponse, RepoAnalysis, RepoRawData
from services.analyzer import analyze_repo
from services.github_client import GitHubClientError, fetch_repo_raw
from services.llm_client import LLMClientError, generate_llm_report


class Settings(BaseSettings):
    github_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="GitHub Repo Health Assistant", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "github-repo-health-assistant",
        "version": "1.0.0",
    }


@app.get("/repo/raw", response_model=RepoRawData)
async def repo_raw(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
) -> RepoRawData:
    try:
        return await fetch_repo_raw(owner=owner, repo=repo, github_token=settings.github_token or None)
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/repo/analyze", response_model=RepoAnalysis)
async def repo_analyze(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
) -> RepoAnalysis:
    raw = await repo_raw(owner=owner, repo=repo)
    return analyze_repo(raw)


@app.get("/repo/llm-report", response_model=LLMReportResponse)
async def repo_llm_report(
    owner: str = Query(..., min_length=1),
    repo: str = Query(..., min_length=1),
) -> LLMReportResponse:
    analysis = await repo_analyze(owner=owner, repo=repo)
    prompt = _build_llm_prompt(analysis)

    try:
        report = await generate_llm_report(prompt)
    except LLMClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return LLMReportResponse(
        repo=analysis.repo,
        health_score=analysis.health_score,
        grade=analysis.grade,
        llm_report=report,
    )


def _build_llm_prompt(analysis: RepoAnalysis) -> str:
    return (
        "You are an AI engineering assistant.\n"
        "You do not calculate scores.\n"
        "You explain the deterministic analysis result produced by backend code.\n"
        "Use clear, simple language.\n"
        "Do not invent missing GitHub data.\n"
        "If data is missing, say that it is missing.\n\n"
        "Explain:\n"
        "1. What this repository is\n"
        "2. Why the health_score is high/medium/low\n"
        "3. Main strengths\n"
        "4. Possible risks\n"
        "5. Whether a student should study this repo\n\n"
        f"ANALYSIS_JSON:\n{analysis.model_dump_json(indent=2)}"
    )
