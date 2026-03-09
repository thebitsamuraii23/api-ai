from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from bot.llm.providers import PROVIDERS


class LLMServiceError(RuntimeError):
    pass


class LLMService:
    async def generate_reply(
        self,
        *,
        provider_id: str,
        api_key: str,
        model: str | None,
        messages: list[dict[str, Any]],
        custom_base_url: str | None = None,
    ) -> str:
        provider = PROVIDERS.get(provider_id)
        if not provider:
            raise LLMServiceError(f"Unsupported provider: {provider_id}")

        base_url = custom_base_url if provider_id == "custom" else provider.base_url
        if provider_id == "custom" and not base_url:
            raise LLMServiceError("Custom provider requires base URL")

        chosen_model = (model or "").strip() or provider.default_model

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        try:
            completion = await client.chat.completions.create(
                model=chosen_model,
                messages=messages,
                temperature=0.7,
            )
            choice = completion.choices[0]
            content = self._extract_content(choice.message.content)
            if not content:
                raise LLMServiceError("Provider returned empty response")
            return content
        except Exception as exc:  # noqa: BLE001
            raise LLMServiceError(str(exc)) from exc
        finally:
            await client.close()

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
