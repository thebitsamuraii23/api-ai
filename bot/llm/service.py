from __future__ import annotations

import asyncio
import os
from typing import Any

from openai import AsyncOpenAI

from bot.llm.providers import PROVIDERS


class LLMServiceError(RuntimeError):
    pass


def _env_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    return max(1, value)


def _env_csv(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


class LLMService:
    _max_concurrency = _env_positive_int("LLM_MAX_CONCURRENCY", 24)
    _request_semaphore = asyncio.Semaphore(_max_concurrency)
    _transcription_model_overrides = _env_csv("TRANSCRIPTION_MODELS")

    @staticmethod
    def _supports_openai_responses(*, provider_id: str, base_url: str | None) -> bool:
        if provider_id == "openai":
            return True
        if provider_id == "custom" and base_url and "openai.com" in base_url.lower():
            return True
        return False

    @staticmethod
    def _to_responses_input(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Convert Chat Completions-style multimodal content to Responses API format.

        - {"type": "text"} -> {"type": "input_text"}
        - {"type": "image_url", "image_url": {"url": ...}} -> {"type": "input_image", "image_url": "..."}
        """
        converted: list[dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            new_msg = dict(msg)
            content = new_msg.get("content")
            if isinstance(content, list):
                new_content: list[dict[str, Any]] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    item_type = item.get("type")
                    if item_type == "text":
                        text = item.get("text")
                        if text:
                            new_content.append({"type": "input_text", "text": str(text)})
                        continue
                    if item_type == "image_url":
                        image_url = item.get("image_url")
                        url: str | None = None
                        if isinstance(image_url, dict):
                            url = image_url.get("url")
                        elif isinstance(image_url, str):
                            url = image_url
                        if url:
                            new_content.append({"type": "input_image", "image_url": str(url)})
                        continue

                    # Preserve unknown items as-is (best effort).
                    new_content.append(dict(item))
                new_msg["content"] = new_content
            converted.append(new_msg)
        return converted

    @classmethod
    def _transcription_models_for_provider(cls, provider_id: str) -> list[str]:
        if cls._transcription_model_overrides:
            return cls._transcription_model_overrides
        if provider_id == "groq":
            return [
                "whisper-large-v3-turbo",
                "whisper-large-v3",
                "distil-whisper-large-v3-en",
                "whisper-1",
            ]
        if provider_id == "google":
            # Google AI Studio OpenAI-compatible endpoint does not provide Whisper-style transcription.
            return []
        return ["gpt-4o-mini-transcribe", "whisper-1"]

    async def generate_reply(
        self,
        *,
        provider_id: str,
        api_key: str,
        model: str | None,
        messages: list[dict[str, Any]],
        custom_base_url: str | None = None,
        enable_web_search: bool = False,
        web_search_tool_choice: str = "auto",
        temperature: float = 0.7,
    ) -> str:
        provider = PROVIDERS.get(provider_id)
        if not provider:
            raise LLMServiceError(f"Unsupported provider: {provider_id}")

        base_url = custom_base_url if provider_id == "custom" else provider.base_url
        if provider_id == "custom" and not base_url:
            raise LLMServiceError("Custom provider requires base URL")

        chosen_model = (model or "").strip() or provider.default_model

        async with self._request_semaphore:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            try:
                if (
                    enable_web_search
                    and web_search_tool_choice != "none"
                    and self._supports_openai_responses(provider_id=provider_id, base_url=base_url)
                ):
                    try:
                        response = await client.responses.create(
                            model=chosen_model,
                            input=self._to_responses_input(messages),
                            tools=[{"type": "web_search"}],
                            tool_choice=web_search_tool_choice,
                            temperature=temperature,
                        )
                        content = self._extract_content(getattr(response, "output_text", None))
                        if not content:
                            raise LLMServiceError("Provider returned empty response")
                        return content
                    except Exception as exc:  # noqa: BLE001
                        # Some models/accounts may not support web_search; fall back to plain chat completions.
                        lowered = str(exc).lower()
                        if "web_search" not in lowered and "tool" not in lowered:
                            raise

                completion = await client.chat.completions.create(
                    model=chosen_model,
                    messages=messages,
                    temperature=temperature,
                )
                choice = completion.choices[0]
                content = self._extract_content(choice.message.content)
                if not content:
                    raise LLMServiceError("Provider returned empty response")
                return content
            except Exception as exc:  # noqa: BLE001
                raise LLMServiceError(str(exc)) from exc
            finally:
                try:
                    await client.close()
                except Exception:  # noqa: BLE001
                    pass

    async def transcribe_audio(
        self,
        *,
        provider_id: str,
        api_key: str,
        audio_bytes: bytes,
        filename: str = "voice.ogg",
        mime_type: str = "audio/ogg",
        custom_base_url: str | None = None,
        language: str | None = None,
    ) -> str:
        provider = PROVIDERS.get(provider_id)
        if not provider:
            raise LLMServiceError(f"Unsupported provider: {provider_id}")
        if not audio_bytes:
            raise LLMServiceError("Audio is empty")

        base_url = custom_base_url if provider_id == "custom" else provider.base_url
        if provider_id == "custom" and not base_url:
            raise LLMServiceError("Custom provider requires base URL")

        last_error: Exception | None = None
        models = self._transcription_models_for_provider(provider_id)
        if not models:
            raise LLMServiceError("No transcription model configured")

        async with self._request_semaphore:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            try:
                for model in models:
                    try:
                        request_kwargs: dict[str, Any] = {
                            "model": model,
                            "file": (filename, audio_bytes, mime_type),
                        }
                        if language:
                            request_kwargs["language"] = language
                        response = await client.audio.transcriptions.create(**request_kwargs)
                        text = self._extract_content(getattr(response, "text", None)).strip()
                        if text:
                            return text
                    except Exception as exc:  # noqa: BLE001
                        last_error = exc

                if last_error is not None:
                    raise LLMServiceError(str(last_error))
                raise LLMServiceError("Provider returned empty transcription")
            finally:
                try:
                    await client.close()
                except Exception:  # noqa: BLE001
                    pass

    @staticmethod
    def _extract_content(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    chunks.append(text)
                elif isinstance(item, dict) and item.get("text"):
                    chunks.append(str(item["text"]))
            return "\n".join(chunks).strip()
        return str(content)
