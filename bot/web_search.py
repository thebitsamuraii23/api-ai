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


@dataclass(frozen=True, slots=True)
class WebPageExtract:
    source_index: int
    title: str
    url: str
    text: str


_DDG_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
    r'(?:<a[^>]+class="result__snippet"[^>]*>(.*?)</a>|<div[^>]+class="result__snippet"[^>]*>(.*?)</div>)',
    re.S,
)


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def _squash_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _clean_html_to_text(value: str) -> str:
    text = value or ""
    text = re.sub(r"(?is)<(script|style|noscript|template|svg|canvas|iframe)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|section|article|li|h1|h2|h3|h4|h5|h6|tr)>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "• ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _truncate_text(value: str, *, max_chars: int) -> str:
    text = _squash_whitespace(value)
    if len(text) <= max_chars:
        return text
    trimmed = text[: max(0, max_chars - 1)].rstrip()
    return f"{trimmed}…"


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


def _normalize_wiki_language(language: str | None) -> str:
    value = (language or "").strip().lower()
    if not value:
        return "en"
    aliases = {
        "en": "en",
        "ru": "ru",
        "es": "es",
        "fr": "fr",
        "tr": "tr",
        "ar": "ar",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "uk": "uk",
        "hi": "hi",
    }
    return aliases.get(value, "en")


async def wikipedia_search(
    query: str,
    *,
    max_results: int = 5,
    timeout_s: float = 12.0,
    language: str = "en",
) -> list[WebSearchResult]:
    q = (query or "").strip()
    if not q:
        return []

    wiki_lang = _normalize_wiki_language(language)
    endpoint = f"https://{wiki_lang}.wikipedia.org/w/api.php"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)"}
    params = {
        "action": "query",
        "list": "search",
        "srsearch": q,
        "utf8": "1",
        "format": "json",
        "srlimit": max(1, int(max_results)),
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(endpoint, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    items = ((payload or {}).get("query") or {}).get("search") or []
    results: list[WebSearchResult] = []
    for item in items:
        title = str(item.get("title") or "").strip()
        snippet_html = str(item.get("snippet") or "").strip()
        snippet = html.unescape(_strip_tags(snippet_html))
        if not title:
            continue
        article = title.replace(" ", "_")
        url = f"https://{wiki_lang}.wikipedia.org/wiki/{article}"
        results.append(WebSearchResult(title=title, url=url, snippet=snippet))
        if len(results) >= max(1, int(max_results)):
            break
    return results


async def github_user_search(query: str, *, max_results: int = 5, timeout_s: float = 12.0) -> list[WebSearchResult]:
    q = (query or "").strip()
    if not q:
        return []

    endpoint = "https://api.github.com/search/users"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)",
        "Accept": "application/vnd.github+json",
    }
    params = {
        "q": f"{q} in:login",
        "per_page": max(1, int(max_results)),
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(endpoint, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    results: list[WebSearchResult] = []
    for item in (payload or {}).get("items") or []:
        login = str(item.get("login") or "").strip()
        url = str(item.get("html_url") or "").strip()
        item_type = str(item.get("type") or "").strip()
        if not login or not url:
            continue
        snippet = f"GitHub {item_type}".strip()
        results.append(WebSearchResult(title=f"GitHub profile: {login}", url=url, snippet=snippet))
        if len(results) >= max(1, int(max_results)):
            break
    return results


async def gitlab_user_search(query: str, *, max_results: int = 5, timeout_s: float = 12.0) -> list[WebSearchResult]:
    q = (query or "").strip()
    if not q:
        return []

    endpoint = "https://gitlab.com/api/v4/users"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)"}
    params = {
        "search": q,
        "per_page": max(1, int(max_results)),
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        resp = await client.get(endpoint, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    results: list[WebSearchResult] = []
    for item in payload or []:
        username = str(item.get("username") or "").strip()
        web_url = str(item.get("web_url") or "").strip()
        name = str(item.get("name") or "").strip()
        if not username or not web_url:
            continue
        title = f"GitLab profile: {username}" if not name else f"GitLab profile: {username} ({name})"
        results.append(WebSearchResult(title=title, url=web_url, snippet="GitLab user profile"))
        if len(results) >= max(1, int(max_results)):
            break
    return results


def _reddit_json_url(url: str) -> str:
    safe = (url or "").strip()
    if not safe:
        return ""
    parsed = urlparse(safe)
    path = parsed.path or "/"
    if not path.endswith(".json"):
        if path.endswith("/"):
            path = f"{path[:-1]}.json"
        else:
            path = f"{path}.json"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme or 'https'}://{parsed.netloc}{path}{query}"


async def _fetch_reddit_extract(
    *,
    client: httpx.AsyncClient,
    url: str,
    source_index: int,
    max_chars: int,
) -> WebPageExtract | None:
    json_url = _reddit_json_url(url)
    if not json_url:
        return None
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)"}
    resp = await client.get(json_url, headers=headers)
    resp.raise_for_status()
    payload = resp.json()

    title = ""
    text = ""
    if isinstance(payload, list) and payload:
        first = payload[0] if payload else {}
        children = (((first or {}).get("data") or {}).get("children") or []) if isinstance(first, dict) else []
        if children and isinstance(children[0], dict):
            data = (children[0].get("data") or {}) if isinstance(children[0], dict) else {}
            title = str(data.get("title") or "").strip()
            selftext = str(data.get("selftext") or "").strip()
            text = selftext or str(data.get("subreddit_name_prefixed") or "").strip()

    if not title:
        title = "Reddit"
    if not text:
        text = title
    excerpt = _truncate_text(text, max_chars=max_chars)
    if not excerpt:
        return None
    return WebPageExtract(source_index=source_index, title=title, url=url, text=excerpt)


async def _fetch_html_extract(
    *,
    client: httpx.AsyncClient,
    url: str,
    source_index: int,
    max_chars: int,
) -> WebPageExtract | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; UrAI/1.0; +https://example.invalid)",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = await client.get(url, headers=headers)
    resp.raise_for_status()
    html_text = resp.text

    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html_text)
    title = _squash_whitespace(_strip_tags(title_match.group(1))) if title_match else ""
    cleaned = _clean_html_to_text(html_text)
    if not cleaned:
        return None

    excerpt = _truncate_text(cleaned, max_chars=max_chars)
    if not excerpt:
        return None
    return WebPageExtract(
        source_index=source_index,
        title=title or url,
        url=url,
        text=excerpt,
    )


