# ГЛАВНАЯ ЛОГИКА ФАЙЛА:
# Pydantic-схемы описывают форму данных на каждом шаге пайплайна:
#   Paper -> PapersRawResponse   (сырые данные из arXiv, /papers/raw)
#   ScoredPaper -> PapersAnalysis (после детерминированного анализа, /papers/analyze)
#   LLMReportResponse            (финальный ответ с текстом от LLM, /papers/llm-report)
# FastAPI использует эти классы как response_model: они валидируют данные и
# автоматически генерируют документацию в /docs.

from pydantic import BaseModel, Field


class Paper(BaseModel):
    # Один нормализованный результат из Atom-фида arXiv.
    arxiv_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    summary: str = ""
    published: str | None = None  # дата первой публикации (ISO 8601) или None
    updated: str | None = None  # дата последнего обновления версии статьи
    categories: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    link: str  # ссылка на страницу статьи (abs)
    pdf_link: str | None = None  # прямая ссылка на PDF, если есть


class PapersRawResponse(BaseModel):
    # Ответ /papers/raw: список статей + метаданные самого запроса.
    query: str
    max_results: int
    total_results: int  # сколько всего статей нашлось в arXiv по запросу
    returned: int  # сколько реально вернулось (может быть меньше max_results)
    papers: list[Paper]


class ScoreBreakdown(BaseModel):
    # Разбивка relevance_score по компонентам — чтобы было видно,
    # за что именно статья получила свои баллы (см. services/analyzer.py).
    title_match: int
    summary_match: int
    category_match: int
    freshness: int


class ScoredPaper(BaseModel):
    # Одна статья + посчитанный для нее score.
    relevance_score: int  # итоговый балл 0-100
    breakdown: ScoreBreakdown
    paper: Paper


class PapersAnalysis(BaseModel):
    # Ответ /papers/analyze: статьи, отсортированные по relevance_score,
    # плюс агрегированная статистика по всей выдаче.
    query: str
    paper_count: int
    average_relevance: float
    top_keywords: list[str]  # частотные слова из title+summary всех статей
    signals: list[str]  # позитивные наблюдения о выдаче (человекочитаемые)
    risks: list[str]  # ограничения/проблемы выдачи (человекочитаемые)
    papers: list[ScoredPaper]


class LLMReportResponse(BaseModel):
    # Ответ /papers/llm-report: краткая сводка анализа + текст от LLM.
    query: str
    paper_count: int
    average_relevance: float
    llm_report: str
