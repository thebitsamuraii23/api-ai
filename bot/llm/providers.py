from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Provider:
    id: str
    title: str
    default_model: str
    base_url: str | None = None


PROVIDERS: dict[str, Provider] = {
    "shared_ai": Provider(
        id="shared_ai",
        title="Shared AI",
        default_model="",
        base_url=None,
    ),
    "openai": Provider(
        id="openai",
        title="OpenAI",
        default_model="gpt-4o-mini",
        base_url=None,
    ),
    "groq": Provider(
        id="groq",
        title="Groq",
        default_model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
    ),
    "openrouter": Provider(
        id="openrouter",
        title="OpenRouter",
        default_model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
    ),
    "together": Provider(
        id="together",
        title="Together AI",
        default_model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        base_url="https://api.together.xyz/v1",
    ),
    "deepinfra": Provider(
        id="deepinfra",
        title="DeepInfra",
        default_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        base_url="https://api.deepinfra.com/v1/openai",
    ),
    "google": Provider(
        id="google",
        title="Google AI Studio",
        default_model="gemini-2.0-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    "custom": Provider(
        id="custom",
        title="Custom OpenAI-compatible",
        default_model="gpt-4o-mini",
        base_url=None,
    ),
}

PROVIDER_ICONS: dict[str, str] = {
    "shared_ai": "🤖",
    "openai": "🧠",
    "groq": "⚡",
    "openrouter": "🛰️",
    "together": "🤝",
    "deepinfra": "🧬",
    "google": "🔷",
    "custom": "🛠️",
}


def provider_ids() -> tuple[str, ...]:
    return tuple(PROVIDERS.keys())


def provider_label(provider_id: str) -> str:
    provider = PROVIDERS.get(provider_id)
    if not provider:
        return provider_id
    icon = PROVIDER_ICONS.get(provider_id, "🤖")
    return f"{icon} {provider.title}"
