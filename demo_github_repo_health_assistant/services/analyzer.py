from datetime import datetime, timedelta, timezone

from schemas import RepoAnalysis, RepoRawData


def analyze_repo(raw: RepoRawData) -> RepoAnalysis:
    score = 0
    signals: list[str] = []
    risks: list[str] = []

    if raw.stars >= 1000:
        score += 20
        signals.append("High community adoption")

    if raw.forks >= 100:
        score += 15
        signals.append("Many forks suggest active reuse")

    if raw.license:
        score += 15
        signals.append("Has license")

    if raw.description:
        score += 15
        signals.append("Has clear repository description")

    if raw.topics:
        score += 10
        signals.append("Has topic tags")

    if _was_updated_recently(raw.updated_at):
        score += 20
        signals.append("Recently updated")
    else:
        risks.append("Repository was not updated in the last 180 days")

    if raw.open_issues > 3000:
        score -= 20
        risks.append("Very large number of open issues")
    elif raw.open_issues > 1000:
        score -= 10
        risks.append("Large number of open issues")

    health_score = max(0, min(100, score))

    return RepoAnalysis(
        repo=raw.full_name,
        health_score=health_score,
        grade=_grade_for_score(health_score),
        signals=signals,
        risks=risks,
        raw=raw,
    )


def _was_updated_recently(updated_at: str | None) -> bool:
    if not updated_at:
        return False

    try:
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    except ValueError:
        return False

    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    return updated >= cutoff


def _grade_for_score(score: int) -> str:
    if score <= 39:
        return "weak"
    if score <= 69:
        return "moderate"
    return "strong"
