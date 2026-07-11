from pydantic import BaseModel, Field


class RepoRawData(BaseModel):
    owner: str
    repo: str
    full_name: str
    description: str | None = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    license: str | None = None
    topics: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    html_url: str


class RepoAnalysis(BaseModel):
    repo: str
    health_score: int
    grade: str
    signals: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    raw: RepoRawData


class LLMReportResponse(BaseModel):
    repo: str
    health_score: int
    grade: str
    llm_report: str
