from fastapi import FastAPI


PROJECT_NAME = "Weather Risk Assistant"

REQUIRED_ENDPOINTS = [
    "GET /health",
    "GET /weather/raw?lat=51.16&lon=71.47",
    "GET /weather/analyze?lat=51.16&lon=71.47",
    "GET /weather/llm-report?lat=51.16&lon=71.47",
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
            "Create your own Open-Meteo client.",
            "Create deterministic weather risk rules.",
            "Create a Vanilla JS UI and Dockerfile.",
        ],
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "weather-risk-assistant",
        "version": "0.1.0-starter",
    }
