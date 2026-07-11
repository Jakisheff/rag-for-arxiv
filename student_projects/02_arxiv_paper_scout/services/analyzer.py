# ГЛАВНАЯ ЛОГИКА ФАЙЛА:
# Детерминированный (без LLM) подсчет relevance score для каждой статьи, 0-100.
# analyze_papers() — точка входа: токенизирует query, скорит каждую статью через
# _score_paper(), сортирует по убыванию score и собирает сводку (keywords,
# signals, risks). Score складывается из 4 независимых компонентов:
#   title_match (до 40) + summary_match (до 30) + category_match (15) + freshness (до 15)
# Чем больше слов запроса встречается в title/summary и чем новее статья —
# тем выше итоговый балл. Никакого ML/LLM здесь нет — только текстовые
# совпадения и разница дат, поэтому результат воспроизводим и объясним.

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from schemas import PapersAnalysis, PapersRawResponse, ScoreBreakdown, ScoredPaper

# Максимальное число баллов за каждый компонент score. Сумма максимумов
# (40+30+15+15) = 100, что и дает верхнюю границу relevance_score.
TITLE_MATCH_MAX = 40
SUMMARY_MATCH_MAX = 30
CATEGORY_MATCH_POINTS = 15
FRESHNESS_MAX = 15

# Частые служебные/общенаучные слова, которые исключаем при токенизации —
# иначе они засоряли бы top_keywords и искусственно завышали summary_match.
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "we", "with",
    "our", "can", "using", "based", "via", "new", "paper", "propose",
    "proposed", "approach", "method", "methods", "model", "models",
    "results", "show", "study", "which", "these", "their", "such", "both",
    "than", "more", "also", "have", "has", "been", "its", "into", "between",
}


def analyze_papers(raw: PapersRawResponse) -> PapersAnalysis:
    # Разбиваем поисковый запрос на значимые слова один раз — они переиспользуются
    # для скоринга каждой статьи.
    query_terms = _tokenize(raw.query)
    scored = sorted(
        (_score_paper(paper, query_terms) for paper in raw.papers),
        key=lambda item: item.relevance_score,
        reverse=True,  # статьи с наивысшим score идут первыми
    )

    average = (
        round(sum(item.relevance_score for item in scored) / len(scored), 1)
        if scored
        else 0.0
    )

    return PapersAnalysis(
        query=raw.query,
        paper_count=len(scored),
        average_relevance=average,
        top_keywords=_top_keywords(raw),
        signals=_build_signals(scored, average, query_terms),
        risks=_build_risks(raw, scored, query_terms),
        papers=scored,
    )


def _score_paper(paper, query_terms: list[str]) -> ScoredPaper:
    # set() — чтобы одно и то же слово не учитывалось дважды в title/summary.
    title_terms = set(_tokenize(paper.title))
    summary_terms = set(_tokenize(paper.summary))

    breakdown = ScoreBreakdown(
        title_match=_coverage_points(query_terms, title_terms, TITLE_MATCH_MAX),
        summary_match=_coverage_points(query_terms, summary_terms, SUMMARY_MATCH_MAX),
        category_match=CATEGORY_MATCH_POINTS if _matches_category(paper, query_terms) else 0,
        freshness=_freshness_points(paper.published),
    )

    total = (
        breakdown.title_match
        + breakdown.summary_match
        + breakdown.category_match
        + breakdown.freshness
    )
    return ScoredPaper(
        # max/min на случай будущих правок весов — score всегда остается в 0-100.
        relevance_score=max(0, min(100, total)),
        breakdown=breakdown,
        paper=paper,
    )


def _coverage_points(query_terms: list[str], text_terms: set[str], max_points: int) -> int:
    # Пропорционально max_points в зависимости от доли слов запроса,
    # найденных в тексте. Пример: 2 из 3 слов запроса есть в title,
    # max_points=40 -> round(40 * 2/3) = 27 баллов.
    if not query_terms:
        return 0
    matched = sum(1 for term in query_terms if term in text_terms)
    return round(max_points * matched / len(query_terms))


