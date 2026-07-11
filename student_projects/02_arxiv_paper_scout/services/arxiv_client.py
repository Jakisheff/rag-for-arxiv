# ГЛАВНАЯ ЛОГИКА ФАЙЛА:
# Этот модуль — единственное место, где сервис ходит во внешний arXiv API.
# 1. fetch_papers() отправляет HTTP GET на export.arxiv.org с query-параметрами.
# 2. arXiv отвечает Atom XML (не JSON!), поэтому _parse_xml() парсит его через
#    стандартный xml.etree.ElementTree с явными XML-namespace'ами.
# 3. Каждый <entry> превращается в Paper (_parse_entry) — нормализуем title,
#    authors, summary, даты, категории и ссылки в единый плоский формат.
# 4. Любая ошибка (timeout, сеть, битый XML, не-Atom ответ) оборачивается в
#    ArxivClientError, чтобы main.py мог поймать её одним except и вернуть 502.

import re
import xml.etree.ElementTree as ET

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from schemas import Paper, PapersRawResponse

ARXIV_API_URL = "https://export.arxiv.org/api/query"

# arXiv отдает Atom-фид с несколькими XML-namespace'ами. ElementTree требует
# указывать их явно при поиске тегов (например "atom:entry", а не "entry").
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivClientError(RuntimeError):
    """Raised when arXiv data cannot be fetched or parsed."""


class Settings(BaseSettings):
    # Настройки читаются из .env (или переменных окружения).
    arxiv_request_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


async def fetch_papers(query: str, max_results: int) -> PapersRawResponse:
    # search_query=all:{query} — ищет термин по всем полям статьи (title,
    # summary, authors и т.д.), start=0 — всегда с первой страницы результатов.
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.arxiv_request_timeout_seconds) as client:
            response = await client.get(ARXIV_API_URL, params=params)
    except httpx.TimeoutException as exc:
        # Отдельно ловим timeout, чтобы дать пользователю понятное сообщение
        # вместо общего "request failed".
        raise ArxivClientError(
            f"arXiv request timed out after {settings.arxiv_request_timeout_seconds}s."
        ) from exc
    except httpx.RequestError as exc:
        # Сюда попадают DNS-ошибки, разрыв соединения и т.п.
        raise ArxivClientError(f"arXiv request failed: {exc}") from exc

    if response.status_code >= 400:
        raise ArxivClientError(f"arXiv returned HTTP {response.status_code}.")

    root = _parse_xml(response.text)
    # Каждый <entry> в фиде — это одна статья.
    papers = [_parse_entry(entry) for entry in root.findall("atom:entry", NAMESPACES)]

    return PapersRawResponse(
        query=query,
        max_results=max_results,
        total_results=_parse_total_results(root, fallback=len(papers)),
        returned=len(papers),
        papers=papers,
    )


def _parse_xml(text: str) -> ET.Element:
    # Ловим как синтаксически битый XML, так и валидный XML, но не Atom-фид
    # (например, если arXiv вдруг вернул HTML-страницу с ошибкой).
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ArxivClientError(f"arXiv returned malformed XML: {exc}") from exc

    if root.tag != f"{{{NAMESPACES['atom']}}}feed":
        raise ArxivClientError("arXiv response is not an Atom feed.")
    return root


def _parse_total_results(root: ET.Element, fallback: int) -> int:
    # <opensearch:totalResults> — общее число статей, подходящих под запрос
    # (может быть намного больше, чем max_results/returned).
    node = root.find("opensearch:totalResults", NAMESPACES)
    try:
        return int(node.text) if node is not None and node.text else fallback
    except ValueError:
        return fallback


def _parse_entry(entry: ET.Element) -> Paper:
    # <atom:id> обычно выглядит как "http://arxiv.org/abs/2401.15391v1" —
    # берем последний сегмент URL как короткий arxiv_id.
    entry_id = _text(entry, "atom:id")
    links = entry.findall("atom:link", NAMESPACES)

    return Paper(
        arxiv_id=entry_id.rsplit("/", 1)[-1] if entry_id else "unknown",
        title=_text(entry, "atom:title") or "Untitled",
        # У каждой статьи может быть несколько <author><name>...</name></author>.
        authors=[
            name
            for author in entry.findall("atom:author", NAMESPACES)
            if (name := _text(author, "atom:name"))
        ],
        summary=_text(entry, "atom:summary"),
        published=_text(entry, "atom:published") or None,
        updated=_text(entry, "atom:updated") or None,
        # <category term="cs.CL"/> — arXiv хранит категории как атрибут term,
        # а не как текст тега.
        categories=[
            term
            for category in entry.findall("atom:category", NAMESPACES)
            if (term := category.get("term", "").strip())
        ],
        primary_category=_primary_category(entry),
        # rel="alternate" — обычная веб-страница статьи; title="pdf" — прямой PDF.
        link=_link(links, rel="alternate") or entry_id or "",
        pdf_link=_link(links, title="pdf"),
    )


def _primary_category(entry: ET.Element) -> str | None:
    # Основная (главная) категория статьи — отдельный тег из arxiv-namespace,
    # отличается от списка всех <atom:category>.
    node = entry.find("arxiv:primary_category", NAMESPACES)
    if node is not None and node.get("term"):
        return node.get("term")
    return None


def _link(links: list[ET.Element], rel: str | None = None, title: str | None = None) -> str | None:
    # Одна статья содержит несколько <link>: страница статьи, PDF, doi и т.д.
    # Ищем нужную по атрибуту rel или title.
    for link in links:
        if rel and link.get("rel") == rel and link.get("href"):
            return link.get("href")
        if title and link.get("title") == title and link.get("href"):
            return link.get("href")
    return None


def _text(node: ET.Element, path: str) -> str:
    child = node.find(path, NAMESPACES)
    if child is None or not child.text:
        return ""
    # arXiv wraps long titles/summaries with newlines and indentation.
    return re.sub(r"\s+", " ", child.text).strip()