async def fetch_page_extracts(
    results: Iterable[WebSearchResult],
    *,
    max_pages: int = 3,
    max_chars_per_page: int = 1200,
    timeout_s: float = 10.0,
) -> list[WebPageExtract]:
    items = list(results)
    if not items:
        return []
    capped = items[: max(1, int(max_pages))]
    extracts: list[WebPageExtract] = []

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
        for idx, item in enumerate(capped, start=1):
            url = (item.url or "").strip()
            if not url:
                continue
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            try:
                if "reddit.com" in host:
                    extract = await _fetch_reddit_extract(
                        client=client,
                        url=url,
                        source_index=idx,
                        max_chars=max_chars_per_page,
                    )
                else:
                    extract = await _fetch_html_extract(
                        client=client,
                        url=url,
                        source_index=idx,
                        max_chars=max_chars_per_page,
                    )
            except Exception:  # noqa: BLE001
                extract = None
            if extract:
                extracts.append(extract)
    return extracts


def format_page_extracts(extracts: Iterable[WebPageExtract]) -> str:
    items = list(extracts)
    if not items:
        return ""
    lines: list[str] = ["Fetched page excerpts:"]
    for item in items:
        lines.append(f"[{item.source_index}] {item.title} ({item.url})")
        lines.append(item.text)
        lines.append("")
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