def _matches_category(paper, query_terms: list[str]) -> bool:
    # Проверяем, встречается ли слово запроса как подстрока в коде категории
    # arXiv (например запрос "rag" совпадет с категорией "cs.IR" не будет,
    # а "cl" совпадет с "cs.CL").
    categories = [category.lower() for category in paper.categories]
    return any(term in category for term in query_terms for category in categories)


def _freshness_points(published: str | None) -> int:
    # Чем свежее статья, тем больше баллов: <=1 года - максимум, дальше
    # ступенчато убывает, старше 5 лет - 0.
    published_at = _parse_date(published)
    if published_at is None:
        return 0

    age = datetime.now(timezone.utc) - published_at
    if age <= timedelta(days=365):
        return FRESHNESS_MAX
    if age <= timedelta(days=3 * 365):
        return 10
    if age <= timedelta(days=5 * 365):
        return 5
    return 0


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # arXiv отдает даты в формате "...Z" (UTC) — fromisoformat не понимает
        # "Z" напрямую, поэтому меняем на "+00:00".
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _top_keywords(raw: PapersRawResponse, limit: int = 10) -> list[str]:
    # Считаем частоту слов по всем title+summary выдачи и берем самые частые —
    # это не относится к конкретной статье, а описывает выдачу в целом.
    counter: Counter[str] = Counter()
    for paper in raw.papers:
        counter.update(term for term in _tokenize(f"{paper.title} {paper.summary}") if len(term) > 2)
    return [word for word, _ in counter.most_common(limit)]


def _build_signals(scored: list[ScoredPaper], average: float, query_terms: list[str]) -> list[str]:
    # Позитивные, человекочитаемые наблюдения о качестве выдачи для UI/LLM.
    if not scored:
        return []

    signals: list[str] = []

    title_hits = sum(1 for item in scored if item.breakdown.title_match == TITLE_MATCH_MAX)
    if title_hits:
        signals.append(f"{title_hits} of {len(scored)} papers mention every query term in the title.")

    fresh = sum(1 for item in scored if item.breakdown.freshness == FRESHNESS_MAX)
    if fresh:
        signals.append(f"{fresh} of {len(scored)} papers were published within the last year.")

    if average >= 60:
        signals.append(f"Average relevance is high ({average}/100) for query terms: {', '.join(query_terms)}.")

    # scored уже отсортирован по убыванию score, поэтому scored[0] — лучший.
    best = scored[0]
    signals.append(
        f"Best match is '{best.paper.title}' with relevance {best.relevance_score}/100."
    )
    return signals


def _build_risks(
    raw: PapersRawResponse, scored: list[ScoredPaper], query_terms: list[str]
) -> list[str]:
    # Ограничения/проблемы выдачи, о которых стоит предупредить пользователя.
    risks: list[str] = []

    if not scored:
        risks.append("arXiv returned no papers for this query.")
        return risks

    if not query_terms:
        # Например, если весь запрос состоит из стоп-слов ("the a of").
        risks.append("The query contains only stopwords, so text matching scored 0 for all papers.")

    if raw.returned < raw.max_results:
        risks.append(f"arXiv returned only {raw.returned} of {raw.max_results} requested papers.")

    if all(item.breakdown.title_match == 0 for item in scored):
        risks.append("No paper mentions the query terms in its title; matches come from summaries only.")

    if all(item.breakdown.freshness == 0 for item in scored):
        risks.append("All papers are older than 5 years; results may be outdated.")

    # Это ограничение актуально всегда, вне зависимости от конкретной выдачи.
    risks.append(
        "Relevance is keyword-based and deterministic; it cannot judge scientific quality or novelty."
    )
    return risks


def _tokenize(text: str) -> list[str]:
    # Приводим к нижнему регистру, режем по всему, что не буква/цифра,
    # выкидываем однобуквенные токены и стоп-слова.
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]
