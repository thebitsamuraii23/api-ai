from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _env_int(name: str, default: int, *, min_value: int | None = None, max_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        value = default
    else:
        try:
            value = int(raw.strip())
        except ValueError:
            value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    data_encryption_key: str
    database_path: str = "data/bot.db"
    default_language: str = "en"
    default_provider: str = "openai"
    memory_messages: int = 20
    polling_tasks_concurrency_limit: int = 64
    shared_api_key: str | None = None
    shared_provider: str = "groq"
    shared_base_url: str | None = None
    shared_token_quota: int = 5000
    openai_web_search: bool = True
    openai_web_search_tool_choice: str = "auto"
    external_web_search_mode: str = "auto"  # off|auto|always
    external_web_search_max_results: int = 5
    web_search_backend: str = "hybrid"  # server|openai|hybrid



def load_settings() -> Settings:
    memory_messages_raw = os.getenv("MEMORY_MESSAGES", "20")
    try:
        memory_messages = max(2, int(memory_messages_raw))
    except ValueError as exc:
        raise ValueError("MEMORY_MESSAGES must be an integer") from exc

    polling_tasks_concurrency_limit = _env_int(
        "POLLING_TASKS_CONCURRENCY_LIMIT",
        64,
        min_value=1,
    )

    shared_token_quota_raw = os.getenv("SHARED_TOKEN_QUOTA", "5000")
    try:
        shared_token_quota = max(100, int(shared_token_quota_raw))
    except ValueError as exc:
        raise ValueError("SHARED_TOKEN_QUOTA must be an integer") from exc

    shared_api_key = os.getenv("SHARED_API_KEY")
    if shared_api_key:
        shared_api_key = shared_api_key.strip()
    if not shared_api_key:
        shared_api_key = os.getenv("GROQ_API_KEY", "").strip() or None

    openai_web_search = _env_bool("OPENAI_WEB_SEARCH", True)
    tool_choice = (os.getenv("OPENAI_WEB_SEARCH_TOOL_CHOICE") or "auto").strip().lower()
    if tool_choice not in {"auto", "required", "none"}:
        tool_choice = "auto"

    external_mode = (os.getenv("EXTERNAL_WEB_SEARCH_MODE") or "auto").strip().lower()
    if external_mode not in {"off", "auto", "always"}:
        external_mode = "auto"
    external_max_results = _env_int("EXTERNAL_WEB_SEARCH_MAX_RESULTS", 5, min_value=1, max_value=8)

    backend = (os.getenv("WEB_SEARCH_BACKEND") or "hybrid").strip().lower()
    if backend not in {"server", "openai", "hybrid"}:
        backend = "server"

    return Settings(
        telegram_bot_token=_required_env("TELEGRAM_BOT_TOKEN"),
        data_encryption_key=_required_env("DATA_ENCRYPTION_KEY"),
        database_path=os.getenv("DATABASE_PATH", "data/bot.db"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
        default_provider=os.getenv("DEFAULT_PROVIDER", "openai"),
        memory_messages=memory_messages,
        polling_tasks_concurrency_limit=polling_tasks_concurrency_limit,
        shared_api_key=shared_api_key,
        shared_provider=os.getenv("SHARED_PROVIDER", "groq").strip().lower() or "groq",
        shared_base_url=(os.getenv("SHARED_BASE_URL") or "").strip() or None,
        shared_token_quota=shared_token_quota,
        openai_web_search=openai_web_search,
        openai_web_search_tool_choice=tool_choice,
        external_web_search_mode=external_mode,
        external_web_search_max_results=external_max_results,
        web_search_backend=backend,
    )
