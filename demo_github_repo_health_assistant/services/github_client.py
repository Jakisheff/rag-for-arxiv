import httpx

from schemas import RepoRawData


class GitHubClientError(RuntimeError):
    """Raised when GitHub cannot be reached or returns an unusable response."""


async def fetch_repo_raw(owner: str, repo: str, github_token: str | None = None) -> RepoRawData:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-engineering-api-lab",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        raise GitHubClientError(f"Could not reach GitHub API: {exc}") from exc

    if response.status_code == 404:
        raise GitHubClientError(f"Repository '{owner}/{repo}' was not found.")

    if response.status_code >= 400:
        body = response.text[:300]
        raise GitHubClientError(f"GitHub API returned {response.status_code}: {body}")

    data = response.json()
    license_data = data.get("license") or {}

    return RepoRawData(
        owner=owner,
        repo=repo,
        full_name=data.get("full_name", f"{owner}/{repo}"),
        description=data.get("description"),
        stars=data.get("stargazers_count", 0),
        forks=data.get("forks_count", 0),
        open_issues=data.get("open_issues_count", 0),
        license=license_data.get("spdx_id") or license_data.get("name"),
        topics=data.get("topics") or [],
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        html_url=data.get("html_url", url),
    )
