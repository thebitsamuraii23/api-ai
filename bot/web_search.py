from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

import httpx


@dataclass(frozen=True, slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str


_DDG_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'(?:<a[^>]+class="result__snippet"[^>]*>(.*?)</a>|<div[^>]+class="result__snippet"[^>]*>(.*?)</div>)',
    re.S,
)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def _unwrap_duckduckgo_url(href: str) -> str:
    # DDG uses redirect links like:
    # //duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&rut=...
    safe = html.unescape(href or "").strip()
    if safe.startswith("//"):
        safe = "https:" + safe
    parsed = urlparse(safe)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        uddg = (qs.get("uddg") or [None])[0]
        if uddg:
            return unquote(uddg)
    return safe


async def duckduckgo_search(query: str, *, max_results: int = 5, timeout_s: float = 12.0) -> list[WebSearchResult]:
    q = (query or "").strip()
    if not q:
        return []

    url = "https://duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(url, params={"q": q}, headers=headers)
        resp.raise_for_status()
        page = resp.text

    results: list[WebSearchResult] = []
    for match in _DDG_RESULT_RE.finditer(page):
        href = match.group(1) or ""
        title_html = match.group(2) or ""
        snippet_html = match.group(3) or match.group(4) or ""

        title = html.unescape(_strip_tags(title_html))
        snippet = html.unescape(_strip_tags(snippet_html))
        target_url = _unwrap_duckduckgo_url(href)

        if not title or not target_url:
            continue
        results.append(WebSearchResult(title=title, url=target_url, snippet=snippet))
        if len(results) >= max(1, int(max_results)):
            break

    return results


def _has_cyrillic(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яЁё]", text or ""))


def _query_has_explicit_date_or_day_hint(query: str) -> bool:
    value = (query or "").lower()
    if not value:
        return False
    if any(token in value for token in ("today", "сегодня", "yesterday", "вчера", "недел", "week", "month", "месяц")):
        return True
    return bool(
        re.search(
            r"\b\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\b|\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b",
            value,
        )
    )


def _looks_like_latest_news_query(query: str) -> bool:
    value = (query or "").lower()
    if not value:
        return False
    news_words = ("news", "новост", "headline", "заголов")
    return any(word in value for word in news_words)


def _dated_news_query(base_query: str, *, target_date: date, is_today: bool) -> str:
    trimmed = (base_query or "").strip()
    if not trimmed:
        return ""
    iso_date = target_date.isoformat()
    if is_today:
        day_hint = "сегодня" if _has_cyrillic(trimmed) else "today"
        return f"{trimmed} {iso_date} {day_hint}".strip()
    return f"{trimmed} {iso_date}".strip()


async def duckduckgo_search_news_aware(
    query: str,
    *,
    max_results: int = 5,
    timeout_s: float = 12.0,
    max_days_back: int = 7,
) -> list[WebSearchResult]:
    """
    For latest-news style queries, try today's date first and then walk back day by day.
    Falls back to the original query when date-scoped attempts yield no results.
    """
    normalized = (query or "").strip()
    if not normalized:
        return []

    if not _looks_like_latest_news_query(normalized) or _query_has_explicit_date_or_day_hint(normalized):
        return await duckduckgo_search(normalized, max_results=max_results, timeout_s=timeout_s)

    days_back = max(0, int(max_days_back))
    today = datetime.now(timezone.utc).date()

    for day_shift in range(days_back + 1):
        target_date = today - timedelta(days=day_shift)
        dated_query = _dated_news_query(
            normalized,
            target_date=target_date,
            is_today=(day_shift == 0),
        )
        if not dated_query:
            continue
        results = await duckduckgo_search(dated_query, max_results=max_results, timeout_s=timeout_s)
        if results:
            return results

    return await duckduckgo_search(normalized, max_results=max_results, timeout_s=timeout_s)


def format_search_results(results: Iterable[WebSearchResult]) -> str:
    items = list(results)
    if not items:
        return ""
    lines: list[str] = ["Web search results (DuckDuckGo):"]
    for idx, item in enumerate(items, start=1):
        snippet = f" - {item.snippet}" if item.snippet else ""
        lines.append(f"{idx}. {item.title} ({item.url}){snippet}")
    return "\n".join(lines).strip()


async def fetch_time_is_datetime(url: str, *, timeout_s: float = 12.0) -> tuple[str, str] | None:
    """
    Extract current local time from a time.is page.

    Returns (date_str, time_str) in English when possible, e.g.
    ("Saturday, March 14, 2026", "16:34:28")
    """
    safe_url = (url or "").strip()
    if not safe_url:
        return None
    parsed = urlparse(safe_url)
    if parsed.netloc.lower() not in {"time.is", "www.time.is"}:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(safe_url, headers=headers)
        resp.raise_for_status()
        html_text = resp.text

    clock_match = re.search(r'id="clock"[^>]*>([^<]+)<', html_text)
    date_match = re.search(r'id="dd"[^>]*>([^<]+)<', html_text)
    if not clock_match:
        return None
    time_str = clock_match.group(1).strip()
    date_str = (date_match.group(1).strip() if date_match else "").strip()
    if not time_str:
        return None
    return (date_str, time_str)


async def fetch_time_is_utc_offset(url: str, *, timeout_s: float = 12.0) -> int | None:
    """
    Extract UTC offset (in minutes) from a time.is page.
    Example: "UTC -7" -> -420, "UTC +4" -> 240.
    """
    safe_url = (url or "").strip()
    if not safe_url:
        return None
    parsed = urlparse(safe_url)
    if parsed.netloc.lower() not in {"time.is", "www.time.is"}:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(safe_url, headers=headers)
        resp.raise_for_status()
        html_text = resp.text

    match = re.search(r"UTC\\s*([+-])\\s*(\\d{1,2})(?::(\\d{2}))?", html_text)
    if not match:
        return None
    sign = -1 if match.group(1) == "-" else 1
    hours = int(match.group(2))
    minutes = int(match.group(3) or 0)
    return sign * (hours * 60 + minutes)
