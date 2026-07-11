from fastapi import FastAPI


PROJECT_NAME = "Hacker News Trend Radar"

REQUIRED_ENDPOINTS = [
    "GET /health",
    "GET /hn/raw?limit=30",
    "GET /hn/analyze?topic=ai&limit=30",
    "GET /hn/llm-report?topic=ai&limit=30",
]

app = FastAPI(title=PROJECT_NAME, version="0.1.0-starter")


@app.get("/")
async def root() -> dict:
    return {
        "project": PROJECT_NAME,
        "status": "starter",
        "message": "Only /health is implemented. Build the API, analyzer, LLM client, UI, and Docker setup yourself.",
        "required_endpoints": REQUIRED_ENDPOINTS,
        "next_steps": [
            "Create your own schemas.",
            "Create your own services for external API, analyzer, and LLM.",
            "Create a Vanilla JS UI.",
            "Add Dockerfile and update README after implementation.",
        ],
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "hacker-news-trend-radar",
        "version": "0.1.0-starter",
    }
