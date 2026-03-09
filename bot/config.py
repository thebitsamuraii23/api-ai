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


@dataclass(slots=True)
class Settings:
    telegram_bot_token: str
    data_encryption_key: str
    database_path: str = "data/bot.db"
    default_language: str = "en"
    default_provider: str = "openai"
    memory_messages: int = 20
    shared_api_key: str | None = None
    shared_provider: str = "groq"
    shared_base_url: str | None = None
    shared_token_quota: int = 5000



def load_settings() -> Settings:
    memory_messages_raw = os.getenv("MEMORY_MESSAGES", "20")
    try:
        memory_messages = max(2, int(memory_messages_raw))
    except ValueError as exc:
        raise ValueError("MEMORY_MESSAGES must be an integer") from exc

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

    return Settings(
        telegram_bot_token=_required_env("TELEGRAM_BOT_TOKEN"),
        data_encryption_key=_required_env("DATA_ENCRYPTION_KEY"),
        database_path=os.getenv("DATABASE_PATH", "data/bot.db"),
        default_language=os.getenv("DEFAULT_LANGUAGE", "en"),
        default_provider=os.getenv("DEFAULT_PROVIDER", "openai"),
        memory_messages=memory_messages,
        shared_api_key=shared_api_key,
        shared_provider=os.getenv("SHARED_PROVIDER", "groq").strip().lower() or "groq",
        shared_base_url=(os.getenv("SHARED_BASE_URL") or "").strip() or None,
        shared_token_quota=shared_token_quota,
    )
