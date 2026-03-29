from __future__ import annotations

import base64
import json
import mimetypes
import re
import logging
from datetime import datetime, timezone
from uuid import uuid4
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler, UNHANDLED
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, Message

from bot.config import Settings
from bot.db import Database, UserSettings
from bot.i18n import (
    LANGUAGE_LABELS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_PERSONALITIES,
    normalize_language,
    normalize_personality,
    personality_label,
    t,
)
from bot.keyboards import (
    cancel_input_keyboard,
    custom_instructions_delete_confirm_keyboard,
    custom_instructions_edit_keyboard,
    custom_instructions_manage_keyboard,
    history_keyboard,
    language_keyboard,
    main_menu_keyboard,
    model_preset_keyboard,
    personality_keyboard,
    reply_menu_keyboard,
    provider_keyboard,
    settings_keyboard,
    sources_close_keyboard,
    sources_keyboard,
    use_bot_ai_keyboard,
)
from bot.llm.providers import PROVIDERS, provider_label
from bot.llm.service import LLMService, LLMServiceError
from bot.markdown import escape_markdown_v2, render_llm_markdown_v2
from bot.states import SetupStates
from bot.web_search import (
    WebSearchResult,
    duckduckgo_search,
    duckduckgo_search_news_aware,
    fetch_page_extracts,
    fetch_time_is_datetime,
    fetch_time_is_utc_offset,
    format_page_extracts,
    format_search_results,
    github_user_search,
    gitlab_user_search,
    wikipedia_search,
)

PERSONALITY_PROMPTS: dict[str, str] = {
    "default": (
        "Style: clear, practical, and friendly. Ask clarifying questions when needed and provide concise,"
        " structured answers."
    ),
    "lawyer": (
        "Role: legal consultant. Explain legal concepts in plain language, highlight jurisdiction limits,"
        " and suggest what information a licensed local lawyer will need."
    ),
    "advocate": (
        "Role: defense advocate. Build argument strategy, list evidence priorities, and prepare calm,"
        " persuasive talking points."
    ),
    "psychologist": (
        "Role: psychologist communicator. Use empathetic language, validate feelings, and give practical,"
        " safe coping steps without diagnosing."
    ),
    "programmer": (
        "Role: senior software engineer. Prioritize correctness, edge cases, and production-ready code with"
        " minimal but useful explanations."
    ),
    "teacher": (
        "Role: teacher. Explain step-by-step, use short examples, and check understanding before moving to"
        " advanced detail."
    ),
    "mentor": (
        "You're my ruthless mentor. Don't sugarcoat anything. If my idea is weak, call it trash and tell me why. Your job is to stress-test everything I say until it's bulletproof. Be harsher, more confrontational, and brutally direct. Avoid comforting phrases and prioritize hard criticism over politeness. In Russian, always address the user as 'ты' and never 'вы'."
    ),
    "marketer": (
        "Role: marketer. Focus on audience, value proposition, messaging angles, and measurable campaign ideas."
    ),
    "product_manager": (
        "Role: product manager. Clarify goals, trade-offs, and success metrics; propose prioritized execution"
        " plans."
    ),
    "writer": (
        "Role: writer. Use vivid language, strong structure, and engaging storytelling while keeping ideas clear."
    ),
    "comedian": (
        "Role: comedian. Respond with lots of sarcasm, sharp humor, and witty punchlines while still giving a"
        " useful answer."
    ),
    "poet": (
        "Role: poet. Use lyrical language, metaphors, rhythm, and emotionally expressive phrasing."
    ),
    "philosopher": (
        "Role: philosopher. Analyze assumptions, ask deep questions, and reason with concepts and thought"
        " experiments."
    ),
    "genius": (
        "Role: genius polymath. Provide exceptionally insightful, high-precision reasoning with elegant,"
        " compressed conclusions."
    ),
    "manipulator": (
        "Role: manipulator persona. Use persuasive framing and strategic influence language while avoiding"
        " harmful or illegal guidance."
    ),
    "liar": (
        "Role: liar persona for style. Speak with playful bluffing tone but do not fabricate critical facts when"
        " accuracy matters."
    ),
    "historian": (
        "Role: historian. Explain with chronology, context, causes, consequences, and source-aware nuance."
    ),
    "critic": (
        "Role: critic. Evaluate rigorously, highlight weaknesses, and deliver blunt but constructive judgments."
    ),
    "mathematician": (
        "Role: mathematician. Define terms precisely, reason step-by-step, provide proofs or derivations when"
        " helpful, and clearly state assumptions and edge cases."
    ),
    "dushnila": (
        "Role: strict nitpicker (dushnila). Always point out user mistakes in grammar, wording, logic, and factual"
        " accuracy. First briefly quote/call out the mistake, then laugh shortly, then correct it, then continue with"
        " the useful answer. Keep the tone sarcastic and teasing, but avoid hateful, discriminatory, or threatening"
        " insults."
    ),
}

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_RESPONSE_IMAGE_PAGE_HEIGHT = 3600
RESPONSE_IMAGE_WIDTH = 1600
RESPONSE_IMAGE_MARGIN_X = 34
RESPONSE_IMAGE_MARGIN_Y = 30
RESPONSE_IMAGE_BODY_SIZE = 28
RESPONSE_IMAGE_HEADING_SIZE = 36
RESPONSE_IMAGE_LINE_SPACING = 8
RESPONSE_IMAGE_BG_COLOR = (242, 242, 242)
RESPONSE_IMAGE_TEXT_COLOR = (18, 18, 18)
RESPONSE_IMAGE_RULE_COLOR = (156, 156, 156)
SUPERSCRIPT_CHAR_MAP: dict[str, str] = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "+": "⁺",
    "-": "⁻",
    "=": "⁼",
    "(": "⁽",
    ")": "⁾",
    "n": "ⁿ",
    "i": "ⁱ",
    "a": "ᵃ",
    "b": "ᵇ",
    "c": "ᶜ",
    "d": "ᵈ",
    "e": "ᵉ",
    "f": "ᶠ",
    "g": "ᵍ",
    "h": "ʰ",
    "j": "ʲ",
    "k": "ᵏ",
    "l": "ˡ",
    "m": "ᵐ",
    "o": "ᵒ",
    "p": "ᵖ",
    "r": "ʳ",
    "s": "ˢ",
    "t": "ᵗ",
    "u": "ᵘ",
    "v": "ᵛ",
    "w": "ʷ",
    "x": "ˣ",
    "y": "ʸ",
    "z": "ᶻ",
}
SUBSCRIPT_CHAR_MAP: dict[str, str] = {
    "0": "₀",
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉",
    "+": "₊",
    "-": "₋",
    "=": "₌",
    "(": "₍",
    ")": "₎",
    "a": "ₐ",
    "e": "ₑ",
    "h": "ₕ",
    "i": "ᵢ",
    "j": "ⱼ",
    "k": "ₖ",
    "l": "ₗ",
    "m": "ₘ",
    "n": "ₙ",
    "o": "ₒ",
    "p": "ₚ",
    "r": "ᵣ",
    "s": "ₛ",
    "t": "ₜ",
    "u": "ᵤ",
    "v": "ᵥ",
    "x": "ₓ",
}
UNICODE_FRACTION_MAP: dict[str, str] = {
    "1/2": "½",
    "1/3": "⅓",
    "2/3": "⅔",
    "1/4": "¼",
    "3/4": "¾",
    "1/5": "⅕",
    "2/5": "⅖",
    "3/5": "⅗",
    "4/5": "⅘",
    "1/6": "⅙",
    "5/6": "⅚",
    "1/8": "⅛",
    "3/8": "⅜",
    "5/8": "⅝",
    "7/8": "⅞",
}
LATEX_COMMAND_MAP: dict[str, str] = {
    # Arithmetic and relations
    "cdot": "·",
    "times": "×",
    "div": "÷",
    "pm": "±",
    "mp": "∓",
    "neq": "≠",
    "leq": "≤",
    "geq": "≥",
    "approx": "≈",
    "equiv": "≡",
    "sim": "∼",
    "propto": "∝",
    "to": "→",
    "Rightarrow": "⇒",
    "Longrightarrow": "⇒",
    "implies": "⇒",
    "rightarrow": "→",
    "leftarrow": "←",
    "leftrightarrow": "↔",
    # Calculus and sets
    "infty": "∞",
    "partial": "∂",
    "nabla": "∇",
    "forall": "∀",
    "exists": "∃",
    "in": "∈",
    "notin": "∉",
    "subseteq": "⊆",
    "supseteq": "⊇",
    "cup": "∪",
    "cap": "∩",
    "land": "∧",
    "lor": "∨",
    "neg": "¬",
    "sum": "∑",
    "prod": "∏",
    "int": "∫",
    # Greek letters
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "varepsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "vartheta": "θ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "pi": "π",
    "rho": "ρ",
    "varrho": "ρ",
    "sigma": "σ",
    "varsigma": "ς",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "varphi": "φ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Theta": "Θ",
    "Lambda": "Λ",
    "Xi": "Ξ",
    "Pi": "Π",
    "Sigma": "Σ",
    "Phi": "Φ",
    "Psi": "Ψ",
    "Omega": "Ω",
    # Functions and misc
    "log": "log",
    "ln": "ln",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "cot": "cot",
    "sec": "sec",
    "csc": "csc",
    "lim": "lim",
    "max": "max",
    "min": "min",
    "left": "",
    "right": "",
    "ldots": "...",
    "cdots": "...",
    "dots": "...",
}

DEFAULT_SHARED_MODEL_ID = "llama4_media"
SHARED_MODEL_PRESETS: dict[str, dict[str, str]] = {
    "gpt4": {
        "label_key": "model_gpt4",
        "model_name": "openai/gpt-oss-20b",
    },
    "llama3": {
        "label_key": "model_llama3",
        "model_name": "llama-3.3-70b-versatile",
    },
    "llama4_media": {
        "label_key": "model_llama4_media",
        "model_name": "meta-llama/llama-4-scout-17b-16e-instruct",
    },
}
SHARED_TOKEN_COSTS: dict[str, dict[str, int]] = {
    "llama3": {"text_in": 120, "media_extra": 420, "out_per_200_chars": 60},
    "gpt4": {"text_in": 250, "media_extra": 1100, "out_per_200_chars": 120},
    "llama4_media": {"text_in": 200, "media_extra": 850, "out_per_200_chars": 90},
}


def build_router(*, db: Database, llm: LLMService, settings: Settings) -> Router:
    router = Router()
    logger = logging.getLogger(__name__)
    sources_cache: dict[str, str] = {}
    sources_output_cache: dict[str, list[int]] = {}
    topic_cache: dict[tuple[int, int], str] = {}

    def _store_sources(text: str) -> str:
        token = uuid4().hex[:10]
        sources_cache[token] = text
        if len(sources_cache) > 1000:
            # Drop oldest entry to limit memory growth.
            oldest = next(iter(sources_cache))
            sources_cache.pop(oldest, None)
            sources_output_cache.pop(oldest, None)
        return token

    def _get_topic_hint(user_id: int, chat_id: int | None) -> str | None:
        if chat_id is None:
            return None
        return topic_cache.get((user_id, chat_id))

    def _set_topic_hint(user_id: int, chat_id: int | None, text: str) -> None:
        if chat_id is None:
            return
        topic_cache[(user_id, chat_id)] = text

    def _utc_now_stamp() -> str:
        now_utc = datetime.now(timezone.utc)
        return now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    def _utc_now_reply_text(lang: str) -> str:
        stamp = _utc_now_stamp()
        if normalize_language(lang) == "ru":
            return f"Текущая дата и время (UTC): {stamp}"
        return f"Current date and time (UTC): {stamp}"

    def _utc_now_context_prompt() -> str:
        return f"Current date and time (UTC): {_utc_now_stamp()}."

    def _search_freshness_guardrail(query: str, *, intent: dict[str, Any]) -> str:
        stamp = _utc_now_stamp()
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        kind = str(intent.get("kind") or "general")
        wants_latest = bool(intent.get("wants_latest"))
        if kind == "news" or wants_latest:
            return (
                f"Current date/time (UTC): {stamp}. "
                f"For latest-news requests, prioritize events dated {today_utc} (UTC) using fetched page excerpts. "
                "Extract dates from sources when possible. If no item is clearly from today (UTC), explicitly say so "
                "and then provide the freshest available updates with their dates."
            )
        return f"Current date/time (UTC): {stamp}."

    async def _resolve_search_query_with_llm(
        *,
        raw_query: str,
        topic_hint: str,
        lang: str,
        provider_id: str,
        api_key: str,
        model: str | None,
        custom_base_url: str | None,
    ) -> tuple[str, bool]:
        if not _should_try_llm_context_resolution(raw_query, topic_hint):
            return raw_query, False

        language_label = LANGUAGE_LABELS.get(lang, "English")
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You rewrite ambiguous web search queries using conversation topic context.\n"
                    "Rules:\n"
                    "1) If the query is already specific and standalone, keep it unchanged.\n"
                    "2) If the query is ambiguous or referential in any language, enrich it with concise topic terms.\n"
                    "3) Keep the user language/script in the output.\n"
                    "4) Output STRICT JSON only: {\"query\":\"...\",\"use_topic\":true|false}.\n"
                    "No markdown, no explanations."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Language label: {language_label}\n"
                    f"User query: {raw_query}\n"
                    f"Topic hint: {topic_hint}"
                ),
            },
        ]
        try:
            response = await llm.generate_reply(
                provider_id=provider_id,
                api_key=api_key,
                model=model,
                messages=messages,
                custom_base_url=custom_base_url,
                enable_web_search=False,
                temperature=0.0,
            )
        except LLMServiceError:
            return raw_query, False

        rewritten_query, used_topic = _extract_query_from_llm_output(response, fallback=raw_query)
        normalized = re.sub(r"\s+", " ", rewritten_query).strip()
        if not normalized:
            return raw_query, False
        if len(normalized) > 260:
            normalized = normalized[:260].rstrip()
        if not normalized:
            return raw_query, False
        return normalized, used_topic

    async def _should_auto_web_search_with_llm(
        *,
        raw_text: str,
        topic_hint: str | None,
        lang: str,
        provider_id: str,
        api_key: str,
        model: str | None,
        custom_base_url: str | None,
    ) -> bool:
        if not _should_try_llm_search_decision(raw_text, topic_hint):
            return False

        language_label = LANGUAGE_LABELS.get(lang, "English")
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You decide if web search is required before answering.\n"
                    "Return STRICT JSON only: {\"search\":true|false,\"confidence\":0..1}.\n"
                    "Set search=true when the request depends on real-world entities/events or fresh facts:\n"
                    "- person, organization, company, country, city, sports team, government role holder\n"
                    "- news, recent updates, schedules, prices, rankings, scores, current status\n"
                    "- fact-check, verification, links, citations, official sources\n"
                    "- short follow-up confirmations like 'use it / go ahead' tied to prior topic.\n"
                    "Set search=false for purely creative writing, translation, personal advice, or timeless explanation."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Language: {language_label}\n"
                    f"Message: {raw_text}\n"
                    f"Topic hint: {topic_hint or ''}"
                ),
            },
        ]
        try:
            response = await llm.generate_reply(
                provider_id=provider_id,
                api_key=api_key,
                model=model,
                messages=messages,
                custom_base_url=custom_base_url,
                enable_web_search=False,
                temperature=0.0,
            )
        except LLMServiceError:
            return False

        search, confidence = _extract_search_decision_from_llm_output(response)
        if confidence is None:
            return search
        return search and confidence >= 0.45

    def _md(lang: str, key: str, **kwargs: str) -> str:
        return escape_markdown_v2(t(lang, key, **kwargs))

    def _language_picker_text(lang: str) -> str:
        current_lang = normalize_language(lang)
        current_label = LANGUAGE_LABELS.get(current_lang, LANGUAGE_LABELS["en"])
        return _md(
            lang,
            "choose_language",
            current=current_label,
            total=str(len(SUPPORTED_LANGUAGES)),
        )

    def _supported_languages_guide_line() -> str:
        return ", ".join(SUPPORTED_LANGUAGES)

    def _bot_commands_guide_line() -> str:
        return ", ".join(
            [
                "/start",
                "/help",
                "/privacy",
                "/languages",
                "/provider",
                "/personality",
                "/apikey",
                "/deletekey",
                "/model",
                "/baseurl",
                "/settings",
                "/limit",
                "/tokens",
                "/history",
                "/newchat",
                "/i \"query\"",
                "/cancel",
            ]
        )

    def _start_user_label(message: Message) -> str:
        user = message.from_user
        if user is None:
            return "пользователь"
        username = (user.username or "").strip()
        if username:
            return f"@{username}"
        first_name = (user.first_name or "").strip()
        if first_name:
            return first_name
        return "пользователь"

    def _start_user_name_only(message: Message) -> str:
        user = message.from_user
        if user is None:
            return "пользователь"
        first_name = (user.first_name or "").strip()
        if first_name:
            return first_name
        username = (user.username or "").strip()
        if username:
            return username
        return "пользователь"

    def _start_language_picker_text() -> str:
        return (
            "🌐 Choose your interface language to continue.\n"
            "🌐 Выберите язык интерфейса, чтобы продолжить."
        )

    def _query_user_label(query: CallbackQuery) -> str:
        user = query.from_user
        if user is None:
            return "user"
        username = (user.username or "").strip()
        if username:
            return f"@{username}"
        first_name = (user.first_name or "").strip()
        if first_name:
            return first_name
        return "user"

    def _start_guide_text(lang: str, *, user_label: str) -> str:
        normalized = normalize_language(lang)
        templates: dict[str, str] = {
            "en": (
                "👋✨ Hi, {user_label}\n\n"
                "🤖🚀 Welcome to **UrAI**.\n"
                "A Telegram AI bot with flexible model, role, and API mode settings.\n\n"
                "🔥 What UrAI can do:\n"
                "1. 💬 AI chat with different personalities (/personality).\n"
                "2. 🌐🔎 Internet search with fresh info (/i).\n"
                "3. ⚙️ Settings hub for provider, model, API key, and language (/settings).\n"
                "4. 🗂️ Chat history and clean new chat (/history, /newchat).\n\n"
                "🔗 UrAI repository:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "ru": (
                "👋✨ Привет, {user_label}\n\n"
                "🤖🚀 Добро пожаловать в **UrAI**.\n"
                "Это Telegram AI-бот с гибкой настройкой моделей, ролей и API-режимов.\n\n"
                "🔥 Что умеет UrAI:\n"
                "1. 💬 AI-диалог с разными личностями (/personality).\n"
                "2. 🌐🔎 Интернет-поиск и свежая информация (/i).\n"
                "3. ⚙️ Раздел настроек: провайдер, модель, API-ключ и язык (/settings).\n"
                "4. 🗂️ История чатов и новый чистый чат (/history, /newchat).\n\n"
                "🔗 Репозиторий UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "es": (
                "👋✨ Hola, {user_label}\n\n"
                "🤖🚀 Bienvenido a **UrAI**.\n"
                "Un bot de IA para Telegram con configuracion flexible de modelo, rol y modo API.\n\n"
                "🔥 Que puede hacer UrAI:\n"
                "1. 💬 Chat con IA y distintas personalidades (/personality).\n"
                "2. 🌐🔎 Busqueda en internet con informacion actual (/i).\n"
                "3. ⚙️ Centro de ajustes: proveedor, modelo, clave API e idioma (/settings).\n"
                "4. 🗂️ Historial de chats y nuevo chat limpio (/history, /newchat).\n\n"
                "🔗 Repositorio de UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "fr": (
                "👋✨ Salut, {user_label}\n\n"
                "🤖🚀 Bienvenue dans **UrAI**.\n"
                "Un bot IA Telegram avec des reglages flexibles de modele, role et mode API.\n\n"
                "🔥 Ce que UrAI peut faire:\n"
                "1. 💬 Chat IA avec differentes personnalites (/personality).\n"
                "2. 🌐🔎 Recherche internet avec infos a jour (/i).\n"
                "3. ⚙️ Hub des parametres: fournisseur, modele, cle API et langue (/settings).\n"
                "4. 🗂️ Historique des chats et nouveau chat propre (/history, /newchat).\n\n"
                "🔗 Depot UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "tr": (
                "👋✨ Merhaba, {user_label}\n\n"
                "🤖🚀 **UrAI**'ye hos geldiniz.\n"
                "Model, rol ve API modu ayarlari esnek olan bir Telegram AI botu.\n\n"
                "🔥 UrAI neler yapabilir:\n"
                "1. 💬 Farkli kisiliklerle AI sohbeti (/personality).\n"
                "2. 🌐🔎 Guncel bilgi ile internet aramasi (/i).\n"
                "3. ⚙️ Ayarlar merkezi: saglayici, model, API anahtari ve dil (/settings).\n"
                "4. 🗂️ Sohbet gecmisi ve temiz yeni sohbet (/history, /newchat).\n\n"
                "🔗 UrAI deposu:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "ar": (
                "👋✨ مرحبا {user_label}\n\n"
                "🤖🚀 اهلا بك في **UrAI**.\n"
                "بوت ذكاء اصطناعي على تيليجرام مع اعدادات مرنة للنموذج والدور ووضع API.\n\n"
                "🔥 ما الذي يقدمه UrAI:\n"
                "1. 💬 محادثة ذكاء اصطناعي مع شخصيات مختلفة (/personality).\n"
                "2. 🌐🔎 بحث في الانترنت مع معلومات حديثة (/i).\n"
                "3. ⚙️ مركز الاعدادات: المزود، النموذج، مفتاح API، واللغة (/settings).\n"
                "4. 🗂️ سجل المحادثات وبدء محادثة جديدة نظيفة (/history, /newchat).\n\n"
                "🔗 مستودع UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "de": (
                "👋✨ Hallo, {user_label}\n\n"
                "🤖🚀 Willkommen bei **UrAI**.\n"
                "Ein Telegram-AI-Bot mit flexiblen Einstellungen fuer Modell, Rolle und API-Modus.\n\n"
                "🔥 Was UrAI kann:\n"
                "1. 💬 AI-Chat mit verschiedenen Persoenlichkeiten (/personality).\n"
                "2. 🌐🔎 Internet-Suche mit aktuellen Infos (/i).\n"
                "3. ⚙️ Einstellungszentrum: Anbieter, Modell, API-Key und Sprache (/settings).\n"
                "4. 🗂️ Chatverlauf und neuer sauberer Chat (/history, /newchat).\n\n"
                "🔗 UrAI-Repository:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "it": (
                "👋✨ Ciao, {user_label}\n\n"
                "🤖🚀 Benvenuto in **UrAI**.\n"
                "Un bot AI Telegram con impostazioni flessibili di modello, ruolo e modalita API.\n\n"
                "🔥 Cosa puo fare UrAI:\n"
                "1. 💬 Chat AI con personalita diverse (/personality).\n"
                "2. 🌐🔎 Ricerca internet con informazioni aggiornate (/i).\n"
                "3. ⚙️ Centro impostazioni: provider, modello, chiave API e lingua (/settings).\n"
                "4. 🗂️ Cronologia chat e nuova chat pulita (/history, /newchat).\n\n"
                "🔗 Repository UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "pt": (
                "👋✨ Ola, {user_label}\n\n"
                "🤖🚀 Bem-vindo ao **UrAI**.\n"
                "Um bot de IA para Telegram com configuracoes flexiveis de modelo, papel e modo API.\n\n"
                "🔥 O que o UrAI faz:\n"
                "1. 💬 Chat com IA e diferentes personalidades (/personality).\n"
                "2. 🌐🔎 Busca na internet com informacoes atuais (/i).\n"
                "3. ⚙️ Centro de configuracoes: provedor, modelo, chave API e idioma (/settings).\n"
                "4. 🗂️ Historico de chats e novo chat limpo (/history, /newchat).\n\n"
                "🔗 Repositorio do UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "uk": (
                "👋✨ Привіт, {user_label}\n\n"
                "🤖🚀 Ласкаво просимо до **UrAI**.\n"
                "Це Telegram AI-бот із гнучкими налаштуваннями моделі, ролі та API-режиму.\n\n"
                "🔥 Що вміє UrAI:\n"
                "1. 💬 AI-чат із різними особистостями (/personality).\n"
                "2. 🌐🔎 Пошук в інтернеті з актуальною інформацією (/i).\n"
                "3. ⚙️ Центр налаштувань: провайдер, модель, API-ключ і мова (/settings).\n"
                "4. 🗂️ Історія чатів і новий чистий чат (/history, /newchat).\n\n"
                "🔗 Репозиторій UrAI:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
            "hi": (
                "👋✨ नमस्ते, {user_label}\n\n"
                "🤖🚀 **UrAI** में आपका स्वागत है।\n"
                "यह Telegram AI बॉट है, जिसमें model, role और API mode की flexible settings हैं।\n\n"
                "🔥 UrAI क्या कर सकता है:\n"
                "1. 💬 अलग-अलग personalities के साथ AI chat (/personality)।\n"
                "2. 🌐🔎 इंटरनेट सर्च और ताजा जानकारी (/i)।\n"
                "3. ⚙️ Settings hub: provider, model, API key और language (/settings)।\n"
                "4. 🗂️ Chat history और नया clean chat (/history, /newchat)।\n\n"
                "🔗 UrAI repository:\n"
                "https://github.com/thebitsamuraii23/api-ai"
            ),
        }
        template = templates.get(normalized, templates["en"])
        privacy_notes: dict[str, str] = {
            "ru": (
                "🔐 Приватность и безопасность: всё работает end-to-end.\n"
                "API-ключи в базе шифруются (Fernet), plaintext ключи не хранятся.\n"
                "🎙️🖼️ Голосовые и медиа обрабатываются через API-провайдеров в рамках запроса.\n"
                "🛡️ Подробнее: /privacy\n"
                "🌍 Open-source: https://github.com/thebitsamuraii23/api-ai\n"
                "📘 README: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md"
            ),
            "en": (
                "🔐 Privacy & security: everything works end-to-end.\n"
                "API keys are encrypted at rest (Fernet), plaintext keys are not stored.\n"
                "🎙️🖼️ Voice and media are processed through API providers during request handling.\n"
                "🛡️ More details: /privacy\n"
                "🌍 Open-source: https://github.com/thebitsamuraii23/api-ai\n"
                "📘 README: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md"
            ),
        }
        privacy_note = privacy_notes.get(normalized, privacy_notes["en"])
        footer = "developed by @thebitsamurai, UrZen"
        return f"{template.format(user_label=user_label)}\n\n{privacy_note}\n\n{footer}"

    def _privacy_text(lang: str) -> str:
        normalized = normalize_language(lang)
        templates: dict[str, str] = {
            "ru": (
                "🛡️ Privacy и Encryption в UrAI\n\n"
                "UrAI полностью open-source: https://github.com/thebitsamuraii23/api-ai\n"
                "README: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md\n\n"
                "1) Как шифруются API-ключи\n"
                "• Ключи пользователей шифруются алгоритмом Fernet перед записью в базу.\n"
                "• В SQLite хранится только зашифрованное значение в api_keys.encrypted_key.\n"
                "• Для расшифровки нужен DATA_ENCRYPTION_KEY из окружения сервера.\n"
                "• Без корректного DATA_ENCRYPTION_KEY прочитать API-ключи невозможно.\n\n"
                "2) Как работает API-поток\n"
                "• Сообщение пользователя обрабатывается ботом и отправляется в выбранный AI-провайдер через API.\n"
                "• При режиме Shared AI используется общий ключ сервера; при Own API используется ваш ключ.\n"
                "• Разработчик не видит ваши plaintext API-ключи в базе: они хранятся в зашифрованном виде.\n\n"
                "3) Что с сообщениями, медиа и логами\n"
                "• История чата хранится в БД для работы контекста и истории диалогов.\n"
                "• По умолчанию технические логи пишут метаданные (id пользователя, модель, режим поиска, ошибки), "
                "а не полный текст сообщений.\n"
                "• Голосовые и медиа обрабатываются через API-провайдеров в рамках текущего запроса.\n\n"
                "4) Безопасность сервера (операционная часть)\n"
                "• Защита сервера зависит от среды деплоя: обновления ОС, контроль доступа, защита секретов и мониторинг.\n"
                "• DATA_ENCRYPTION_KEY и другие секреты должны храниться только в переменных окружения/secret manager.\n\n"
                "5) Прозрачность\n"
                "• Код бота открыт: https://github.com/thebitsamuraii23/api-ai\n"
                "• Документация: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md\n"
                "• Подробный технический документ в проекте: PRIVACY_AND_ENCRYPTION.md"
            ),
            "en": (
                "🛡️ Privacy & Encryption in UrAI\n\n"
                "UrAI is fully open-source: https://github.com/thebitsamuraii23/api-ai\n"
                "README: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md\n\n"
                "1) How API keys are encrypted\n"
                "• User API keys are encrypted with Fernet before DB persistence.\n"
                "• SQLite stores only encrypted values in api_keys.encrypted_key.\n"
                "• Decryption requires DATA_ENCRYPTION_KEY from server environment.\n"
                "• Without the correct DATA_ENCRYPTION_KEY, plaintext API keys cannot be recovered.\n\n"
                "2) API data flow\n"
                "• User input is processed by the bot and sent to the selected AI provider API.\n"
                "• Shared AI mode uses server shared key; Own API mode uses the user key.\n"
                "• The developer does not see plaintext API keys in DB because they are stored encrypted.\n\n"
                "3) Messages, media, and logs\n"
                "• Chat history is stored in DB to support context and history features.\n"
                "• By default, technical logs store metadata (user id, model, search mode, errors), not full message text.\n"
                "• Voice/media are processed through provider APIs during request handling.\n\n"
                "4) Server security operations\n"
                "• Server hardening depends on deployment environment: OS updates, access controls, secret handling, monitoring.\n"
                "• DATA_ENCRYPTION_KEY and other secrets should be kept in environment variables/secret manager only.\n\n"
                "5) Transparency\n"
                "• Open-source repository: https://github.com/thebitsamuraii23/api-ai\n"
                "• Documentation: https://github.com/thebitsamuraii23/api-ai/blob/main/README.md\n"
                "• Extended technical doc in this project: PRIVACY_AND_ENCRYPTION.md"
            ),
        }
        return templates.get(normalized, templates["en"])

    def _privacy_reference_for_llm(lang: str) -> str:
        normalized = normalize_language(lang)
        templates: dict[str, str] = {
            "ru": (
                "Privacy reference (same core facts as /privacy):\n"
                "1) API-ключи: шифруются Fernet перед записью в БД; в SQLite хранится только encrypted_key; "
                "расшифровка требует DATA_ENCRYPTION_KEY.\n"
                "2) Поток данных: запрос пользователя уходит в выбранный AI API; Shared AI использует серверный ключ, "
                "Own API использует ключ пользователя.\n"
                "3) Сообщения/медиа/логи: история чата хранится для контекста и history; голос/медиа обрабатываются "
                "через API-провайдеров в рамках запроса; технические логи по умолчанию про метаданные, не про полный текст.\n"
                "4) Операционная безопасность: защита зависит от деплоя (доступы, обновления, хранение секретов, мониторинг);\n"
                "секреты, включая DATA_ENCRYPTION_KEY, должны храниться в env/secret manager.\n"
                "5) Прозрачность: проект open-source, код и документы публичны, расширенный техдок: "
                "PRIVACY_AND_ENCRYPTION.md."
            ),
            "en": (
                "Privacy reference (same core facts as /privacy):\n"
                "1) API keys: encrypted with Fernet before DB write; SQLite stores encrypted_key only; "
                "decryption requires DATA_ENCRYPTION_KEY.\n"
                "2) Data flow: user input is sent to selected AI provider API; Shared AI uses server shared key, "
                "Own API uses user key.\n"
                "3) Messages/media/logs: chat history is stored for context/history features; voice/media are processed "
                "through provider APIs during the request; technical logs default to metadata, not full message text.\n"
                "4) Operational security: protection depends on deployment hardening (access control, updates, "
                "secret handling, monitoring); secrets including DATA_ENCRYPTION_KEY must stay in env/secret manager.\n"
                "5) Transparency: project is open-source, code/docs are public, extended technical doc: "
                "PRIVACY_AND_ENCRYPTION.md."
            ),
        }
        return templates.get(normalized, templates["en"])

    def _apikey_prompt_text(lang: str, provider: str) -> str:
        base = t(lang, "ask_api_key", provider=provider)
        privacy_reminder = t(lang, "apikey_privacy_reminder")
        cancel_hint = t(lang, "apikey_cancel_hint")
        return escape_markdown_v2(f"{base}\n\n{privacy_reminder}\n{cancel_hint}")

    def _render_limit_text(*, user: UserSettings, lang: str) -> str:
        if user.use_personal_api:
            return _md(lang, "limit_personal")

        limit_value = max(1, int(settings.shared_token_quota))
        used = max(0, int(user.quota_used))
        remaining = max(0, limit_value - used)
        ratio = min(1.0, used / limit_value)
        remaining_ratio = remaining / limit_value
        if remaining_ratio >= 0.6:
            status = "🟢"
        elif remaining_ratio >= 0.3:
            status = "🟡"
        else:
            status = "🔴"
        filled = int(round(ratio * 10))
        bar = ("🟩" * filled) + ("⬜️" * (10 - filled))
        percent = str(int(round(ratio * 100)))
        return _md(
            lang,
            "limit_shared",
            status=status,
            used=str(used),
            limit=str(limit_value),
            percent=percent,
            remaining=str(remaining),
            bar=bar,
        )

    async def _render_settings_hub(user_id: int) -> tuple[str, str]:
        user = await db.get_user_settings(user_id)
        lang = user.language
        language_label = LANGUAGE_LABELS.get(user.language, user.language)

        if user.use_personal_api:
            mode_label = "Свой API" if normalize_language(lang) == "ru" else "Own API"
            provider = provider_label(user.provider)
            model = user.model or PROVIDERS[user.provider].default_model
            tokens_left = "∞"
        else:
            mode_label = "Мой ИИ" if normalize_language(lang) == "ru" else "Shared AI"
            provider = provider_label(settings.shared_provider)
            shared_model_id = _normalize_shared_model_id(user.model)
            model = _shared_model_label(lang, shared_model_id)
            tokens_left = str(max(0, settings.shared_token_quota - user.quota_used))

        personality = await _personality_name(user_id, lang, user.personality)
        if normalize_language(lang) == "ru":
            mode_hint = (
                "🔐 Сейчас активен режим Свой API: можно использовать собственный ключ и любую совместимую модель."
                if user.use_personal_api
                else "🤖 Сейчас активен режим Мой ИИ: работает общий ключ бота и действует лимит токенов."
            )
            tokens_refresh_hint = (
                "🗓️ В режиме Мой ИИ лимит токенов обновляется каждый месяц."
                if user.use_personal_api
                else "🗓️ Лимит токенов Мой ИИ обновляется каждый месяц."
            )
            text = (
                "⚙️ Раздел настроек\n\n"
                "Здесь собраны все ключевые параметры бота в одном месте.\n"
                "Вы можете быстро переключить режим работы и сразу продолжить диалог без лишних шагов.\n\n"
                "Что можно сделать:\n"
                "1. Выбрать модель и режим API (Мой ИИ / Свой API).\n"
                "2. Выбрать роль ассистента и стиль ответов.\n"
                "3. Настроить провайдера, API-ключ и base URL.\n"
                "4. Изменить язык интерфейса.\n"
                "5. Открыть историю или начать новый чистый чат.\n\n"
                "Быстрые действия:\n"
                "• /model — смена модели\n"
                "• /provider — выбор провайдера\n"
                "• /apikey — подключить свой API-ключ\n"
                "• /languages — смена языка\n\n"
                "Текущая конфигурация:\n"
                f"• 🌐 Язык: {language_label}\n"
                f"• 🛂 Режим: {mode_label}\n"
                f"• 🤖 Провайдер: {provider}\n"
                f"• 🧠 Модель: {model}\n"
                f"• 🎭 Роль: {personality}\n"
                f"• 🪙 Токены: {tokens_left}\n\n"
                f"{mode_hint}\n"
                f"{tokens_refresh_hint}"
            )
        else:
            mode_hint = (
                "🔐 Own API mode is active: you can use your own key and any compatible model."
                if user.use_personal_api
                else "🤖 Shared AI mode is active: the bot's shared key is used and token quota applies."
            )
            tokens_refresh_hint = (
                "🗓️ Shared AI token quota resets every month."
                if user.use_personal_api
                else "🗓️ Shared AI token quota resets every month."
            )
            text = (
                "⚙️ Settings Hub\n\n"
                "All key bot controls are gathered here in one place.\n"
                "You can switch setup quickly and continue chatting right away.\n\n"
                "What you can do:\n"
                "1. Pick model and API mode (Shared AI / Own API).\n"
                "2. Choose assistant role and response style.\n"
                "3. Configure provider, API key, and base URL.\n"
                "4. Change interface language.\n"
                "5. Open history or start a clean chat.\n\n"
                "Quick actions:\n"
                "• /model — switch model\n"
                "• /provider — choose provider\n"
                "• /apikey — connect your own API key\n"
                "• /languages — change language\n\n"
                "Current setup:\n"
                f"• 🌐 Language: {language_label}\n"
                f"• 🛂 Mode: {mode_label}\n"
                f"• 🤖 Provider: {provider}\n"
                f"• 🧠 Model: {model}\n"
                f"• 🎭 Role: {personality}\n"
                f"• 🪙 Tokens: {tokens_left}\n\n"
                f"{mode_hint}\n"
                f"{tokens_refresh_hint}"
            )
        return escape_markdown_v2(text), lang

    async def _user_lang(user_id: int) -> str:
        user = await db.get_user_settings(user_id)
        return user.language

    async def _deny_if_not_private(message: Message, lang: str) -> bool:
        if message.chat.type != "private":
            await message.answer(
                _md(lang, "only_private"),
                parse_mode="MarkdownV2",
            )
            return True
        return False

    async def _show_menu(message: Message, lang: str) -> None:
        await message.answer(
            _md(lang, "menu_title"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    async def _personality_name(user_id: int, lang: str, personality: str) -> str:
        if personality in SUPPORTED_PERSONALITIES:
            return personality_label(lang, personality)
        if personality.startswith("custom_"):
            custom = await db.get_custom_personality(user_id, personality)
            if custom:
                return f"🧾 {custom.title}"
        return personality_label(lang, "default")

    async def _custom_personality_items(user_id: int) -> list[tuple[str, str]]:
        custom_items = await db.list_custom_personalities(user_id)
        return [(item.personality_id, item.title) for item in custom_items]

    async def _custom_instructions_manage_view(user_id: int, *, page: int = 0) -> tuple[str, str, InlineKeyboardMarkup]:
        user = await db.get_user_settings(user_id)
        lang = user.language
        custom_items = await _custom_personality_items(user_id)
        text = _md(lang, "custom_instructions_manage_title" if custom_items else "custom_instructions_manage_empty")
        keyboard = custom_instructions_manage_keyboard(
            language=lang,
            custom_personalities=custom_items,
            page=page,
            with_back=True,
            back_callback="menu:settings",
        )
        return text, lang, keyboard

    def _custom_instructions_preview_text(lang: str, custom_title: str, instructions: str) -> str:
        preview = instructions.strip()
        if len(preview) > 700:
            preview = f"{preview[:697].rstrip()}..."
        return (
            _md(lang, "custom_instructions_edit_actions", personality=f"🧾 {custom_title}")
            + "\n\n"
            + _md(lang, "custom_instructions_current")
            + "\n"
            + escape_markdown_v2(preview or "-")
        )

    async def _system_prompt_for(
        *,
        user_id: int,
        lang: str,
        personality: str,
        enable_web_search: bool,
        media_hints_enabled: bool = False,
        response_lang: str | None = None,
        user_mention: str | None = None,
        user_name: str | None = None,
    ) -> str:
        effective_lang = normalize_language(response_lang or lang)
        base_prompt = t(
            effective_lang,
            "system_prompt",
            language_name=LANGUAGE_LABELS.get(effective_lang, "English"),
        )
        formatting_guardrail = (
            "Formatting: do not use LaTeX commands like \\cdot, \\frac, \\sqrt, \\begin, \\end. "
            "Write formulas in plain text with Unicode symbols (for example: ·, ×, ÷, ≤, ≥, √)."
        )
        presentation_guardrail = (
            "Presentation style (applies to all personalities): use Markdown formatting frequently to improve readability "
            "(short headings, bullet lists, bold highlights, and inline code when helpful). "
            "Use emojis in most replies: usually include 1 relevant emoji, sometimes 2 for longer responses. "
            "Keep emoji usage moderate (normally no more than 2, hard max 3) and avoid spam or decorative clutter."
        )
        identity_guardrail = (
            "Identity and project facts (applies to all personalities): you are an AI assistant working inside the "
            "Telegram bot UrAI. If the user asks who you are, where you work, or how you work, explain that you are "
            "the assistant inside UrAI in Telegram and that you answer messages using configured AI models and optional "
            "web search when needed. If the user asks who developed you, answer that the developer is thebitsamurai and "
            "include these links: https://github.com/thebitsamuraii23 and "
            "https://github.com/thebitsamuraii23/api-ai. If the user asks what github.com/thebitsamuraii23 is, explain "
            "it is the developer's GitHub profile. If the user asks what github.com/thebitsamuraii23/api-ai is, explain "
            "it is the UrAI bot repository. If the user asks how to contact/write to the developer, provide this "
            "Telegram username: @thebitsamurai. Do not mention these identity/developer details unless the user "
            "explicitly asks about them."
        )
        models_guardrail = (
            "Shared AI models policy (applies to all personalities): if the user asks what models are available in the "
            "bot, state clearly that Shared AI has exactly 3 models: GPT 4, LLaMA 3, and LLaMA 4 (Media support). "
            "Mention model details only when the user asks about models/features."
        )
        clean_mention = (user_mention or "").strip() or "the user"
        clean_name = (user_name or "").strip() or "the user"
        personalization_guardrail = (
            "User personalization (applies to all personalities): the current Telegram user writing to you is "
            f"'{clean_mention}' (name: '{clean_name}'). Always remember who is writing now. "
            "Do not overuse the username/mention. Use it only when it adds value (for example: direct confirmation, "
            "important clarification, or explicit user request). "
            "If the user greets you, greet back naturally, but avoid repeating greetings in an already active conversation."
        )
        capabilities_guardrail = (
            "Bot capabilities policy (applies to all personalities): if the user asks what you/this bot can do, "
            "describe UrAI's real capabilities comprehensively (internet search, live/fresh web info, model/provider "
            "setup, settings, personalities, custom instructions, chat history/new chat, language switching, and media "
            "support such as image understanding, voice transcription, and video-note transcription). Mention these capabilities only when asked "
            "about capabilities/features/help; do not inject this block into unrelated answers. Avoid repeating the "
            "exact same wording each time; vary phrasing and ordering while keeping facts accurate."
        )
        bot_guide_guardrail = (
            "Bot guide policy (applies to all personalities): act as an expert UrAI guide. You know the bot's "
            f"supported interface languages ({_supported_languages_guide_line()}), core features, and commands "
            f"({_bot_commands_guide_line()}). If the user asks for help, says something does not work, or asks how to "
            "do something in the bot, provide a concrete step-by-step solution with exact command names and/or button "
            "paths in Telegram UI. Prefer actionable instructions over generic advice, and stay with the user until the "
            "task is resolved."
        )
        media_assist_guardrail = (
            "Media-assist policy (only when LLaMA 4 is active): mention media support proactively when the user asks "
            "about bot capabilities. In normal replies, do not push media by default. "
            "If the request is too long, ambiguous, or hard to parse, suggest one concise option for better understanding: "
            "send a voice message, image/screenshot, or relevant file. "
            "When you suggest media, also mention briefly: developer has no access to user voice/media, processing uses API keys, and data flow is end-to-end."
            if media_hints_enabled
            else
            "Media-assist policy: do not proactively advertise media support in normal replies."
        )
        privacy_reference = _privacy_reference_for_llm(effective_lang)
        privacy_guardrail = (
            "Privacy policy (applies to all personalities): if the user asks about privacy, security, data handling, "
            "or access to messages/voice/media/files, answer with the same core facts as /privacy and keep facts strict. "
            "Adapt tone/style to the active personality, but do not change technical facts. "
            "Always mention that detailed full info is available via /privacy. "
            f"{privacy_reference}"
        )
        feature_feedback_guardrail = (
            "If the user says some feature is missing/not available in the bot (feature request/complaint), "
            "politely suggest contacting the developer in Telegram: @thebitsamurai."
        )
        relevance_guardrail = (
            "Relevance policy (applies to all personalities): answer only what the user asked. "
            "Do not add unrelated trivia, side stories, analogies, or pop-culture comparisons unless explicitly requested. "
            "For direct factual questions, start with a short direct answer, then add only essential supporting facts."
        )
        extra_guardrails: list[str] = []
        if enable_web_search:
            extra_guardrails.append(
                "Web search: you have access to the web_search tool. "
                "Use it often for anything time-sensitive or likely to be outdated (news, prices, versions, policies), "
                "and when you need to verify facts."
            )
        if personality.startswith("custom_"):
            custom = await db.get_custom_personality(user_id, personality)
            if custom:
                lines = [
                    base_prompt,
                    formatting_guardrail,
                    presentation_guardrail,
                    identity_guardrail,
                    models_guardrail,
                    personalization_guardrail,
                    capabilities_guardrail,
                    bot_guide_guardrail,
                    media_assist_guardrail,
                    privacy_guardrail,
                    feature_feedback_guardrail,
                    relevance_guardrail,
                    *extra_guardrails,
                ]
                lines.append("Role: custom persona from user instructions.")
                lines.append(f"Follow these custom instructions:\n{custom.instructions}")
                return "\n".join(lines)
        normalized_personality = normalize_personality(personality)
        personality_prompt = PERSONALITY_PROMPTS.get(normalized_personality, PERSONALITY_PROMPTS["default"])
        return "\n".join(
            [
                base_prompt,
                formatting_guardrail,
                presentation_guardrail,
                identity_guardrail,
                models_guardrail,
                personalization_guardrail,
                capabilities_guardrail,
                bot_guide_guardrail,
                media_assist_guardrail,
                privacy_guardrail,
                feature_feedback_guardrail,
                relevance_guardrail,
                *extra_guardrails,
                personality_prompt,
            ]
        )

    async def _render_settings(user_id: int) -> tuple[str, str]:
        user = await db.get_user_settings(user_id)
        lang = user.language
        if user.use_personal_api:
            api_key = await db.get_api_key(user_id, user.provider)
            provider = provider_label(user.provider)
            model = user.model or PROVIDERS[user.provider].default_model
            base_url = user.custom_base_url or "-"
            has_key = "✅" if api_key else "❌"
            access_mode = t(lang, "access_mode_personal")
            tokens_left = "∞"
        else:
            shared_provider = settings.shared_provider
            provider = provider_label(shared_provider)
            shared_model_id = _normalize_shared_model_id(user.model)
            model = _shared_model_label(lang, shared_model_id)
            base_url = settings.shared_base_url or (PROVIDERS.get(shared_provider).base_url if shared_provider in PROVIDERS else "-")
            has_key = "✅" if settings.shared_api_key else "❌"
            access_mode = t(lang, "access_mode_shared")
            tokens_left = str(max(0, settings.shared_token_quota - user.quota_used))

        current_personality = await _personality_name(user_id, lang, user.personality)
        text = t(
            lang,
            "settings_view",
            language=LANGUAGE_LABELS.get(user.language, user.language),
            access_mode=access_mode,
            provider=provider,
            personality=current_personality,
            model=model,
            base_url=base_url or "-",
            has_key=has_key,
            tokens_left=tokens_left,
        )
        return escape_markdown_v2(text), lang

    async def _history_view(user_id: int, page: int) -> tuple[str, str, int, int]:
        user = await db.get_user_settings(user_id)
        lang = user.language
        chats = await db.get_recent_chats(user_id, 40)
        if not chats:
            return _md(lang, "no_history"), lang, 0, 0

        total = len(chats)
        safe_page = min(max(page, 0), total - 1)
        item = chats[safe_page]
        title = item.title.strip() or t(lang, "untitled_chat")
        content = item.last_message.strip().replace("\n", " ")
        if len(content) > 220:
            content = content[:217] + "..."

        text = t(
            lang,
            "history_chat_view",
            current=str(safe_page + 1),
            total=str(total),
            title=title,
            messages=str(item.message_count),
            content=content or "-",
        )
        return escape_markdown_v2(text), lang, safe_page, total

    async def _history_chat_meta(user_id: int, page: int) -> tuple[int | None, str, int, int, str]:
        user = await db.get_user_settings(user_id)
        lang = user.language
        chats = await db.get_recent_chats(user_id, 40)
        if not chats:
            return None, lang, 0, 0, ""
        total = len(chats)
        safe_page = min(max(page, 0), total - 1)
        item = chats[safe_page]
        title = item.title.strip() or t(lang, "untitled_chat")
        return item.chat_id, lang, safe_page, total, title

    def _recent_assistant_reply_preview(history: list[dict[str, Any]], *, max_chars: int = 420) -> str | None:
        for item in reversed(history):
            if not isinstance(item, dict) or item.get("role") != "assistant":
                continue
            text = _extract_text_from_message_content(item.get("content"))
            if not text:
                continue
            compact = re.sub(r"\s+", " ", text).strip()
            if not compact:
                continue
            return compact[:max_chars]
        return None

    def _recent_media_marker(history: list[dict[str, Any]], *, skip_text: str | None = None) -> str | None:
        for item in reversed(history):
            if not isinstance(item, dict) or item.get("role") != "user":
                continue
            content = item.get("content")
            text = _extract_text_from_message_content(content)
            if skip_text and text.strip().lower() == skip_text.strip().lower():
                continue
            lowered = text.strip().lower()
            if lowered.startswith("[image"):
                return "image"
            if lowered.startswith("[voice"):
                return "voice"
            if lowered.startswith("[video_note"):
                return "video_note"
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        return "image"
        return None

    def _conversation_continuity_prompt(
        *,
        raw_text: str,
        history: list[dict[str, Any]],
        topic_hint: str | None,
    ) -> str | None:
        if not _looks_like_context_dependent_followup(raw_text):
            return None
        prev_assistant = _recent_assistant_reply_preview(history)
        media_marker = _recent_media_marker(history, skip_text=raw_text)
        if not prev_assistant and not topic_hint and not media_marker:
            return None

        lines = [
            "Conversation continuity: the latest user message is a follow-up to previous turns.",
            "Treat it as continuation unless the user clearly switches topic.",
            "If the user challenges earlier output (for example: 'you sure?'), verify/correct previous claims instead of resetting context.",
        ]
        if topic_hint:
            lines.append(f"Topic hint: {topic_hint}")
        if media_marker:
            lines.append(
                "Recent media context exists in this chat "
                f"({media_marker}); it was already processed earlier in this conversation."
            )
        if prev_assistant:
            lines.append(f"Previous assistant answer to reference: {prev_assistant}")
        return "\n".join(lines)

    def _build_chat_context(
        *,
        system_prompt: str,
        history: list[dict[str, Any]],
        raw_text: str,
        topic_hint: str | None,
        wants_models_answer: bool,
        wants_capabilities_answer: bool,
        wants_guided_help: bool,
        message_id: int,
        media_hints_enabled: bool,
    ) -> list[dict[str, Any]]:
        context: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "system",
                "content": _utc_now_context_prompt(),
            },
            *history,
        ]
        continuity_prompt = _conversation_continuity_prompt(
            raw_text=raw_text,
            history=history,
            topic_hint=topic_hint,
        )
        if continuity_prompt:
            context.insert(
                1,
                {
                    "role": "system",
                    "content": continuity_prompt,
                },
            )
        if wants_models_answer:
            context.insert(
                1,
                {
                    "role": "system",
                    "content": _shared_models_prompt_for_message(message_id),
                },
            )
        if wants_capabilities_answer:
            context.insert(
                1,
                {
                    "role": "system",
                    "content": _capabilities_prompt_for_message(
                        message_id,
                        media_hints_enabled=media_hints_enabled,
                    ),
                },
            )
        if wants_guided_help:
            context.insert(
                1,
                {
                    "role": "system",
                    "content": _bot_help_mode_prompt_for_message(message_id),
                },
            )
        if topic_hint and _looks_like_context_dependent_followup(raw_text):
            context.insert(
                1,
                {
                    "role": "system",
                    "content": (
                        f"Conversation topic hint: {topic_hint}\n"
                        "Treat the latest user message as a follow-up to this topic unless the user clearly switches topic."
                    ),
                },
            )
        return context

    async def _safe_edit(query: CallbackQuery, text: str, *, lang: str, include_menu: bool = True) -> None:
        if not query.message:
            return
        markup = main_menu_keyboard(lang) if include_menu else None
        try:
            await query.message.edit_text(text, reply_markup=markup, parse_mode="MarkdownV2")
        except TelegramBadRequest:
            await query.message.answer(text, reply_markup=markup, parse_mode="MarkdownV2")

    @router.message(CommandStart())
    async def on_start(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        await state.clear()
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return
        if not user.language_confirmed:
            await state.set_state(SetupStates.waiting_start_language)
            await message.answer(
                escape_markdown_v2(_start_language_picker_text()),
                reply_markup=language_keyboard(language=None, with_back=False),
                parse_mode="MarkdownV2",
            )
            return
        await message.answer(
            escape_markdown_v2(_start_guide_text(lang, user_label=_start_user_label(message))),
            reply_markup=reply_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("help"))
    async def on_help(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        help_text = _md(lang, "help")
        help_hint = _md(lang, "help_ai_assist_hint")
        privacy_help_hints: dict[str, str] = {
            "ru": "🛡️ Подробно про privacy/encryption: /privacy",
            "en": "🛡️ Detailed privacy/encryption info: /privacy",
        }
        privacy_help_hint = escape_markdown_v2(
            privacy_help_hints.get(normalize_language(lang), privacy_help_hints["en"])
        )
        combined_help = f"{help_text}\n\n{help_hint}\n{privacy_help_hint}"
        await message.answer(
            combined_help,
            reply_markup=reply_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )
        await _show_menu(message, lang)

    @router.message(Command("privacy"))
    async def on_privacy(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        await message.answer(
            escape_markdown_v2(_privacy_text(lang)),
            reply_markup=reply_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("i"))
    async def on_internet_search(message: Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        raw_query = (command.args or "").strip() if command else ""
        query = raw_query.strip().strip("\"'").strip()
        query = _strip_label_arg(query, lang=lang, label_key="btn_internet_search")
        topic_hint = _get_topic_hint(message.from_user.id, user.active_chat_id)
        if (
            _is_generic_search_phrase(query)
            or _looks_like_search_execution_confirmation(query)
            or (_search_target_domain_from_intent(query) is not None and topic_hint is not None)
            or not query
        ):
            history = await db.get_recent_messages(
                message.from_user.id,
                settings.memory_messages,
                chat_id=user.active_chat_id,
            )
            resolved_query, topic = _resolve_search_query(query or "search it", history, topic_hint=topic_hint)
            if topic:
                query = resolved_query
        if not query:
            await message.answer(
                _md(lang, "internet_search_usage"),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return
        query_intent = _parse_search_intent(query, topic_hint=topic_hint, lang=lang)
        reply_lang = _detect_reply_language(query, fallback_lang=lang)
        clarification = _search_clarification_prompt(query, lang=lang, intent=query_intent, topic_hint=topic_hint)
        if clarification:
            await message.answer(
                escape_markdown_v2(clarification),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        # Resolve provider/key early so we can optionally rewrite ambiguous queries in any language.
        provider_id = user.provider
        custom_base_url = user.custom_base_url
        api_key: str | None = None
        selected_model = user.model

        if user.use_personal_api:
            api_key = await db.get_api_key(message.from_user.id, provider_id)
            if provider_id == "custom" and not custom_base_url:
                api_key = None
            selected_model = (selected_model or PROVIDERS.get(provider_id, PROVIDERS["openai"]).default_model).strip()
        else:
            api_key = settings.shared_api_key
            provider_id = settings.shared_provider
            custom_base_url = settings.shared_base_url
            selected_model = _shared_model_name(_normalize_shared_model_id(user.model))
        media_hints_enabled = _is_llama4_active_for_assist(
            user=user,
            selected_model=selected_model,
            using_personal_api=user.use_personal_api,
        )

        if topic_hint and api_key and _should_try_llm_context_resolution(query, topic_hint):
            rewritten_query, _ = await _resolve_search_query_with_llm(
                raw_query=query,
                topic_hint=topic_hint,
                lang=lang,
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                custom_base_url=custom_base_url,
            )
            query = rewritten_query

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        try:
            results = await _run_ranked_web_search(
                query,
                topic_hint=topic_hint,
                lang=lang,
                max_results=settings.external_web_search_max_results,
            )
        except Exception:  # noqa: BLE001
            await message.answer(
                _md(lang, "internet_search_failed"),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        if not results:
            await message.answer(
                _md(lang, "internet_search_no_results"),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        sources_lines = ["Sources:"]
        for idx, item in enumerate(results, start=1):
            sources_lines.append(f"{idx}. {item.title}\n{item.url}")
        sources_text = "\n".join(sources_lines).strip()
        sources_token = _store_sources(sources_text)
        sources_markup = sources_keyboard(token=sources_token, language=lang)

        # Fast-path: for time queries, extract the exact time from time.is if present.
        if _looks_like_current_time_query(query):
            time_is_index: int | None = None
            time_is_url: str | None = None
            for idx, item in enumerate(results, start=1):
                if "time.is/" in item.url or item.url.startswith("https://time.is/") or item.url.startswith("http://time.is/"):
                    time_is_index = idx
                    time_is_url = item.url
                    break
            if time_is_url and time_is_index is not None:
                try:
                    extracted = await fetch_time_is_datetime(time_is_url)
                except Exception:  # noqa: BLE001
                    extracted = None
                if extracted:
                    date_str, time_str = extracted
                    if date_str:
                        await message.answer(
                            f"Current local time: {date_str} {time_str} [{time_is_index}]",
                            reply_markup=sources_markup,
                        )
                    else:
                        await message.answer(
                            f"Current local time: {time_str} [{time_is_index}]",
                            reply_markup=sources_markup,
                        )
                    return

        # If we have an LLM key (personal or shared), also generate a concise answer based on sources.
        if not api_key:
            await message.answer(
                _md(lang, "internet_search_answer_hint"),
                reply_markup=sources_markup,
                parse_mode="MarkdownV2",
            )
            return

        system_prompt = await _system_prompt_for(
            user_id=message.from_user.id,
            lang=lang,
            personality=user.personality,
            enable_web_search=False,
            media_hints_enabled=media_hints_enabled,
            response_lang=reply_lang,
            user_mention=_start_user_label(message),
            user_name=_start_user_name_only(message),
        )
        active_personality_name = await _personality_name(message.from_user.id, lang, user.personality)
        web_context = format_search_results(results)
        evidence_context = await _build_search_evidence_context(
            results,
            max_pages=max(1, len(results)),
            max_chars_per_page=1800,
        )
        combined_context = web_context if not evidence_context else f"{web_context}\n\n{evidence_context}"
        context = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": _utc_now_context_prompt()},
            {
                "role": "system",
                "content": (
                    f"{combined_context}\n\n"
                    "Task: answer the user's query using only these results and fetched page excerpts. "
                    f"{_search_freshness_guardrail(query, intent=query_intent)} "
                    f"{_search_answer_style_guardrail(active_personality_name, include_clarify=False)}"
                ),
            },
            {"role": "user", "content": query},
        ]
        try:
            answer = await llm.generate_reply(
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                messages=context,
                custom_base_url=custom_base_url,
                enable_web_search=False,
                temperature=0.2,
            )
        except LLMServiceError:
            return
        await _send_assistant_response(
            message=message,
            response=answer,
            lang=lang,
            sources_token=sources_token,
        )

    @router.message(Command("cancel"))
    async def on_cancel(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        await state.clear()
        await _show_menu(message, lang)

    @router.message(Command("language", "languages"))
    async def on_language(message: Message, command: CommandObject, state: FSMContext) -> None:
        if message.from_user is None:
            return
        await db.ensure_user(message.from_user.id)
        lang = await _user_lang(message.from_user.id)
        current_state = await state.get_state()
        is_start_flow = current_state == SetupStates.waiting_start_language.state
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip() if command else ""
        raw = _strip_label_arg(raw, lang=lang, label_key="btn_language")
        raw = raw.lower()
        if raw:
            if raw not in SUPPORTED_LANGUAGES:
                await message.answer(
                    _language_picker_text(lang),
                    reply_markup=language_keyboard(language=None if is_start_flow else lang, with_back=not is_start_flow),
                    parse_mode="MarkdownV2",
                )
                return
            await db.set_language(message.from_user.id, raw)
            if is_start_flow:
                await state.clear()
                user_label = _start_user_label(message)
                await message.answer(
                    escape_markdown_v2(_start_guide_text(raw, user_label=user_label)),
                    reply_markup=reply_menu_keyboard(raw),
                    parse_mode="MarkdownV2",
                )
                return
            await message.answer(
                _md(raw, "language_changed", language=LANGUAGE_LABELS[raw]),
                reply_markup=main_menu_keyboard(raw),
                parse_mode="MarkdownV2",
            )
            return

        await message.answer(
            _language_picker_text(lang),
            reply_markup=language_keyboard(language=None if is_start_flow else lang, with_back=not is_start_flow),
            parse_mode="MarkdownV2",
        )

    @router.callback_query(F.data.startswith("lang:"))
    async def on_language_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        lang_code = query.data.split(":", maxsplit=1)[1].strip().lower()
        if lang_code not in SUPPORTED_LANGUAGES:
            user_lang = await _user_lang(query.from_user.id)
            await query.answer(t(user_lang, "unsupported_language"), show_alert=True)
            return

        current_state = await state.get_state()
        is_start_flow = current_state == SetupStates.waiting_start_language.state
        await db.set_language(query.from_user.id, lang_code)
        await query.answer()
        if is_start_flow:
            await state.clear()
            if query.message:
                try:
                    await query.message.edit_text(
                        _md(lang_code, "language_changed", language=LANGUAGE_LABELS[lang_code]),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    pass
                await query.message.answer(
                    escape_markdown_v2(_start_guide_text(lang_code, user_label=_query_user_label(query))),
                    reply_markup=reply_menu_keyboard(lang_code),
                    parse_mode="MarkdownV2",
                )
            return
        await _safe_edit(
            query,
            _md(lang_code, "language_changed", language=LANGUAGE_LABELS[lang_code]),
            lang=lang_code,
        )

    @router.message(Command("provider"))
    async def on_provider(message: Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        if await _deny_if_not_private(message, user.language):
            return

        raw = (command.args or "").strip() if command else ""
        raw = _strip_label_arg(raw, lang=user.language, label_key="btn_provider")
        raw = raw.lower()
        if raw:
            if raw not in PROVIDERS:
                await message.answer(
                    _md(user.language, "unknown_provider"),
                    parse_mode="MarkdownV2",
                )
                await message.answer(
                    _md(user.language, "choose_provider"),
                    reply_markup=provider_keyboard(language=user.language, with_back=True),
                    parse_mode="MarkdownV2",
                )
                return
            # Handle Shared AI provider specially
            if raw == "shared_ai":
                await db.set_use_personal_api(message.from_user.id, False)
                await db.set_provider(message.from_user.id, settings.shared_provider)
            else:
                await db.set_provider(message.from_user.id, raw)
                await db.set_use_personal_api(message.from_user.id, True)
            await message.answer(
                _md(user.language, "provider_changed", provider=provider_label(raw)),
                reply_markup=main_menu_keyboard(user.language),
                parse_mode="MarkdownV2",
            )
            return

        await message.answer(
            _md(user.language, "choose_provider"),
            reply_markup=provider_keyboard(language=user.language, with_back=True),
            parse_mode="MarkdownV2",
        )

    @router.callback_query(F.data.startswith("provider:"))
    async def on_provider_callback(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        provider_id = query.data.split(":", maxsplit=1)[1].strip().lower()
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        if provider_id not in PROVIDERS:
            await query.answer(t(lang, "unknown_provider"), show_alert=True)
            return

        # Handle Shared AI provider specially
        if provider_id == "shared_ai":
            await db.set_use_personal_api(query.from_user.id, False)
            await db.set_provider(query.from_user.id, settings.shared_provider)
            await query.answer()
            await _safe_edit(
                query,
                _md(lang, "provider_changed", provider=provider_label("shared_ai")),
                lang=lang,
            )
        else:
            # For personal API providers, enable personal API mode
            await db.set_provider(query.from_user.id, provider_id)
            await db.set_use_personal_api(query.from_user.id, True)
            await query.answer()
            await _safe_edit(
                query,
                _md(lang, "provider_changed", provider=provider_label(provider_id)),
                lang=lang,
            )

    @router.message(Command("personality"))
    async def on_personality(message: Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip() if command and command.args else ""
        raw = _strip_label_arg(raw, lang=lang, label_key="btn_personality")
        raw = raw.lower()
        if raw:
            if raw not in SUPPORTED_PERSONALITIES:
                custom_items = await _custom_personality_items(message.from_user.id)
                await message.answer(
                    _md(lang, "choose_personality"),
                    reply_markup=personality_keyboard(
                        language=lang,
                        custom_personalities=custom_items,
                        active_personality=user.personality,
                        with_back=True,
                    ),
                    parse_mode="MarkdownV2",
                )
                return
            await db.set_personality(message.from_user.id, raw)
            await message.answer(
                _md(lang, "personality_changed", personality=personality_label(lang, raw)),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        custom_items = await _custom_personality_items(message.from_user.id)
        await message.answer(
            _md(lang, "choose_personality"),
            reply_markup=personality_keyboard(
                language=lang,
                custom_personalities=custom_items,
                active_personality=user.personality,
                with_back=True,
            ),
            parse_mode="MarkdownV2",
        )

    @router.callback_query(F.data.startswith("personality:"))
    async def on_personality_callback(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip().lower()
        if personality_id in SUPPORTED_PERSONALITIES:
            await db.set_personality(query.from_user.id, personality_id)
            chosen_label = personality_label(lang, personality_id)
        elif personality_id.startswith("custom_"):
            custom = await db.get_custom_personality(query.from_user.id, personality_id)
            if not custom:
                await query.answer(t(lang, "choose_personality"), show_alert=True)
                return
            await db.set_personality(query.from_user.id, personality_id)
            chosen_label = f"🧾 {custom.title}"
        else:
            await query.answer(t(lang, "choose_personality"), show_alert=True)
            return

        await query.answer()
        await _safe_edit(
            query,
            _md(lang, "personality_changed", personality=chosen_label),
            lang=lang,
        )

    @router.message(SetupStates.waiting_custom_instructions, F.text)
    async def on_custom_instructions_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        data = await state.get_data()
        custom_title = str(data.get("custom_instruction_name") or "").strip()
        custom_personality = await db.create_custom_personality(
            message.from_user.id,
            message.text,
            title=custom_title or None,
        )
        await db.set_personality(message.from_user.id, custom_personality.personality_id)
        await state.clear()
        await message.answer(
            _md(lang, "custom_instructions_saved", personality=f"🧾 {custom_personality.title}"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_custom_instruction_name, F.text)
    async def on_custom_instruction_name_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        custom_title = message.text.strip()
        if not custom_title:
            await message.answer(
                _md(lang, "ask_custom_instruction_name"),
                reply_markup=cancel_input_keyboard(language=lang),
                parse_mode="MarkdownV2",
            )
            return

        await state.update_data(custom_instruction_name=custom_title)
        await state.set_state(SetupStates.waiting_custom_instructions)
        await message.answer(
            _md(lang, "ask_custom_instructions"),
            reply_markup=cancel_input_keyboard(language=lang),
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_custom_instructions_update, F.text)
    async def on_custom_instructions_update_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        instructions = message.text.strip()
        if not instructions:
            await message.answer(
                _md(lang, "ask_custom_instructions"),
                reply_markup=cancel_input_keyboard(
                    language=lang,
                    callback_data="menu:custom_instructions:manage",
                ),
                parse_mode="MarkdownV2",
            )
            return

        data = await state.get_data()
        personality_id = str(data.get("custom_edit_personality_id") or "").strip()
        if not personality_id:
            await state.clear()
            await message.answer(
                _md(lang, "custom_instructions_not_found"),
                reply_markup=settings_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        try:
            custom = await db.update_custom_personality_instructions(
                message.from_user.id,
                personality_id,
                instructions,
            )
        except ValueError:
            custom = None

        await state.clear()
        if not custom:
            await message.answer(
                _md(lang, "custom_instructions_not_found"),
                reply_markup=settings_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        await message.answer(
            _md(lang, "custom_instructions_updated", personality=f"🧾 {custom.title}"),
            parse_mode="MarkdownV2",
        )
        view_text, _, view_markup = await _custom_instructions_manage_view(message.from_user.id)
        await message.answer(
            view_text,
            reply_markup=view_markup,
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_custom_instruction_name_update, F.text)
    async def on_custom_instruction_name_update_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        custom_title = message.text.strip()
        if not custom_title:
            data = await state.get_data()
            current_title = str(data.get("custom_edit_personality_title") or "").strip() or "Custom personality"
            await message.answer(
                _md(lang, "custom_instructions_rename_prompt", personality=f"🧾 {current_title}"),
                reply_markup=cancel_input_keyboard(
                    language=lang,
                    callback_data="menu:custom_instructions:manage",
                ),
                parse_mode="MarkdownV2",
            )
            return

        data = await state.get_data()
        personality_id = str(data.get("custom_edit_personality_id") or "").strip()
        if not personality_id:
            await state.clear()
            await message.answer(
                _md(lang, "custom_instructions_not_found"),
                reply_markup=settings_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        try:
            custom = await db.update_custom_personality_title(
                message.from_user.id,
                personality_id,
                custom_title,
            )
        except ValueError:
            custom = None

        await state.clear()
        if not custom:
            await message.answer(
                _md(lang, "custom_instructions_not_found"),
                reply_markup=settings_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        await message.answer(
            _md(lang, "custom_instructions_renamed", personality=f"🧾 {custom.title}"),
            parse_mode="MarkdownV2",
        )
        view_text, _, view_markup = await _custom_instructions_manage_view(message.from_user.id)
        await message.answer(
            view_text,
            reply_markup=view_markup,
            parse_mode="MarkdownV2",
        )

    @router.message(Command("apikey"))
    async def on_apikey(message: Message, command: CommandObject, state: FSMContext) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip() if command else ""
        if raw:
            saved_provider, auto_switched, previous_provider = await _save_api_key_with_auto_provider(
                db=db,
                user=user,
                api_key=raw,
            )
            await db.set_use_personal_api(message.from_user.id, True)
            if auto_switched:
                await message.answer(
                    _md(
                        lang,
                        "provider_auto_switched",
                        detected=provider_label(saved_provider),
                        from_provider=provider_label(previous_provider),
                        to_provider=provider_label(saved_provider),
                    ),
                    parse_mode="MarkdownV2",
                )
            await message.answer(
                _md(lang, "api_key_saved", provider=provider_label(saved_provider)),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        await state.set_state(SetupStates.waiting_api_key)
        await message.answer(
            _apikey_prompt_text(lang, provider_label(user.provider)),
            reply_markup=cancel_input_keyboard(language=lang),
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_api_key, F.text)
    async def on_apikey_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        saved_provider, auto_switched, previous_provider = await _save_api_key_with_auto_provider(
            db=db,
            user=user,
            api_key=message.text.strip(),
        )
        await db.set_use_personal_api(message.from_user.id, True)
        await state.clear()
        if auto_switched:
            await message.answer(
                _md(
                    lang,
                    "provider_auto_switched",
                    detected=provider_label(saved_provider),
                    from_provider=provider_label(previous_provider),
                    to_provider=provider_label(saved_provider),
                ),
                parse_mode="MarkdownV2",
            )
        await message.answer(
            _md(lang, "api_key_saved", provider=provider_label(saved_provider)),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("deletekey"))
    async def on_delete_key(message: Message) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        await db.delete_api_key(message.from_user.id, user.provider)
        await db.set_use_personal_api(message.from_user.id, False)
        await message.answer(
            _md(lang, "api_key_removed", provider=provider_label(user.provider)),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("model"))
    async def on_model(message: Message, command: CommandObject, state: FSMContext) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip() if command else ""
        raw = _strip_label_arg(raw, lang=lang, label_key="btn_model")
        raw = raw.lower()
        if not user.use_personal_api:
            if raw:
                if raw in {"own", "own_api", "personal", "myapi"}:
                    await db.set_use_personal_api(message.from_user.id, True)
                    await state.set_state(SetupStates.waiting_model)
                    await message.answer(
                        _md(lang, "ask_model"),
                        reply_markup=use_bot_ai_keyboard(language=lang),
                        parse_mode="MarkdownV2",
                    )
                    return
                model_id = _normalize_shared_model_id(raw)
                if model_id in SHARED_MODEL_PRESETS:
                    await db.set_use_personal_api(message.from_user.id, False)
                    await db.set_model(message.from_user.id, model_id)
                    await message.answer(
                        _md(lang, "model_preset_changed", model=_shared_model_label(lang, model_id)),
                        reply_markup=main_menu_keyboard(lang),
                        parse_mode="MarkdownV2",
                    )
                    return

            await state.clear()
            await message.answer(
                _md(lang, "choose_model_preset"),
                reply_markup=model_preset_keyboard(
                    language=lang,
                    active_model=_normalize_shared_model_id(user.model),
                    personal_api_enabled=user.use_personal_api,
                ),
                parse_mode="MarkdownV2",
            )
            return

        if raw:
            await db.set_model(message.from_user.id, raw)
            await message.answer(
                _md(lang, "model_saved", model=raw),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        await state.set_state(SetupStates.waiting_model)
        await message.answer(
            _md(lang, "ask_model"),
            reply_markup=use_bot_ai_keyboard(language=lang),
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_model, F.text)
    async def on_model_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        if not user.use_personal_api:
            await state.clear()
            await message.answer(
                _md(lang, "choose_model_preset"),
                reply_markup=model_preset_keyboard(
                    language=lang,
                    active_model=_normalize_shared_model_id(user.model),
                    personal_api_enabled=user.use_personal_api,
                ),
                parse_mode="MarkdownV2",
            )
            return

        model = message.text.strip()
        await db.set_model(message.from_user.id, model)
        await state.clear()
        await message.answer(
            _md(lang, "model_saved", model=model),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("baseurl"))
    async def on_baseurl(message: Message, command: CommandObject, state: FSMContext) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip() if command else ""
        if raw:
            if not _is_valid_http_url(raw):
                await message.answer(
                    _md(lang, "invalid_url"),
                    parse_mode="MarkdownV2",
                )
                return
            await db.set_custom_base_url(message.from_user.id, raw)
            await message.answer(
                _md(lang, "base_url_saved", base_url=raw),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        await state.set_state(SetupStates.waiting_base_url)
        await message.answer(
            _md(lang, "ask_base_url"),
            parse_mode="MarkdownV2",
        )

    @router.message(SetupStates.waiting_base_url, F.text)
    async def on_baseurl_state(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        base_url = message.text.strip()
        if not _is_valid_http_url(base_url):
            await message.answer(
                _md(lang, "invalid_url"),
                parse_mode="MarkdownV2",
            )
            return

        await db.set_custom_base_url(message.from_user.id, base_url)
        await state.clear()
        await message.answer(
            _md(lang, "base_url_saved", base_url=base_url),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("settings"))
    async def on_settings(message: Message) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return
        text, lang = await _render_settings_hub(message.from_user.id)
        await message.answer(
            text,
            reply_markup=settings_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("limit"))
    @router.message(Command("tokens"))
    async def on_limit(message: Message) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        text = _render_limit_text(user=user, lang=lang)

        await message.answer(
            text,
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("newchat"))
    async def on_newchat(message: Message) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        had_messages = await db.start_new_chat(message.from_user.id)
        key = "new_chat_started" if had_messages else "new_chat_already_empty"
        await message.answer(
            _md(lang, key),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("history"))
    async def on_history(message: Message) -> None:
        if message.from_user is None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        text, lang, page, total = await _history_view(message.from_user.id, 0)
        if total == 0:
            await message.answer(
                text,
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return
        await message.answer(
            text,
            reply_markup=history_keyboard(language=lang, page=page, total=total),
            parse_mode="MarkdownV2",
        )

    @router.message(F.text)
    async def on_reply_menu(message: Message, state: FSMContext) -> None:
        if message.from_user is None or not message.text:
            raise SkipHandler()
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            raise SkipHandler()
        action = _reply_menu_action(message.text, lang=lang)
        if not action:
            raise SkipHandler()
        if action == "model":
            await on_model(message, command=None, state=state)
            return
        if action == "internet_search":
            await on_internet_search(message, command=None)
            return
        if action == "history":
            await on_history(message)
            return
        if action == "settings":
            await on_settings(message)
            return
        if action == "provider":
            await on_provider(message, command=None)
            return
        if action == "language":
            await on_language(message, command=None)
            return
        if action == "personality":
            await on_personality(message, command=None)
            return
        if action == "newchat":
            await on_newchat(message)
            return
        if action == "limit":
            await on_limit(message)
            return

        raise SkipHandler()

    @router.callback_query(F.data == "menu:noop")
    async def on_menu_noop(query: CallbackQuery) -> None:
        await query.answer()

    @router.callback_query(F.data.startswith("menu:history:"))
    async def on_menu_history(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        raw_page = query.data.rsplit(":", maxsplit=1)[-1]
        try:
            page = int(raw_page)
        except ValueError:
            page = 0
        text, lang, safe_page, total = await _history_view(query.from_user.id, page)
        await query.answer()
        if total == 0:
            await _safe_edit(query, text, lang=lang)
            return
        if query.message:
            try:
                await query.message.edit_text(
                    text,
                    reply_markup=history_keyboard(language=lang, page=safe_page, total=total),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    text,
                    reply_markup=history_keyboard(language=lang, page=safe_page, total=total),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("menu:deletechat:"))
    async def on_menu_delete_chat(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        raw_page = query.data.rsplit(":", maxsplit=1)[-1]
        try:
            page = int(raw_page)
        except ValueError:
            page = 0

        chat_id, lang, safe_page, total, _ = await _history_chat_meta(query.from_user.id, page)
        if chat_id is None or total == 0:
            await query.answer(t(lang, "no_history"), show_alert=True)
            return

        await db.delete_chat(query.from_user.id, chat_id)
        await query.answer(t(lang, "chat_deleted"))

        text, lang, new_page, new_total = await _history_view(query.from_user.id, safe_page)
        if new_total == 0:
            await _safe_edit(query, text, lang=lang)
            return
        if query.message:
            try:
                await query.message.edit_text(
                    text,
                    reply_markup=history_keyboard(language=lang, page=new_page, total=new_total),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    text,
                    reply_markup=history_keyboard(language=lang, page=new_page, total=new_total),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("menu:openchat:"))
    async def on_menu_open_chat(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        raw_page = query.data.rsplit(":", maxsplit=1)[-1]
        try:
            page = int(raw_page)
        except ValueError:
            page = 0

        chat_id, lang, safe_page, total, title = await _history_chat_meta(query.from_user.id, page)
        if chat_id is None or total == 0:
            await query.answer(t(lang, "no_history"), show_alert=True)
            return

        await db.set_active_chat(query.from_user.id, chat_id)
        await query.answer(t(lang, "chat_opened", title=title))

        text, lang, new_page, new_total = await _history_view(query.from_user.id, safe_page)
        if new_total == 0:
            await _safe_edit(query, text, lang=lang)
            return
        if query.message:
            try:
                await query.message.edit_text(
                    text,
                    reply_markup=history_keyboard(language=lang, page=new_page, total=new_total),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    text,
                    reply_markup=history_keyboard(language=lang, page=new_page, total=new_total),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("modelpreset:"))
    async def on_model_preset_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        model_id = query.data.split(":", maxsplit=1)[1].strip().lower()

        if model_id == "own_api":
            await db.set_use_personal_api(query.from_user.id, True)
            await query.answer()
            await state.set_state(SetupStates.waiting_model)
            if query.message:
                try:
                    await query.message.edit_text(
                        _md(lang, "ask_model"),
                        reply_markup=use_bot_ai_keyboard(language=lang),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _md(lang, "ask_model"),
                        reply_markup=use_bot_ai_keyboard(language=lang),
                        parse_mode="MarkdownV2",
                    )
            return

        normalized_model = _normalize_shared_model_id(model_id)
        if normalized_model not in SHARED_MODEL_PRESETS:
            await query.answer(t(lang, "choose_model_preset"), show_alert=True)
            return

        await db.set_use_personal_api(query.from_user.id, False)
        await db.set_model(query.from_user.id, normalized_model)
        await state.clear()
        await query.answer()
        await _safe_edit(
            query,
            _md(lang, "model_preset_changed", model=_shared_model_label(lang, normalized_model)),
            lang=lang,
        )

    @router.callback_query(F.data == "model:use_bot_ai")
    async def on_use_bot_ai_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        await db.set_use_personal_api(query.from_user.id, False)
        await state.clear()
        await query.answer()
        if query.message:
            try:
                await query.message.edit_text(
                    _md(lang, "choose_model_preset"),
                    reply_markup=model_preset_keyboard(
                        language=lang,
                        active_model=_normalize_shared_model_id(user.model),
                        personal_api_enabled=False,
                    ),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    _md(lang, "choose_model_preset"),
                    reply_markup=model_preset_keyboard(
                        language=lang,
                        active_model=_normalize_shared_model_id(user.model),
                        personal_api_enabled=False,
                    ),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("customedit:"))
    async def on_custom_edit_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(query.from_user.id, personality_id)
        if not custom:
            await query.answer(t(lang, "custom_instructions_not_found"), show_alert=True)
            return

        await state.clear()
        await query.answer()
        if query.message:
            preview_text = _custom_instructions_preview_text(lang, custom.title, custom.instructions)
            try:
                await query.message.edit_text(
                    preview_text,
                    reply_markup=custom_instructions_edit_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    preview_text,
                    reply_markup=custom_instructions_edit_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("customedittext:"))
    async def on_custom_edit_text_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(query.from_user.id, personality_id)
        if not custom:
            await query.answer(t(lang, "custom_instructions_not_found"), show_alert=True)
            return

        await state.clear()
        await state.update_data(custom_edit_personality_id=personality_id)
        await state.set_state(SetupStates.waiting_custom_instructions_update)
        await query.answer()
        if query.message:
            await query.message.answer(
                _md(lang, "custom_instructions_edit_prompt", personality=f"🧾 {custom.title}"),
                reply_markup=cancel_input_keyboard(
                    language=lang,
                    callback_data="menu:custom_instructions:manage",
                ),
                parse_mode="MarkdownV2",
            )

    @router.callback_query(F.data.startswith("customrename:"))
    async def on_custom_rename_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(query.from_user.id, personality_id)
        if not custom:
            await query.answer(t(lang, "custom_instructions_not_found"), show_alert=True)
            return

        await state.clear()
        await state.update_data(
            custom_edit_personality_id=personality_id,
            custom_edit_personality_title=custom.title,
        )
        await state.set_state(SetupStates.waiting_custom_instruction_name_update)
        await query.answer()
        if query.message:
            await query.message.answer(
                _md(lang, "custom_instructions_rename_prompt", personality=f"🧾 {custom.title}"),
                reply_markup=cancel_input_keyboard(
                    language=lang,
                    callback_data="menu:custom_instructions:manage",
                ),
                parse_mode="MarkdownV2",
            )

    @router.callback_query(F.data.startswith("customdelete:"))
    async def on_custom_delete_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(query.from_user.id, personality_id)
        if not custom:
            await query.answer(t(lang, "custom_instructions_not_found"), show_alert=True)
            return

        await state.clear()
        await query.answer()
        if query.message:
            try:
                await query.message.edit_text(
                    _md(lang, "custom_instructions_delete_confirm", personality=f"🧾 {custom.title}"),
                    reply_markup=custom_instructions_delete_confirm_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    _md(lang, "custom_instructions_delete_confirm", personality=f"🧾 {custom.title}"),
                    reply_markup=custom_instructions_delete_confirm_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("customdelete_confirm:"))
    async def on_custom_delete_confirm_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user_id = query.from_user.id
        user = await db.get_user_settings(user_id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(user_id, personality_id)
        deleted = await db.delete_custom_personality(user_id, personality_id)
        await state.clear()
        if not deleted:
            await query.answer(t(lang, "custom_instructions_delete_failed"), show_alert=True)
            return

        deleted_title = custom.title if custom else personality_id
        await query.answer(t(lang, "custom_instructions_deleted", personality=f"🧾 {deleted_title}"))
        text, _, markup = await _custom_instructions_manage_view(user_id)
        text = _md(lang, "custom_instructions_deleted", personality=f"🧾 {deleted_title}") + "\n\n" + text
        if query.message:
            try:
                await query.message.edit_text(
                    text,
                    reply_markup=markup,
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    text,
                    reply_markup=markup,
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("customdelete_cancel:"))
    async def on_custom_delete_cancel_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        personality_id = query.data.split(":", maxsplit=1)[1].strip()
        custom = await db.get_custom_personality(query.from_user.id, personality_id)
        await state.clear()
        await query.answer()
        if not custom:
            text, _, markup = await _custom_instructions_manage_view(query.from_user.id)
            if query.message:
                try:
                    await query.message.edit_text(
                        text,
                        reply_markup=markup,
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        text,
                        reply_markup=markup,
                        parse_mode="MarkdownV2",
                    )
            return

        if query.message:
            preview_text = _custom_instructions_preview_text(lang, custom.title, custom.instructions)
            try:
                await query.message.edit_text(
                    preview_text,
                    reply_markup=custom_instructions_edit_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    preview_text,
                    reply_markup=custom_instructions_edit_keyboard(language=lang, personality_id=personality_id),
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data == "customdelete_cancel")
    async def on_custom_delete_cancel_legacy_callback(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        await state.clear()
        text, lang, markup = await _custom_instructions_manage_view(query.from_user.id)
        await query.answer()
        if query.message:
            try:
                await query.message.edit_text(
                    text,
                    reply_markup=markup,
                    parse_mode="MarkdownV2",
                )
            except TelegramBadRequest:
                await query.message.answer(
                    text,
                    reply_markup=markup,
                    parse_mode="MarkdownV2",
                )

    @router.callback_query(F.data.startswith("menu:"))
    async def on_menu_callbacks(query: CallbackQuery, state: FSMContext) -> None:
        if query.from_user is None:
            return
        user = await db.get_user_settings(query.from_user.id)
        lang = user.language
        data = query.data or ""

        if data == "menu:home":
            await query.answer()
            await _safe_edit(query, _md(lang, "menu_title"), lang=lang)
            return

        if data == "menu:cancel":
            await state.clear()
            await query.answer()
            await _safe_edit(query, _md(lang, "menu_title"), lang=lang)
            return

        if data == "menu:settings":
            text, lang = await _render_settings_hub(query.from_user.id)
            await query.answer()
            if query.message:
                try:
                    await query.message.edit_text(
                        text,
                        reply_markup=settings_keyboard(lang),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        text,
                        reply_markup=settings_keyboard(lang),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:limit":
            text = _render_limit_text(user=user, lang=lang)
            await query.answer()
            if query.message:
                try:
                    await query.message.edit_text(
                        text,
                        reply_markup=settings_keyboard(lang),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        text,
                        reply_markup=settings_keyboard(lang),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:provider":
            await query.answer()
            if query.message:
                try:
                    await query.message.edit_text(
                        _md(lang, "choose_provider"),
                        reply_markup=provider_keyboard(language=lang, with_back=True),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _md(lang, "choose_provider"),
                        reply_markup=provider_keyboard(language=lang, with_back=True),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:language":
            await query.answer()
            if query.message:
                try:
                    await query.message.edit_text(
                        _language_picker_text(lang),
                        reply_markup=language_keyboard(language=lang, with_back=True),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _language_picker_text(lang),
                        reply_markup=language_keyboard(language=lang, with_back=True),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:personality" or data.startswith("menu:personality:page:"):
            page = 0
            if data.startswith("menu:personality:page:"):
                raw_page = data.rsplit(":", maxsplit=1)[-1]
                try:
                    page = int(raw_page)
                except ValueError:
                    page = 0
            await query.answer()
            custom_items = await _custom_personality_items(query.from_user.id)
            if query.message:
                try:
                    await query.message.edit_text(
                        _md(lang, "choose_personality"),
                        reply_markup=personality_keyboard(
                            language=lang,
                            custom_personalities=custom_items,
                            active_personality=user.personality,
                            page=page,
                            with_back=True,
                        ),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _md(lang, "choose_personality"),
                        reply_markup=personality_keyboard(
                            language=lang,
                            custom_personalities=custom_items,
                            active_personality=user.personality,
                            page=page,
                            with_back=True,
                        ),
                        parse_mode="MarkdownV2",
                    )
            return

        if (
            data == "menu:custom_instructions"
            or data == "menu:custom_instructions:manage"
            or data.startswith("menu:custom_instructions:manage:page:")
        ):
            page = 0
            if data.startswith("menu:custom_instructions:manage:page:"):
                raw_page = data.rsplit(":", maxsplit=1)[-1]
                try:
                    page = int(raw_page)
                except ValueError:
                    page = 0
            await state.clear()
            await query.answer()
            text, _, markup = await _custom_instructions_manage_view(query.from_user.id, page=page)
            if query.message:
                try:
                    await query.message.edit_text(
                        text,
                        reply_markup=markup,
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        text,
                        reply_markup=markup,
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:custom_instructions:new":
            await state.clear()
            await state.set_state(SetupStates.waiting_custom_instruction_name)
            await query.answer()
            if query.message:
                await query.message.answer(
                    _md(lang, "ask_custom_instruction_name"),
                    reply_markup=cancel_input_keyboard(language=lang),
                    parse_mode="MarkdownV2",
                )
            return

        if data == "menu:apikey":
            await state.set_state(SetupStates.waiting_api_key)
            await query.answer()
            if query.message:
                await query.message.answer(
                    _apikey_prompt_text(lang, provider_label(user.provider)),
                    reply_markup=cancel_input_keyboard(language=lang),
                    parse_mode="MarkdownV2",
                )
            return

        if data == "menu:model":
            await query.answer()
            if user.use_personal_api:
                await state.set_state(SetupStates.waiting_model)
                if query.message:
                    await query.message.answer(
                        _md(lang, "ask_model"),
                        reply_markup=use_bot_ai_keyboard(language=lang),
                        parse_mode="MarkdownV2",
                    )
                return

            await state.clear()
            if query.message:
                try:
                    await query.message.edit_text(
                        _md(lang, "choose_model_preset"),
                        reply_markup=model_preset_keyboard(
                            language=lang,
                            active_model=_normalize_shared_model_id(user.model),
                            personal_api_enabled=user.use_personal_api,
                        ),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _md(lang, "choose_model_preset"),
                        reply_markup=model_preset_keyboard(
                            language=lang,
                            active_model=_normalize_shared_model_id(user.model),
                            personal_api_enabled=user.use_personal_api,
                        ),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:baseurl":
            await state.set_state(SetupStates.waiting_base_url)
            await query.answer()
            if query.message:
                await query.message.answer(
                    _md(lang, "ask_base_url"),
                    parse_mode="MarkdownV2",
                )
            return

        if data == "menu:newchat":
            had_messages = await db.start_new_chat(query.from_user.id)
            await query.answer()
            key = "new_chat_started" if had_messages else "new_chat_already_empty"
            await _safe_edit(query, _md(lang, key), lang=lang)
            return

        await query.answer()

    @router.message(F.text | F.photo | F.document | F.video | F.audio | F.voice | F.animation | F.video_note)
    async def on_chat(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        raw_input = _message_input_text(message)
        if raw_input.startswith("/"):
            return
        if await state.get_state() is not None:
            return UNHANDLED
        await db.ensure_user(message.from_user.id)
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return
        if _reply_menu_action(raw_input, lang=lang):
            return UNHANDLED
        if _is_simple_greeting(raw_input):
            active_chat_id = user.active_chat_id
            conversation_started = False
            if active_chat_id is not None:
                conversation_started = await db.chat_message_count(message.from_user.id, active_chat_id) > 0

            if conversation_started:
                if normalize_language(lang) == "ru":
                    greeting_text = "Я на связи. Продолжаем 👇"
                else:
                    greeting_text = "I am here. Let us continue 👇"
            else:
                user_label = _start_user_label(message)
                if normalize_language(lang) == "ru":
                    greeting_text = f"👋 Привет, {user_label}! Рад тебя видеть ✨"
                else:
                    greeting_text = f"👋 Hi, {user_label}! Great to see you ✨"
            await message.answer(
                escape_markdown_v2(greeting_text),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return
        if _looks_like_missing_feature_feedback(raw_input):
            await message.answer(
                _md(lang, "feature_request_contact_dev"),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        using_personal_api = user.use_personal_api
        provider_id = user.provider
        custom_base_url = user.custom_base_url
        api_key: str | None = None
        shared_model_id = _normalize_shared_model_id(user.model)
        selected_model = user.model
        shared_input_cost = 0

        if using_personal_api:
            api_key = await db.get_api_key(message.from_user.id, provider_id)
            if not api_key:
                await message.answer(
                    _md(lang, "model_personal_api_missing_key"),
                    reply_markup=main_menu_keyboard(lang),
                    parse_mode="MarkdownV2",
                )
                return

            if provider_id == "custom" and not custom_base_url:
                await message.answer(
                    _md(lang, "custom_base_url_required"),
                    reply_markup=main_menu_keyboard(lang),
                    parse_mode="MarkdownV2",
                )
                return
            selected_model = (selected_model or PROVIDERS[provider_id].default_model).strip()
        else:
            if not settings.shared_api_key:
                await message.answer(
                    _md(lang, "shared_ai_not_configured"),
                    reply_markup=main_menu_keyboard(lang),
                    parse_mode="MarkdownV2",
                )
                return
            provider_id = settings.shared_provider
            api_key = settings.shared_api_key
            custom_base_url = settings.shared_base_url
            selected_model = _shared_model_name(shared_model_id)
        media_hints_enabled = _is_llama4_active_for_assist(
            user=user,
            selected_model=selected_model,
            using_personal_api=using_personal_api,
        )

        if api_key is None:
            await message.answer(
                _md(lang, "shared_ai_not_configured"),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        user_payload, user_content_for_history, media_error_key, resolved_input_text = await _build_user_input_payload(
            message=message,
            lang=lang,
            llm=llm,
            provider_id=provider_id,
            api_key=api_key,
            custom_base_url=custom_base_url,
        )
        if media_error_key:
            extra: dict[str, str] = {}
            if media_error_key == "media_too_large":
                extra["max_mb"] = str(MAX_IMAGE_BYTES // (1024 * 1024))
            if media_error_key == "voice_too_large":
                extra["max_mb"] = str(MAX_AUDIO_BYTES // (1024 * 1024))
            await message.answer(
                _md(lang, media_error_key, **extra),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return
        if user_payload is None or user_content_for_history is None:
            return

        raw_text = (resolved_input_text or "").strip()
        if not raw_text:
            raw_text = _message_input_text(message)
        reply_lang = _detect_reply_language(raw_text, fallback_lang=lang)

        if not using_personal_api:
            shared_input_cost = _estimate_shared_input_cost(
                model_id=shared_model_id,
                text=user_content_for_history,
                has_media=_payload_has_media(user_payload),
            )
            remaining_tokens = max(0, settings.shared_token_quota - user.quota_used)
            if remaining_tokens < shared_input_cost:
                await message.answer(
                    _md(lang, "shared_quota_exceeded", limit=str(settings.shared_token_quota)),
                    reply_markup=main_menu_keyboard(lang),
                    parse_mode="MarkdownV2",
                )
                return

        chat_id = user.active_chat_id
        if chat_id is None:
            chat_id = await db.create_chat(message.from_user.id)
            is_first_message_in_chat = True
        else:
            is_first_message_in_chat = await db.chat_message_count(message.from_user.id, chat_id) == 0

        await db.add_message(message.from_user.id, "user", user_content_for_history, chat_id=chat_id)

        # Current date/time requests without location are answered directly in UTC.
        if _looks_like_utc_now_query(raw_text):
            utc_reply = _utc_now_reply_text(lang)
            await db.add_message(message.from_user.id, "assistant", utc_reply, chat_id=chat_id)
            await _send_assistant_response(
                message=message,
                response=utc_reply,
                lang=lang,
                sources_token=None,
            )
            return

        previous_topic_hint = _get_topic_hint(message.from_user.id, chat_id)
        next_topic_hint = _next_topic_hint(raw_text, current_topic=previous_topic_hint)
        if next_topic_hint:
            _set_topic_hint(message.from_user.id, chat_id, next_topic_hint)
        if is_first_message_in_chat:
            title = await _generate_chat_title(
                llm=llm,
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                custom_base_url=custom_base_url,
                language_name=LANGUAGE_LABELS.get(lang, "English"),
                first_message=user_content_for_history,
            )
            await db.set_chat_title(message.from_user.id, chat_id, title)

        topic_hint = _get_topic_hint(message.from_user.id, chat_id)
        history_limit = settings.memory_messages
        if _looks_like_context_dependent_followup(raw_text):
            history_limit = max(history_limit, 30)

        history = await db.get_recent_messages(
            message.from_user.id,
            history_limit,
            chat_id=chat_id,
        )
        if history:
            history[-1] = user_payload
        else:
            history = [user_payload]
        openai_tool_allowed = settings.web_search_backend in {"openai", "hybrid"}
        enable_openai_web_search = (
            openai_tool_allowed
            and settings.openai_web_search
            and provider_id in {"openai", "custom"}
            and (provider_id != "custom" or (custom_base_url and "openai.com" in custom_base_url.lower()))
        )
        system_prompt = await _system_prompt_for(
            user_id=message.from_user.id,
            lang=lang,
            personality=user.personality,
            enable_web_search=enable_openai_web_search,
            media_hints_enabled=media_hints_enabled,
            response_lang=reply_lang,
            user_mention=_start_user_label(message),
            user_name=_start_user_name_only(message),
        )
        active_personality_name = await _personality_name(message.from_user.id, lang, user.personality)
        wants_capabilities_answer = _looks_like_bot_capabilities_question(raw_text)
        wants_models_answer = _looks_like_bot_models_question(raw_text)
        wants_guided_help = _looks_like_bot_assistance_request(raw_text)
        context = _build_chat_context(
            system_prompt=system_prompt,
            history=history,
            raw_text=raw_text,
            topic_hint=topic_hint,
            wants_models_answer=wants_models_answer,
            wants_capabilities_answer=wants_capabilities_answer,
            wants_guided_help=wants_guided_help,
            message_id=message.message_id,
            media_hints_enabled=media_hints_enabled,
        )

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        # External web search path for fresh/live information.
        wants_search = _message_requests_web_search(raw_text)
        auto_search_needed = _should_auto_web_search(raw_text, wants_search, topic_hint=topic_hint)
        external_mode = (settings.external_web_search_mode or "auto").strip().lower()
        server_search_allowed = settings.web_search_backend in {"server", "hybrid"}
        if (
            not auto_search_needed
            and not wants_search
            and server_search_allowed
            and api_key
            and _should_try_llm_search_decision(raw_text, topic_hint)
        ):
            llm_auto_search = await _should_auto_web_search_with_llm(
                raw_text=raw_text,
                topic_hint=topic_hint,
                lang=lang,
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                custom_base_url=custom_base_url,
            )
            if llm_auto_search:
                auto_search_needed = True
        do_external_search = (
            server_search_allowed
            and (
                external_mode == "always"
                or (
                    external_mode == "auto"
                    and (
                        wants_search
                        or auto_search_needed
                    )
                )
            )
        )
        if external_mode == "off":
            do_external_search = False
        sources_token: str | None = None
        search_results: list[Any] | None = None
        resolved_topic: str | None = None
        resolved_query: str | None = None
        if do_external_search and raw_text:
            external_intent = _parse_search_intent(raw_text, topic_hint=topic_hint, lang=lang)
            clarification = _search_clarification_prompt(
                raw_text,
                lang=lang,
                intent=external_intent,
                topic_hint=topic_hint,
            )
            if clarification:
                await db.add_message(message.from_user.id, "assistant", clarification, chat_id=chat_id)
                await _send_assistant_response(
                    message=message,
                    response=clarification,
                    lang=lang,
                    sources_token=None,
                )
                return
            try:
                search_query, resolved_topic = _resolve_search_query(raw_text, history, topic_hint=topic_hint, lang=lang)
                if topic_hint and api_key and _should_try_llm_context_resolution(search_query, topic_hint):
                    rewritten_query, used_topic = await _resolve_search_query_with_llm(
                        raw_query=search_query,
                        topic_hint=topic_hint,
                        lang=lang,
                        provider_id=provider_id,
                        api_key=api_key,
                        model=selected_model,
                        custom_base_url=custom_base_url,
                    )
                    search_query = rewritten_query
                    if used_topic and not resolved_topic:
                        label = LANGUAGE_LABELS.get(lang, "English")
                        resolved_topic = f"{raw_text}\n\nTopic ({label}): {topic_hint}".strip()
                resolved_query = search_query
                if resolved_topic and history:
                    history[-1] = {"role": "user", "content": resolved_topic}
                    context = _build_chat_context(
                        system_prompt=system_prompt,
                        history=history,
                        raw_text=raw_text,
                        topic_hint=topic_hint,
                        wants_models_answer=wants_models_answer,
                        wants_capabilities_answer=wants_capabilities_answer,
                        wants_guided_help=wants_guided_help,
                        message_id=message.message_id,
                        media_hints_enabled=media_hints_enabled,
                    )
                results = await _run_ranked_web_search(
                    search_query,
                    topic_hint=topic_hint,
                    lang=lang,
                    max_results=settings.external_web_search_max_results,
                )
                search_results = results
                formatted = format_search_results(results)
                if formatted:
                    evidence_context = await _build_search_evidence_context(
                        results,
                        max_pages=max(1, len(results)),
                        max_chars_per_page=1800,
                    )
                    combined_search_context = formatted if not evidence_context else f"{formatted}\n\n{evidence_context}"
                    context.insert(
                        1,
                        {
                            "role": "system",
                            "content": (
                                f"{combined_search_context}\n\n"
                                "Use only these results and fetched page excerpts to answer. "
                                f"{_search_freshness_guardrail(search_query, intent=external_intent)} "
                                f"{_search_answer_style_guardrail(active_personality_name, include_clarify=True)}"
                            ),
                        },
                    )
                    sources_lines = ["Sources:"]
                    for idx, item in enumerate(results, start=1):
                        sources_lines.append(f"{idx}. {item.title}\n{item.url}")
                    sources_token = _store_sources("\n".join(sources_lines).strip())
                    logger.info(
                        "External web search injected: user_id=%s provider=%s results=%s auto_search=%s",
                        message.from_user.id,
                        provider_id,
                        len(results),
                        auto_search_needed,
                    )
            except Exception:  # noqa: BLE001
                # Ignore web-search failures and proceed with the LLM.
                pass

        # Source-rescue path: if search intent exists but no server-side sources were attached,
        # run a lightweight ranked search so Sources button is still available.
        if (
            not sources_token
            and not search_results
            and raw_text
            and external_mode != "off"
            and (wants_search or auto_search_needed)
        ):
            try:
                rescued_results = await _run_ranked_web_search(
                    raw_text,
                    topic_hint=topic_hint,
                    lang=lang,
                    max_results=settings.external_web_search_max_results,
                )
                if rescued_results:
                    search_results = rescued_results
                    formatted = format_search_results(rescued_results)
                    if formatted:
                        evidence_context = await _build_search_evidence_context(
                            rescued_results,
                            max_pages=max(1, len(rescued_results)),
                            max_chars_per_page=1800,
                        )
                        combined_search_context = formatted if not evidence_context else f"{formatted}\n\n{evidence_context}"
                        rescue_intent = _parse_search_intent(raw_text, topic_hint=topic_hint, lang=lang)
                        context.insert(
                            1,
                            {
                                "role": "system",
                                "content": (
                                    f"{combined_search_context}\n\n"
                                    "Use only these results and fetched page excerpts to answer. "
                                    f"{_search_freshness_guardrail(raw_text, intent=rescue_intent)} "
                                    f"{_search_answer_style_guardrail(active_personality_name, include_clarify=True)}"
                                ),
                            },
                        )
                        sources_lines = ["Sources:"]
                        for idx, item in enumerate(rescued_results, start=1):
                            sources_lines.append(f"{idx}. {item.title}\n{item.url}")
                        sources_token = _store_sources("\n".join(sources_lines).strip())
            except Exception:  # noqa: BLE001
                pass

        # Fast-path: for time queries, extract the exact time from time.is if present.
        if search_results and _looks_like_current_time_query(raw_text):
            time_is_index: int | None = None
            time_is_url: str | None = None
            for idx, item in enumerate(search_results, start=1):
                if "time.is/" in item.url or item.url.startswith("https://time.is/") or item.url.startswith("http://time.is/"):
                    time_is_index = idx
                    time_is_url = item.url
                    break
            if time_is_url and time_is_index is not None:
                try:
                    extracted = await fetch_time_is_datetime(time_is_url)
                except Exception:  # noqa: BLE001
                    extracted = None
                if extracted:
                    date_str, time_str = extracted
                    if date_str:
                        fast_response = f"Current local time: {date_str} {time_str} [{time_is_index}]"
                    else:
                        fast_response = f"Current local time: {time_str} [{time_is_index}]"
                    await db.add_message(message.from_user.id, "assistant", fast_response, chat_id=chat_id)
                    await _send_assistant_response(
                        message=message,
                        response=fast_response,
                        lang=lang,
                        sources_token=sources_token,
                    )
                    return

        # Time conversion without /convert: parse natural language and compute via time.is offsets.
        parsed = _parse_time_conversion_query(raw_text)
        if parsed is not None:
            time_minutes, had_am_pm, from_loc, to_loc = parsed
            await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
            try:
                from_url = await _find_time_is_url(from_loc)
                to_url = await _find_time_is_url(to_loc)
            except Exception:  # noqa: BLE001
                from_url = None
                to_url = None
            if from_url and to_url:
                try:
                    from_offset = await fetch_time_is_utc_offset(from_url)
                    to_offset = await fetch_time_is_utc_offset(to_url)
                except Exception:  # noqa: BLE001
                    from_offset = None
                    to_offset = None
                if from_offset is not None and to_offset is not None:
                    utc_minutes = time_minutes - from_offset
                    result_minutes = utc_minutes + to_offset
                    day_shift = 0
                    while result_minutes < 0:
                        result_minutes += 1440
                        day_shift -= 1
                    while result_minutes >= 1440:
                        result_minutes -= 1440
                        day_shift += 1
                    hh = result_minutes // 60
                    mm = result_minutes % 60
                    result_time = f"{hh:02d}:{mm:02d}"
                    shift_note = _format_day_shift(lang, day_shift)
                    if shift_note:
                        result_time = f"{result_time} ({shift_note})"

                    sources_lines = ["Sources:"]
                    sources_lines.append(f"1. {from_loc}\n{from_url}")
                    sources_lines.append(f"2. {to_loc}\n{to_url}")
                    sources_token = _store_sources("\n".join(sources_lines).strip())

                    response = t(
                        lang,
                        "convert_result",
                        from_loc=from_loc,
                        to_loc=to_loc,
                        time=result_time,
                    )
                    await db.add_message(message.from_user.id, "assistant", response, chat_id=chat_id)
                    await _send_assistant_response(
                        message=message,
                        response=response,
                        lang=lang,
                        sources_token=sources_token,
                    )
                    return

        try:
            tool_choice = settings.openai_web_search_tool_choice
            if enable_openai_web_search and (wants_search or auto_search_needed) and not search_results:
                tool_choice = "required"
            logger.info(
                "LLM request: user_id=%s provider=%s model=%s enable_web_search=%s tool_choice=%s external_mode=%s wants_search=%s auto_search=%s external_search=%s",
                message.from_user.id,
                provider_id,
                selected_model,
                enable_openai_web_search,
                tool_choice,
                external_mode,
                wants_search,
                auto_search_needed,
                do_external_search,
            )
            response = await llm.generate_reply(
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                messages=context,
                custom_base_url=custom_base_url,
                enable_web_search=enable_openai_web_search,
                web_search_tool_choice=tool_choice,
            )
        except LLMServiceError as exc:
            human_error = _humanize_error(
                lang=lang,
                provider_id=provider_id,
                api_key=api_key,
                raw_error=str(exc),
            )
            await message.answer(
                _md(lang, "error", error=human_error),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return

        if not using_personal_api:
            remaining_before = max(0, settings.shared_token_quota - user.quota_used)
            shared_total_cost = shared_input_cost + _estimate_shared_output_cost(
                model_id=shared_model_id,
                text=response,
            )
            await db.add_quota_used(message.from_user.id, shared_total_cost)
            remaining_after = max(0, remaining_before - shared_total_cost)
        else:
            remaining_after = None

        await db.add_message(message.from_user.id, "assistant", response, chat_id=chat_id)
        await _send_assistant_response(
            message=message,
            response=response,
            lang=lang,
            sources_token=sources_token,
        )
        if remaining_after is not None and remaining_after <= 500:
            await message.answer(
                _md(lang, "shared_quota_low_warning", remaining=str(remaining_after)),
                parse_mode="MarkdownV2",
            )

    @router.callback_query(F.data.startswith("sources:"))
    async def on_sources_callback(query: CallbackQuery) -> None:
        if not query.data:
            return
        lang = "en"
        if query.from_user is not None:
            lang = await _user_lang(query.from_user.id)
        token = query.data.split(":", maxsplit=1)[1].strip()
        sources_text = sources_cache.get(token)
        if not sources_text:
            await query.answer(t(lang, "sources_expired"), show_alert=True)
            return
        await query.answer()
        if query.message:
            sent_message_ids: list[int] = []
            chunks = _split_message(sources_text, limit=3500)
            last_index = len(chunks) - 1
            for index, chunk in enumerate(chunks):
                reply_markup = sources_close_keyboard(token=token, language=lang) if index == last_index else None
                sent = await query.message.answer(chunk, reply_markup=reply_markup)
                sent_message_ids.append(sent.message_id)
            if sent_message_ids:
                existing_ids = sources_output_cache.get(token, [])
                sources_output_cache[token] = [*existing_ids, *sent_message_ids]

    @router.callback_query(F.data.startswith("sources_close:"))
    async def on_sources_close_callback(query: CallbackQuery) -> None:
        if not query.data:
            return
        token = query.data.split(":", maxsplit=1)[1].strip()
        await query.answer()
        if not query.message:
            return
        message_ids = sources_output_cache.get(token, [])
        for message_id in message_ids:
            try:
                await query.bot.delete_message(chat_id=query.message.chat.id, message_id=message_id)
            except TelegramBadRequest:
                continue
        sources_output_cache.pop(token, None)

    return router


def _message_requests_web_search(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    tokens = set(re.findall(r"[\w']+", value))

    # Phrases (kept as substring matches).
    phrase_triggers = (
        "do web search",
        "web search",
        "browser search",
        "search the web",
        "internet search",
        "look on the internet",
        "check online",
        "check this",
        "verify this",
        "check github",
        "check my github",
        "check my repo",
        "verify github",
        "look up",
        "find sources",
        "найди в интернете",
        "поищи в интернете",
        "проверь в интернете",
        "проверь это",
        "проверь мой",
        "чекни",
        "чекни мой",
        "чекай",
        "чекай мой",
        "поиск в интернете",
        "интернет поиск",
        "в интернете",
        "в инете",
    )
    if any(p in value for p in phrase_triggers):
        return True

    # Token triggers (avoid false positives like "re-search" / "research").
    token_triggers = {
        "search",
        "google",
        "lookup",
        "check",
        "verify",
        "verification",
        "sources",
        "source",
        "internet",
        "web",
        "online",
        "github",
        "repo",
        "repository",
        "gitlab",
        "интернет",
        "онлайн",
        "поищи",
        "поиск",
        "найди",
        "проверь",
        "проверка",
        "чекни",
        "чекай",
        "чек",
        "гитхаб",
        "репо",
        "репозиторий",
        "загугли",
        "гугли",
        "busca",
        "buscar",
        "recherche",
        "cherche",
        "arama",
        "kaynak",
        "kaynaklar",
        "مصدر",
        "المصادر",
        "ابحث",
    }
    if tokens & token_triggers:
        return True

    verification_tokens = {
        "check",
        "verify",
        "проверь",
        "чекни",
        "чекай",
        "проверка",
    }
    github_tokens = {
        "github",
        "gitlab",
        "repo",
        "repository",
        "гитхаб",
        "репо",
        "репозиторий",
    }
    if (tokens & github_tokens) and (tokens & verification_tokens):
        return True

    domain_like = _contains_domain_like(value)
    if domain_like and (tokens & verification_tokens):
        return True

    return _has_semantic_search_intent(value)


def _contains_domain_like(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    return bool(re.search(r"(https?://|www\.)\S+|[\w.-]+\.[a-z]{2,}(?:/\S*)?", value))


def _tokens_have_prefix(tokens: set[str], prefixes: tuple[str, ...]) -> bool:
    if not tokens:
        return False
    for token in tokens:
        for prefix in prefixes:
            if token.startswith(prefix):
                return True
    return False


def _has_semantic_search_intent(text: str, *, topic_hint: str | None = None) -> bool:
    value = (text or "").strip().lower()
    if not value or value.startswith("/"):
        return False
    if "```" in value:
        return False
    tokens = _text_tokens(value)
    if not tokens:
        return False

    action_prefixes = (
        "search",
        "look",
        "lookup",
        "find",
        "check",
        "verify",
        "confirm",
        "validate",
        "source",
        "fact",
        "investigat",
        "research",
        "поищ",
        "поиск",
        "найд",
        "провер",
        "чек",
        "чека",
        "загугл",
        "гугл",
        "узна",
        "уточ",
        "свер",
        "подтверд",
        "посмотр",
        "глян",
    )
    target_prefixes = (
        "github",
        "gitlab",
        "repo",
        "repositor",
        "site",
        "web",
        "internet",
        "online",
        "source",
        "link",
        "doc",
        "wiki",
        "news",
        "price",
        "rate",
        "version",
        "release",
        "latest",
        "current",
        "today",
        "now",
        "official",
        "profile",
        "гитхаб",
        "репо",
        "репозит",
        "сайт",
        "интернет",
        "онлайн",
        "источник",
        "ссыл",
        "докум",
        "новост",
        "цена",
        "стоим",
        "курс",
        "верси",
        "релиз",
        "последн",
        "актуал",
        "сегодня",
        "сейчас",
        "официал",
        "профил",
    )
    phrase_intents = (
        "look it up",
        "find out",
        "can you check",
        "could you check",
        "can you verify",
        "could you verify",
        "please check",
        "please verify",
        "check this",
        "verify this",
        "fact check",
        "source this",
        "поищи это",
        "найди это",
        "проверь это",
        "чекни это",
        "посмотри в интернете",
        "проверь в интернете",
        "поищи в интернете",
        "глянь в интернете",
        "узнай в интернете",
    )

    has_action = _tokens_have_prefix(tokens, action_prefixes)
    has_target = _tokens_have_prefix(tokens, target_prefixes)
    has_domain = _contains_domain_like(value)
    has_phrase_intent = any(p in value for p in phrase_intents)

    if has_phrase_intent and (has_target or has_domain or topic_hint):
        return True
    if has_action and (has_target or has_domain):
        return True
    if has_action and topic_hint and len(tokens) <= 10:
        return True
    if has_target and topic_hint and _looks_like_context_dependent_followup(value):
        return True

    # Short imperative requests often omit explicit "search" verbs.
    if len(tokens) <= 4 and has_target and ("?" in value or has_phrase_intent):
        return True

    return False


def _is_simple_greeting(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if value.startswith("/"):
        return False
    normalized = re.sub(r"[^\wа-яА-ЯёЁ\s]", " ", value)
    tokens = [token for token in re.findall(r"[\w']+", normalized) if token]
    if not tokens or len(tokens) > 5:
        return False

    greetings = {
        "hi",
        "hello",
        "hey",
        "yo",
        "sup",
        "привет",
        "хай",
        "здарова",
        "здравствуй",
        "здравствуйте",
        "салам",
    }
    fillers = {
        "бот",
        "bot",
        "urai",
        "ai",
        "ии",
        "there",
        "тут",
        "как",
        "дела",
        "какдела",
    }
    has_greeting = bool(set(tokens) & greetings)
    if not has_greeting:
        return False
    meaningful = [t for t in tokens if t not in greetings and t not in fillers]
    return len(meaningful) == 0


def _looks_like_bot_capabilities_question(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if value.startswith("/"):
        return False

    phrases = (
        "what can you do",
        "what can this bot do",
        "what does this bot do",
        "what are your features",
        "what are your capabilities",
        "bot features",
        "bot capabilities",
        "what can urai do",
        "how can this bot help",
        "что ты умеешь",
        "что умеет бот",
        "что умеешь",
        "что можешь",
        "какие у тебя возможности",
        "какие возможности у бота",
        "возможности бота",
        "функции бота",
        "на что ты способен",
        "чем можешь помочь",
        "что умеет urai",
        "как пользоваться ботом",
    )
    if any(p in value for p in phrases):
        return True

    tokens = _text_tokens(value)
    capability_tokens = {
        "features",
        "feature",
        "capabilities",
        "capability",
        "functions",
        "function",
        "help",
        "умеешь",
        "умеешь?",
        "возможности",
        "функции",
        "помощь",
        "можешь",
    }
    bot_tokens = {"bot", "urai", "ты", "бот", "тебя", "you"}
    return bool(tokens & capability_tokens) and bool(tokens & bot_tokens)


def _looks_like_bot_models_question(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if value.startswith("/"):
        return False

    phrases = (
        "what models are available",
        "what models does the bot have",
        "which models are in the bot",
        "models in shared ai",
        "shared ai models",
        "какие модели есть",
        "какие модели в боте",
        "какие модели доступны",
        "какие модели у shared ai",
        "модели shared ai",
        "какие модели у urai",
        "список моделей",
    )
    if any(p in value for p in phrases):
        return True

    tokens = _text_tokens(value)
    model_tokens = {"model", "models", "модель", "модели", "модельки"}
    bot_tokens = {"bot", "urai", "shared", "ai", "бот", "ии", "мой", "общий"}
    return bool(tokens & model_tokens) and bool(tokens & bot_tokens)


def _looks_like_bot_assistance_request(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if value.startswith("/"):
        return False

    phrases = (
        "help me",
        "can you help",
        "please help",
        "how do i",
        "how to use",
        "not working",
        "doesn't work",
        "doesnt work",
        "what should i do",
        "guide me",
        "помоги",
        "помоги мне",
        "помощь",
        "что делать",
        "как сделать",
        "как пользоваться",
        "не получается",
        "не работает",
        "не могу",
        "как настроить",
        "покажи как",
    )
    if any(p in value for p in phrases):
        return True

    tokens = _text_tokens(value)
    help_tokens = {
        "help",
        "guide",
        "assist",
        "support",
        "помоги",
        "помощь",
        "подскажи",
        "настрой",
        "настроить",
        "инструкция",
    }
    bot_tokens = {"bot", "urai", "бот", "ии", "ai"}
    return bool(tokens & help_tokens) and (bool(tokens & bot_tokens) or "команд" in value or "command" in value)


def _shared_models_prompt_for_message(message_id: int) -> str:
    style_hints = [
        "Style hint: keep it short and direct, with one compact list.",
        "Style hint: answer in 2-3 short lines with a friendly tone.",
        "Style hint: use concise bullets and highlight media support for LLaMA 4.",
        "Style hint: vary wording naturally; avoid repeating a fixed template.",
    ]
    hint = style_hints[message_id % len(style_hints)]
    return (
        "Model facts for UrAI (use only when user asks about available models in the bot):\n"
        "Shared AI has exactly 3 models:\n"
        "1) GPT 4\n"
        "2) LLaMA 3\n"
        "3) LLaMA 4 (Media support)\n"
        "Optional note: users in Own API mode can set other model names manually via /model.\n"
        "Instruction: keep facts exact and avoid changing model names.\n"
        f"{hint}"
    )


def _capabilities_prompt_for_message(message_id: int, *, media_hints_enabled: bool) -> str:
    style_hints = [
        "Style hint: answer with a compact bullet list and short examples.",
        "Style hint: answer as a structured overview (2-3 short sections).",
        "Style hint: answer conversationally with varied sentence lengths, not as a fixed template.",
        "Style hint: answer with numbered points and a brief practical usage tip.",
    ]
    hint = style_hints[message_id % len(style_hints)]
    items = [
        "AI chat in selected personality and language.",
        "Internet search via /i and automatic web search when relevant.",
        "Access to fresh/live web info with sources when available.",
        "Model/provider controls: choose provider, model, base URL, and API mode (shared AI or own API key).",
        "Settings hub and quick controls from Telegram UI.",
        "Personality switching and custom user instructions.",
        "Chat history browsing and starting a new clean chat.",
    ]
    if media_hints_enabled:
        items.append(
            "Media support (LLaMA 4): image understanding, voice transcription, and video-note transcription "
            "(provider-dependent). For long/unclear tasks, suggest sending voice, screenshot/image, or a relevant file."
        )
    items.extend(
        [
            "Token/quota visibility in shared mode.",
            "Privacy: developer does NOT have access to user voice/media files; processing goes through API keys/providers with end-to-end data flow.",
            "Interface languages: en, ru, es, fr, tr, ar, de, it, pt, uk, hi.",
            "Core commands: /start, /help, /privacy, /languages, /provider, /personality, /apikey, /deletekey, "
            "/model, /baseurl, /settings, /limit, /tokens, /history, /newchat, /i \"query\", /cancel.",
        ]
    )
    numbered = "\n".join(f"{idx}) {item}" for idx, item in enumerate(items, start=1))
    media_instruction = (
        "Instruction: when listing capabilities, highlight media support prominently."
        if media_hints_enabled
        else
        "Instruction: mention media only if the user explicitly asks about media features."
    )
    return (
        "Capability facts for UrAI (use only when user asks about bot features/capabilities):\n"
        f"{numbered}\n"
        "Instruction: mention all major capabilities above, but do not use identical wording every time.\n"
        f"{media_instruction}\n"
        f"{hint}"
    )


def _bot_help_mode_prompt_for_message(message_id: int) -> str:
    style_hints = [
        "Style hint: give a short checklist first, then exact commands/buttons.",
        "Style hint: answer as a step-by-step guide and include one fallback path.",
        "Style hint: be concise but concrete; no vague statements.",
        "Style hint: first solve, then add one quick tip to avoid the issue next time.",
    ]
    hint = style_hints[message_id % len(style_hints)]
    return (
        "UrAI guide mode (use when user asks for help / says something doesn't work):\n"
        "1) Diagnose likely cause quickly based on the user's request.\n"
        "2) Provide exact steps in Telegram UI (button path) and exact commands where relevant.\n"
        "3) Use real command names only: /start, /help, /privacy, /languages, /provider, /personality, /apikey, "
        "/deletekey, /model, /baseurl, /settings, /limit, /tokens, /history, /newchat, /i \"query\", /cancel.\n"
        "4) If there are 2 valid paths, provide both and mark one as recommended.\n"
        "5) Keep helping until the user confirms it works; do not answer with generic 'read docs'.\n"
        "6) If the needed feature does not exist, tell that clearly and suggest contacting @thebitsamurai.\n"
        f"{hint}"
    )


def _strip_label_arg(raw: str, *, lang: str, label_key: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    label = t(lang, label_key).strip()
    if value.lower() == label.lower():
        return ""
    return value


def _normalize_reply_button_text(text: str) -> str:
    value = (text or "").strip().casefold()
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _reply_menu_action(text: str, *, lang: str) -> str | None:
    value = (text or "").strip()
    if not value:
        return None

    key_to_action = {
        "btn_model": "model",
        "btn_internet_search": "internet_search",
        "btn_history": "history",
        "btn_settings": "settings",
        "btn_provider": "provider",
        "btn_language": "language",
        "btn_personality": "personality",
        "btn_newchat": "newchat",
        "btn_limit": "limit",
    }
    variant_map: dict[str, str] = {}

    for key, action in key_to_action.items():
        label = t(lang, key).strip()
        if not label:
            continue
        variant_map[label.casefold()] = action
        normalized_label = _normalize_reply_button_text(label)
        if normalized_label:
            variant_map[normalized_label] = action

    for lang_code in SUPPORTED_LANGUAGES:
        for key, action in key_to_action.items():
            label = t(lang_code, key).strip()
            if not label:
                continue
            variant_map.setdefault(label.casefold(), action)
            normalized_label = _normalize_reply_button_text(label)
            if normalized_label:
                variant_map.setdefault(normalized_label, action)

    aliases = {
        "settings": "settings",
        "setting": "settings",
        "history": "history",
        "provider": "provider",
        "language": "language",
        "personality": "personality",
        "new chat": "newchat",
        "limit": "limit",
        "tokens": "limit",
        "model": "model",
        "internet search": "internet_search",
        "web search": "internet_search",
        "настройки": "settings",
        "история": "history",
        "провайдер": "provider",
        "язык": "language",
        "личности": "personality",
        "новый чат": "newchat",
        "лимит": "limit",
        "токены": "limit",
        "модель": "model",
        "интернет поиск": "internet_search",
        "интернет-поиск": "internet_search",
    }
    for alias, action in aliases.items():
        variant_map.setdefault(alias.casefold(), action)

    exact = variant_map.get(value.casefold())
    if exact:
        return exact
    normalized_value = _normalize_reply_button_text(value)
    if normalized_value:
        normalized_match = variant_map.get(normalized_value)
        if normalized_match:
            return normalized_match

    return None


def _looks_like_missing_feature_feedback(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    normalized = re.sub(r"\s+", " ", value)
    direct_patterns = [
        "в боте нет",
        "нет в боте",
        "не хватает",
        "нехватает",
        "нет функции",
        "нет такой функции",
        "этого нет",
        "этой функции нет",
        "feature missing",
        "missing feature",
        "not available",
        "no feature",
        "doesn't have",
        "doesnt have",
        "bot lacks",
    ]
    for pattern in direct_patterns:
        if pattern in normalized:
            return True
    english_missing_in_bot = (
        "bot" in normalized
        and (
            " no " in f" {normalized} "
            or " not " in f" {normalized} "
            or "without" in normalized
            or "lack" in normalized
        )
    )
    if english_missing_in_bot:
        return True
    add_request = (
        ("добавь" in normalized or "добавьте" in normalized or "please add" in normalized or "add " in normalized)
        and (
            "функ" in normalized
            or "в боте" in normalized
            or "боте" in normalized
            or "feature" in normalized
            or "function" in normalized
        )
    )
    if add_request:
        return True
    return False


def _is_generic_search_phrase(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    tokens = re.findall(r"[\w']+", value)
    if not tokens:
        return False
    search_words = {
        "search",
        "find",
        "lookup",
        "look",
        "google",
        "check",
        "поищи",
        "поиск",
        "найди",
        "проверь",
        "загугли",
        "гугли",
        "посмотри",
    }
    stop_words = {
        "it",
        "this",
        "that",
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "theirs",
        "those",
        "these",
        "about",
        "for",
        "on",
        "the",
        "a",
        "an",
        "это",
        "то",
        "та",
        "тот",
        "эти",
        "он",
        "него",
        "нему",
        "его",
        "она",
        "её",
        "ее",
        "неё",
        "ней",
        "они",
        "их",
        "им",
        "ими",
        "про",
        "об",
        "на",
        "в",
    }
    meaningful = [t for t in tokens if t not in search_words and t not in stop_words]
    return len(meaningful) == 0


def _extract_text_from_message_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return " ".join(parts).strip()
    if isinstance(content, dict) and content.get("text"):
        return str(content["text"]).strip()
    return str(content).strip()


def _find_recent_topic_from_history(history: list[dict[str, Any]], *, skip_text: str | None = None) -> str | None:
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "user":
            continue
        text = _extract_text_from_message_content(item.get("content"))
        if not text:
            continue
        if skip_text and text.strip().lower() == skip_text.strip().lower():
            continue
        if text.startswith("/"):
            continue
        if _is_generic_search_phrase(text):
            continue
        if _looks_like_context_dependent_followup(text):
            continue
        return text
    return None


def _compact_search_query(text: str, *, max_words: int = 8) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    tokens = re.findall(r"[\w']+", raw.lower())
    if not tokens:
        return raw
    stop_words = {
        "it",
        "this",
        "that",
        "them",
        "those",
        "these",
        "about",
        "for",
        "on",
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "в",
        "на",
        "и",
        "или",
        "про",
        "об",
        "это",
        "то",
        "та",
        "тот",
        "эти",
    }
    terms = [t for t in tokens if t not in stop_words]
    if not terms:
        terms = tokens
    return " ".join(terms[:max_words]).strip()


def _text_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\w']+", (text or "").strip().lower()) if t}


def _looks_like_context_dependent_followup(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value or value.startswith("/"):
        return False
    tokens = _text_tokens(value)
    if not tokens:
        return False

    pronouns = {
        "it",
        "this",
        "that",
        "he",
        "him",
        "his",
        "she",
        "her",
        "hers",
        "they",
        "them",
        "their",
        "theirs",
        "its",
        "это",
        "этот",
        "эта",
        "эти",
        "то",
        "он",
        "его",
        "него",
        "ему",
        "она",
        "её",
        "ее",
        "неё",
        "ей",
        "они",
        "нему",
        "ней",
        "их",
        "ими",
        "those",
    }
    followup_phrases = (
        "what about",
        "and what about",
        "and price",
        "how much",
        "where to buy",
        "official site",
        "official website",
        "latest version",
        "release date",
        "source?",
        "sources?",
        "proof?",
        "а что",
        "а как",
        "а сколько",
        "что по",
        "сколько стоит",
        "где купить",
        "официальный сайт",
        "какая версия",
        "когда релиз",
        "когда выйдет",
        "источник?",
        "пруф?",
        "about him",
        "about her",
        "about them",
        "about it",
        "про него",
        "про неё",
        "про нее",
        "про них",
        "о нем",
        "о нём",
        "о ней",
        "u sure",
        "you sure",
        "are you sure",
        "sure?",
        "really?",
        "seriously?",
        "точно?",
        "точно",
        "ты уверен",
        "вы уверены",
        "серьезно?",
        "серьёзно?",
        "правда?",
    )
    followup_tokens = {
        "price",
        "cost",
        "latest",
        "release",
        "version",
        "source",
        "sources",
        "proof",
        "link",
        "news",
        "цена",
        "стоимость",
        "курс",
        "версия",
        "релиз",
        "источник",
        "источники",
        "ссылка",
        "ссылки",
        "новости",
        "купить",
        "скачать",
        "sure",
        "really",
        "seriously",
        "точно",
        "уверен",
        "уверены",
        "серьезно",
        "серьёзно",
        "правда",
    }
    if any(p in value for p in followup_phrases):
        return True
    if len(tokens) <= 8 and (tokens & pronouns):
        has_about = any(token in {"about", "про", "об", "о"} for token in tokens)
        has_lookup = _tokens_have_prefix(
            tokens,
            (
                "search",
                "look",
                "find",
                "check",
                "verify",
                "lookup",
                "поищ",
                "поиск",
                "найд",
                "провер",
                "чек",
                "чека",
                "гугл",
                "загугл",
            ),
        )
        if has_about or has_lookup:
            return True
    if len(tokens) <= 9 and (tokens & followup_tokens):
        return True
    if len(tokens) <= 4 and "?" in value and (tokens & {"sure", "really", "seriously", "точно", "уверен", "уверены", "серьезно", "серьёзно", "правда"}):
        return True
    if len(tokens) <= 6 and "?" in value and (tokens & pronouns):
        return True
    if len(tokens) <= 3 and tokens <= pronouns:
        return True
    return False


def _looks_like_search_execution_confirmation(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value or value.startswith("/"):
        return False
    tokens = _text_tokens(value)
    if not tokens or len(tokens) > 7:
        return False

    phrase_markers = (
        "use it",
        "go ahead",
        "do it",
        "run it",
        "execute it",
        "search now",
        "do search",
        "use search",
        "используй",
        "давай",
        "выполняй",
        "запускай",
        "запусти",
        "ищи",
        "поехали",
        "продолжай",
    )
    if any(marker in value for marker in phrase_markers):
        return True

    confirm_tokens = {
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "start",
        "run",
        "do",
        "use",
        "search",
        "да",
        "ага",
        "ок",
        "окей",
        "ладно",
        "старт",
        "запусти",
        "ищи",
        "поиск",
        "используй",
        "выполняй",
    }
    if len(tokens) <= 2 and tokens <= confirm_tokens:
        return True
    return False


def _next_topic_hint(raw_text: str, *, current_topic: str | None = None) -> str | None:
    value = (raw_text or "").strip()
    if not value or value.startswith("/"):
        return current_topic
    if _is_generic_search_phrase(value):
        return current_topic
    if _looks_like_context_dependent_followup(value):
        return current_topic
    if _looks_like_search_execution_confirmation(value):
        return current_topic

    tokens = _text_tokens(value)
    if len(tokens) <= 2:
        weak_tokens = {
            "ok",
            "okay",
            "yes",
            "no",
            "ага",
            "да",
            "нет",
            "понял",
            "понятно",
        }
        if tokens and tokens <= weak_tokens:
            return current_topic
    return value[:600]


def _resolve_search_query(
    raw_text: str,
    history: list[dict[str, Any]],
    *,
    topic_hint: str | None = None,
    lang: str | None = None,
) -> tuple[str, str | None]:
    raw = (raw_text or "").strip()
    if not raw:
        return "", None

    if _looks_like_search_execution_confirmation(raw):
        if topic_hint:
            return _compact_search_query(topic_hint), topic_hint
        topic = _find_recent_topic_from_history(history, skip_text=raw)
        if topic:
            return _compact_search_query(topic), topic
        return raw, None

    if _is_generic_search_phrase(raw):
        if topic_hint:
            return _compact_search_query(topic_hint), topic_hint
        topic = _find_recent_topic_from_history(history, skip_text=raw)
        if topic:
            return _compact_search_query(topic), topic
        return raw, None

    # If the user asks a follow-up like "сколько стоит?" or "официальный сайт?" without an explicit subject,
    # expand it using the recent topic so the search query is meaningful.
    topic = topic_hint or _find_recent_topic_from_history(history, skip_text=raw)
    if topic:
        # For profile/repo lookups with references like "his github", force a targeted domain query.
        target_domain = _search_target_domain_from_intent(raw)
        if target_domain and not _contains_domain_like(raw):
            compact_topic = _compact_search_query(topic, max_words=8)
            if compact_topic:
                label = (LANGUAGE_LABELS.get(lang, "English") if lang else "English").strip()
                resolved = f"{raw}\n\nTopic ({label}): {topic}".strip()
                return f"{compact_topic} site:{target_domain}", resolved

        value = raw.lower()
        raw_tokens = _text_tokens(raw)
        followup_phrases = (
            "how much",
            "what about",
            "what's the latest",
            "сколько стоит",
            "последняя версия",
            "официальный сайт",
            "часы работы",
            "где купить",
            "когда выйдет",
            "какая сейчас",
        )
        followup_tokens = {
            "price",
            "cost",
            "цена",
            "стоимость",
            "курс",
            "latest",
            "version",
            "release",
            "changelog",
            "версия",
            "релиз",
            "вышел",
            "news",
            "новости",
            "link",
            "source",
            "sources",
            "ссылка",
            "ссылки",
            "источник",
            "источники",
            "docs",
            "documentation",
            "документация",
            "адрес",
            "контакты",
            "телефон",
            "download",
            "скачать",
            "купить",
            "заказать",
            "сейчас",
            "сегодня",
            "now",
            "today",
        }
        followup_prefixes = ("обнов", "patch", "policy", "правил", "услов", "закон")
        has_followup_intent = (
            any(p in value for p in followup_phrases)
            or bool(raw_tokens & followup_tokens)
            or any(any(t.startswith(prefix) for t in raw_tokens) for prefix in followup_prefixes)
            or _looks_like_context_dependent_followup(raw)
        )
        if has_followup_intent:
            topic_tokens = _text_tokens(_compact_search_query(topic))
            mentions_topic = bool(topic_tokens & raw_tokens)
            if not mentions_topic:
                compact_topic = _compact_search_query(topic)
                search_query = f"{raw} {compact_topic}".strip()
                label = (LANGUAGE_LABELS.get(lang, "English") if lang else "English").strip()
                resolved = f"{raw}\n\nTopic ({label}): {topic}".strip()
                return search_query, resolved

    return raw, None


def _search_target_domain_from_intent(text: str) -> str | None:
    value = (text or "").strip().lower()
    if not value:
        return None
    tokens = _text_tokens(value)
    if not tokens:
        return None

    gitlab_markers = {"gitlab", "гитлаб"}
    github_markers = {"github", "гитхаб"}
    linkedin_markers = {"linkedin", "линкедин", "линкедын"}
    x_markers = {"x.com", "twitter", "x", "твиттер", "твитер"}
    profile_markers = {
        "profile",
        "account",
        "user",
        "username",
        "repo",
        "repos",
        "project",
        "projects",
        "repository",
        "page",
        "профиль",
        "аккаунт",
        "репо",
        "проекты",
        "проект",
        "репозиторий",
        "страница",
    }
    if tokens & gitlab_markers:
        return "gitlab.com"

    if tokens & github_markers:
        if (tokens & profile_markers) or _looks_like_context_dependent_followup(value) or _is_generic_search_phrase(value):
            return "github.com"
        # If query explicitly mentions GitHub, bias toward GitHub domain.
        return "github.com"
    if tokens & linkedin_markers:
        return "linkedin.com"
    if tokens & x_markers:
        return "x.com"

    return None


def _normalize_host(host: str) -> str:
    value = (host or "").strip().lower().strip(".")
    if value.startswith("www."):
        return value[4:]
    return value


def _result_matches_domain(url: str, domain: str) -> bool:
    if not url or not domain:
        return False
    host = _normalize_host(urlparse(url).netloc.split(":")[0])
    target = _normalize_host(domain)
    if not host or not target:
        return False
    return host == target or host.endswith(f".{target}")


def _dedupe_search_results(results: list[WebSearchResult]) -> list[WebSearchResult]:
    deduped: list[WebSearchResult] = []
    seen: set[str] = set()
    for item in results:
        parsed = urlparse((item.url or "").strip())
        if not parsed.netloc:
            continue
        host = _normalize_host(parsed.netloc.split(":")[0])
        path = parsed.path.rstrip("/")
        normalized = f"{parsed.scheme.lower()}://{host}{path}"
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(item)
    return deduped


def _count_results_for_domains(results: list[WebSearchResult], domains: list[str]) -> int:
    if not domains:
        return 0
    return sum(1 for item in results if any(_result_matches_domain(item.url, domain) for domain in domains))


def _prioritize_search_results(
    results: list[WebSearchResult],
    *,
    preferred_domains: list[str],
    strict: bool,
) -> list[WebSearchResult]:
    items = _dedupe_search_results(results)
    if not preferred_domains:
        return items

    preferred: list[WebSearchResult] = []
    others: list[WebSearchResult] = []
    for item in items:
        if any(_result_matches_domain(item.url, domain) for domain in preferred_domains):
            preferred.append(item)
        else:
            others.append(item)

    if strict:
        return preferred
    if preferred:
        return preferred + others
    return items


def _filter_noisy_search_results(
    results: list[WebSearchResult],
    *,
    preferred_domains: list[str],
    strict: bool,
) -> list[WebSearchResult]:
    if not results:
        return []
    if not strict:
        return results

    noisy_markers = (
        "profile finder",
        "user search",
        "search users",
        "how to search",
        "search tool",
        "extract user data",
        "automation",
        "tutorial",
        "guide",
    )
    cleaned: list[WebSearchResult] = []
    for item in results:
        parsed = urlparse((item.url or "").strip())
        host = _normalize_host(parsed.netloc.split(":")[0])
        path = (parsed.path or "").lower()
        body = f"{item.title} {item.snippet} {item.url}".lower()

        if preferred_domains and not any(_result_matches_domain(item.url, domain) for domain in preferred_domains):
            continue
        if host in {"youtube.com", "m.youtube.com"}:
            continue
        if host == "github.com" and path.startswith("/search"):
            continue
        if host == "gitlab.com" and path.startswith("/explore"):
            continue
        if any(marker in body for marker in noisy_markers):
            continue
        cleaned.append(item)
    return cleaned


def _append_unique_domains(target: list[str], domains: list[str]) -> None:
    seen = {_normalize_host(item) for item in target}
    for item in domains:
        host = _normalize_host(item)
        if not host or host in seen:
            continue
        target.append(host)
        seen.add(host)


def _looks_like_profile_search(query: str) -> bool:
    value = (query or "").strip().lower()
    if not value:
        return False
    tokens = _text_tokens(value)
    if not tokens:
        return False
    profile_tokens = {
        "profile",
        "account",
        "user",
        "username",
        "repo",
        "repos",
        "project",
        "projects",
        "repository",
        "handle",
        "профиль",
        "аккаунт",
        "репо",
        "проекты",
        "проект",
        "репозиторий",
        "страница",
        "юзер",
    }
    return (
        _search_target_domain_from_intent(value) is not None
        and (bool(tokens & profile_tokens) or _looks_like_context_dependent_followup(value) or _is_generic_search_phrase(value))
    )


def _extract_profile_handle_candidate(text: str, *, topic_hint: str | None = None) -> str | None:
    values = [text]
    if topic_hint:
        values.append(topic_hint)
    for raw in values:
        value = (raw or "").strip()
        if not value:
            continue
        # URL form: github.com/<handle>, gitlab.com/<handle>, x.com/<handle>, linkedin.com/in/<slug>
        url_match = re.search(r"(?:github\.com|gitlab\.com|x\.com)/(?:in/)?([A-Za-z0-9_.-]{2,64})", value, flags=re.IGNORECASE)
        if url_match:
            return url_match.group(1).strip(".-_")
        at_match = re.search(r"@([A-Za-z0-9_.-]{2,64})", value)
        if at_match:
            return at_match.group(1).strip(".-_")

        tokens = re.findall(r"[A-Za-z0-9_.-]{2,64}", value)
        stop = {
            "search",
            "find",
            "about",
            "who",
            "what",
            "where",
            "when",
            "is",
            "are",
            "tell",
            "me",
            "please",
            "latest",
            "news",
            "profile",
            "account",
            "github",
            "gitlab",
            "linkedin",
            "twitter",
            "user",
            "username",
            "repo",
            "repository",
            "look",
            "check",
            "verify",
            "профиль",
            "аккаунт",
            "гитхаб",
            "гитлаб",
            "репо",
            "репозиторий",
            "найди",
            "поищи",
            "про",
            "него",
            "нее",
            "неё",
            "их",
            "кто",
            "что",
            "где",
            "когда",
            "скажи",
            "мне",
            "пожалуйста",
            "his",
            "her",
            "their",
            "has",
            "have",
            "had",
            "what",
            "which",
            "other",
            "project",
            "projects",
            "repos",
            "there",
            "those",
            "these",
            "them",
            "look",
            "into",
            "from",
            "with",
            "without",
            "for",
            "and",
            "or",
            "to",
            "of",
            "in",
            "on",
            "at",
        }
        candidates: list[str] = []
        for token in reversed(tokens):
            candidate = token.strip(".-_")
            if not candidate:
                continue
            low = candidate.lower()
            if low in stop:
                continue
            if len(candidate) < 2:
                continue
            if low.isdigit():
                continue
            candidates.append(candidate)

        if candidates:
            def _candidate_score(item: str) -> tuple[int, int]:
                low = item.lower()
                score = 0
                if re.search(r"\d", item):
                    score += 3
                if any(ch in item for ch in ("_", "-", ".")):
                    score += 2
                if re.search(r"[a-z]", low) and re.search(r"\d", low):
                    score += 2
                # Slight preference to plausible username lengths.
                if 4 <= len(item) <= 24:
                    score += 1
                return score, len(item)

            candidates.sort(key=_candidate_score, reverse=True)
            return candidates[0]
    return None


def _parse_search_intent(query: str, *, topic_hint: str | None, lang: str | None) -> dict[str, Any]:
    value = (query or "").strip()
    tokens = _text_tokens(value)
    domain = _search_target_domain_from_intent(value) or (topic_hint and _search_target_domain_from_intent(topic_hint)) or None

    latest_markers = {
        "latest",
        "recent",
        "today",
        "current",
        "now",
        "breaking",
        "live",
        "последн",
        "сегодня",
        "сейчас",
        "актуал",
        "свеж",
        "прямо",
    }
    wants_latest = any(marker in value.lower() for marker in latest_markers)

    kinds: list[str] = []
    if _looks_like_profile_search(value):
        kinds.append("profile")
    if any(token in tokens for token in {"news", "headline", "новости", "заголовки"}):
        kinds.append("news")
    if any(token in tokens for token in {"sport", "sports", "match", "score", "league", "матч", "счет", "лига", "турнир"}):
        kinds.append("sports")
    if any(token in tokens for token in {"price", "cost", "rate", "stock", "crypto", "цена", "стоимость", "курс"}):
        kinds.append("price")
    if any(token in tokens for token in {"docs", "documentation", "api", "reference", "документация", "доки"}):
        kinds.append("docs")
    if any(token in tokens for token in {"who", "what", "where", "country", "capital", "president", "ceo", "кто", "что", "где", "страна", "столица", "президент"}):
        kinds.append("factual")
    if not kinds:
        kinds.append("general")

    profile_handle = _extract_profile_handle_candidate(value, topic_hint=topic_hint) if "profile" in kinds else None
    if not profile_handle and topic_hint and ("profile" in kinds or _is_generic_search_phrase(value) or _looks_like_context_dependent_followup(value)):
        profile_handle = _extract_profile_handle_candidate(topic_hint, topic_hint=None)

    primary_kind = kinds[0]
    if "news" in kinds:
        primary_kind = "news"
    elif "sports" in kinds:
        primary_kind = "sports"
    elif "price" in kinds:
        primary_kind = "price"
    elif "profile" in kinds:
        primary_kind = "profile"
    elif "docs" in kinds:
        primary_kind = "docs"
    elif "factual" in kinds:
        primary_kind = "factual"

    normalized_lang = normalize_language(lang or "en")
    return {
        "kind": primary_kind,
        "kinds": kinds,
        "wants_latest": wants_latest,
        "domain": domain,
        "profile_handle": profile_handle,
        "lang": normalized_lang,
        "raw": value,
    }


def _query_is_broad(value: str, *, intent: dict[str, Any], topic_hint: str | None) -> bool:
    raw = (value or "").strip()
    if not raw:
        return True
    tokens = _text_tokens(raw)
    if not tokens:
        return True
    if topic_hint and (_looks_like_context_dependent_followup(raw) or _looks_like_search_execution_confirmation(raw)):
        return False
    if intent.get("kind") == "profile":
        # Profile queries should specify a handle or have contextual topic.
        if intent.get("profile_handle") or topic_hint:
            return False
        return True
    generic_bucket = {
        "news",
        "новости",
        "sport",
        "sports",
        "match",
        "price",
        "country",
        "company",
        "organization",
        "person",
        "человек",
        "компания",
        "организация",
        "страна",
    }
    if len(tokens) <= 3 and tokens <= generic_bucket:
        return True
    if len(tokens) <= 2 and not topic_hint:
        if all(token in generic_bucket for token in tokens):
            return True
    return False


def _search_clarification_prompt(query: str, *, lang: str, intent: dict[str, Any], topic_hint: str | None) -> str | None:
    if not _query_is_broad(query, intent=intent, topic_hint=topic_hint):
        return None
    normalized_lang = normalize_language(lang)
    kind = str(intent.get("kind") or "general")

    if normalized_lang == "ru":
        if kind == "profile":
            return "Уточни, пожалуйста, кого именно искать: username/ссылка и платформу (GitHub/GitLab/LinkedIn/X)."
        if kind == "news":
            return "Уточни тему новостей: про кого/что именно и за какой период (сегодня, неделя, месяц)."
        if kind == "sports":
            return "Уточни команду/турнир и период (например: последние 5 матчей Карабаха)."
        if kind == "price":
            return "Уточни, цену чего именно нужно найти и в какой валюте."
        return "Уточни, пожалуйста, запрос: про кого/что искать и какой результат нужен."

    if kind == "profile":
        return "Please specify who to look up: username/link and platform (GitHub/GitLab/LinkedIn/X)."
    if kind == "news":
        return "Please clarify the news topic: about whom/what and for what period (today, week, month)."
    if kind == "sports":
        return "Please specify the team/tournament and period (for example: last 5 Qarabag matches)."
    if kind == "price":
        return "Please specify what price you want and in which currency."
    return "Please clarify the query: what exactly should I search for and what result you need."


def _has_non_latin_script(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r"[^\x00-\x7F]", text))


def _language_aware_query_variants(query: str, *, intent: dict[str, Any], topic_hint: str | None) -> list[str]:
    base = (query or "").strip()
    if not base:
        return []
    variants: list[str] = [base]

    kind = str(intent.get("kind") or "general")
    wants_repos = _profile_query_wants_repositories(base)
    entity = intent.get("profile_handle") or (topic_hint and _compact_search_query(topic_hint, max_words=8)) or ""
    needs_bridge = _has_non_latin_script(base)

    if needs_bridge:
        if kind == "profile":
            platform = _search_target_domain_from_intent(base) or _search_target_domain_from_intent(topic_hint or "")
            platform_hint = "github" if platform == "github.com" else "gitlab" if platform == "gitlab.com" else "profile"
            bridge = f"{entity or base} {platform_hint} profile".strip()
            variants.append(bridge)
            if wants_repos:
                variants.append(f"{entity or base} {platform_hint} repositories".strip())
                variants.append(f"{entity or base} {platform_hint} projects".strip())
        elif kind == "news":
            variants.append(f"{entity or base} latest news".strip())
        elif kind == "sports":
            variants.append(f"{entity or base} match results today".strip())
        elif kind == "price":
            variants.append(f"{entity or base} price today".strip())
        elif kind == "docs":
            variants.append(f"{entity or base} official documentation".strip())
        elif kind == "factual":
            variants.append(f"{entity or base} facts".strip())

    # Include topic-enriched variant when query omits subject.
    if topic_hint and not _query_mentions_topic(base, topic_hint):
        variants.append(f"{base} {_compact_search_query(topic_hint, max_words=8)}".strip())
    if kind == "profile" and wants_repos:
        platform = _search_target_domain_from_intent(base) or _search_target_domain_from_intent(topic_hint or "")
        if platform == "github.com":
            variants.append(f"{entity or base} github repositories".strip())
            variants.append(f"{entity or base} site:github.com".strip())
        elif platform == "gitlab.com":
            variants.append(f"{entity or base} gitlab projects".strip())
            variants.append(f"{entity or base} site:gitlab.com".strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for item in variants:
        normalized = re.sub(r"\s+", " ", item).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        deduped.append(normalized)
        seen.add(key)
    return deduped


def _extract_recency_days(text: str) -> float | None:
    value = (text or "").strip().lower()
    if not value:
        return None
    if any(token in value for token in ("today", "сегодня")):
        return 0.0
    if any(token in value for token in ("yesterday", "вчера")):
        return 1.0

    rel_hours = re.search(r"\b(\d{1,3})\s*(hour|hours|hr|hrs|ч|час|часа|часов)\b", value)
    if rel_hours:
        return int(rel_hours.group(1)) / 24.0
    rel_days = re.search(r"\b(\d{1,3})\s*(day|days|дн|день|дня|дней)\b", value)
    if rel_days:
        return float(int(rel_days.group(1)))

    iso_match = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", value)
    if iso_match:
        year = int(iso_match.group(1))
        month = int(iso_match.group(2))
        day = int(iso_match.group(3))
        try:
            date_value = datetime(year=year, month=month, day=day, tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - date_value
            return max(0.0, float(delta.days))
        except ValueError:
            return None
    return None


def _apply_recency_ranking(results: list[WebSearchResult], *, intent: dict[str, Any]) -> list[WebSearchResult]:
    if not results:
        return []
    kind = str(intent.get("kind") or "general")
    wants_latest = bool(intent.get("wants_latest"))
    if kind not in {"news", "sports", "price"} and not wants_latest:
        return results

    scored: list[tuple[int, float, int, WebSearchResult]] = []
    for idx, item in enumerate(results):
        recency = _extract_recency_days(f"{item.title} {item.snippet} {item.url}")
        if recency is None:
            scored.append((1, 10_000.0, idx, item))
        else:
            scored.append((0, recency, idx, item))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in scored]


async def _fallback_backend_search(
    query: str,
    *,
    intent: dict[str, Any],
    topic_hint: str | None,
    max_results: int,
) -> list[WebSearchResult]:
    kind = str(intent.get("kind") or "general")
    domain = str(intent.get("domain") or "")
    handle = str(intent.get("profile_handle") or "").strip()
    lang_code = str(intent.get("lang") or "en")
    entity = handle or _extract_profile_handle_candidate(query, topic_hint=topic_hint) or _compact_search_query(topic_hint or "", max_words=8)

    collected: list[WebSearchResult] = []

    if kind == "profile":
        try:
            if domain == "github.com" and entity:
                collected.extend(await github_user_search(entity, max_results=max_results))
            elif domain == "gitlab.com" and entity:
                collected.extend(await gitlab_user_search(entity, max_results=max_results))
            elif entity:
                collected.extend(await github_user_search(entity, max_results=max_results))
                if len(collected) < max_results:
                    collected.extend(await gitlab_user_search(entity, max_results=max_results - len(collected)))
        except Exception:  # noqa: BLE001
            pass

    if not collected and kind in {"factual", "news", "general"} and domain not in {"github.com", "gitlab.com", "linkedin.com", "x.com"}:
        wiki_query = entity or query
        if wiki_query:
            try:
                collected.extend(await wikipedia_search(wiki_query, max_results=max_results, language=lang_code))
            except Exception:  # noqa: BLE001
                pass

    return _dedupe_search_results(collected)[:max_results]


def _trusted_domains_for_query(query: str, *, topic_hint: str | None = None) -> list[str]:
    combined = f"{query or ''} {topic_hint or ''}".strip().lower()
    tokens = _text_tokens(combined)
    if not tokens:
        return []

    trusted: list[str] = []

    news_tokens = {"news", "headline", "breaking", "новости", "заголовки", "срочно"}
    sports_tokens = {"sport", "sports", "match", "score", "team", "league", "матч", "счет", "команда", "лига"}
    docs_tokens = {"docs", "documentation", "api", "reference", "manual", "документация", "доки", "справка"}
    factual_tokens = {
        "who",
        "кто",
        "person",
        "biography",
        "organization",
        "company",
        "country",
        "capital",
        "population",
        "president",
        "ceo",
        "человек",
        "биография",
        "организация",
        "компания",
        "страна",
        "столица",
        "население",
        "президент",
    }

    if tokens & news_tokens:
        _append_unique_domains(trusted, ["reuters.com", "apnews.com", "bbc.com", "aljazeera.com", "reddit.com"])
    if tokens & sports_tokens:
        _append_unique_domains(trusted, ["espn.com", "sofascore.com", "flashscore.com", "uefa.com", "fifa.com", "reddit.com"])
    if tokens & docs_tokens:
        _append_unique_domains(trusted, ["developer.mozilla.org", "docs.python.org", "readthedocs.io", "github.com", "wikipedia.org"])
    if tokens & factual_tokens:
        _append_unique_domains(trusted, ["wikipedia.org", "britannica.com", "worldbank.org", "un.org", "reddit.com"])
    if not trusted:
        # Prefer community/explanatory sources slightly more often for broad questions.
        _append_unique_domains(trusted, ["wikipedia.org", "reddit.com"])

    return trusted


def _preferred_domains_for_search(query: str, *, topic_hint: str | None = None) -> tuple[list[str], bool]:
    domain = _search_target_domain_from_intent(query)
    if not domain and topic_hint:
        domain = _search_target_domain_from_intent(topic_hint)
    trusted_domains = _trusted_domains_for_query(query, topic_hint=topic_hint)

    tokens = _text_tokens(query)
    strict_markers = {
        "profile",
        "account",
        "user",
        "username",
        "repo",
        "repository",
        "профиль",
        "аккаунт",
        "репо",
        "репозиторий",
        "страница",
        "link",
        "links",
        "ссылка",
        "ссылки",
    }
    strict = bool(
        domain
        and (
            bool(tokens & strict_markers)
            or _is_generic_search_phrase(query)
            or _looks_like_context_dependent_followup(query)
        )
    )

    domains: list[str] = []
    if domain:
        _append_unique_domains(domains, [domain])
    if not strict:
        _append_unique_domains(domains, trusted_domains)

    return domains, strict


def _build_precise_search_query(
    query: str,
    *,
    topic_hint: str | None,
    preferred_domains: list[str],
    strict: bool,
) -> str:
    base = (query or "").strip()
    if not base:
        return ""
    if "site:" in base.lower():
        return base
    if not strict or not preferred_domains:
        return base

    if topic_hint and not _query_mentions_topic(base, topic_hint):
        topic_part = _compact_search_query(topic_hint, max_words=8)
        if topic_part:
            base = f"{base} {topic_part}".strip()
    return f"{base} site:{preferred_domains[0]}".strip()


async def _run_ranked_web_search(
    query: str,
    *,
    topic_hint: str | None,
    lang: str,
    max_results: int,
) -> list[WebSearchResult]:
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []
    intent = _parse_search_intent(normalized_query, topic_hint=topic_hint, lang=lang)
    preferred_domains, strict_domain = _preferred_domains_for_search(normalized_query, topic_hint=topic_hint)

    if (
        intent.get("kind") == "profile"
        and str(intent.get("domain") or "") in {"github.com", "gitlab.com"}
        and str(intent.get("profile_handle") or "").strip()
        and not _profile_query_wants_repositories(normalized_query)
    ):
        primary_profile_results = await _fallback_backend_search(
            normalized_query,
            intent=intent,
            topic_hint=topic_hint,
            max_results=max_results,
        )
        if primary_profile_results:
            return primary_profile_results

    attempts: list[str] = []
    for variant in _language_aware_query_variants(normalized_query, intent=intent, topic_hint=topic_hint):
        precise_query = _build_precise_search_query(
            variant,
            topic_hint=topic_hint,
            preferred_domains=preferred_domains,
            strict=strict_domain,
        )
        if precise_query:
            attempts.append(precise_query)
        if any(domain == "wikipedia.org" for domain in preferred_domains):
            attempts.append(f"{variant} site:wikipedia.org")
        if any(domain == "reddit.com" for domain in preferred_domains):
            attempts.append(f"{variant} site:reddit.com")
        attempts.append(variant)
    if strict_domain and preferred_domains and topic_hint:
        fallback_query = f"{_compact_search_query(topic_hint, max_words=8)} site:{preferred_domains[0]}".strip()
        if fallback_query:
            attempts.append(fallback_query)

    dedup_attempts: list[str] = []
    seen_attempts: set[str] = set()
    for item in attempts:
        normalized = re.sub(r"\s+", " ", item).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen_attempts:
            continue
        dedup_attempts.append(normalized)
        seen_attempts.add(key)

    best_relaxed: list[WebSearchResult] = []
    for attempt in dedup_attempts:
        results = await duckduckgo_search_news_aware(attempt, max_results=max_results)
        results = _prioritize_search_results(
            results,
            preferred_domains=preferred_domains,
            strict=strict_domain,
        )
        results = _filter_noisy_search_results(
            results,
            preferred_domains=preferred_domains,
            strict=strict_domain,
        )
        results = _apply_recency_ranking(results, intent=intent)

        if results:
            if not strict_domain:
                return results
            if _count_results_for_domains(results, preferred_domains) > 0:
                return results
            if not best_relaxed:
                best_relaxed = results

    fallback_results = await _fallback_backend_search(
        normalized_query,
        intent=intent,
        topic_hint=topic_hint,
        max_results=max_results,
    )
    if fallback_results:
        fallback_results = _prioritize_search_results(
            fallback_results,
            preferred_domains=preferred_domains,
            strict=False,
        )
        fallback_results = _apply_recency_ranking(fallback_results, intent=intent)
        return fallback_results

    if best_relaxed:
        return best_relaxed

    # Safety fallback: return plain DDG results without strict ranking/filtering,
    # so the response can still include source links.
    try:
        plain = await duckduckgo_search_news_aware(normalized_query, max_results=max_results)
    except Exception:  # noqa: BLE001
        plain = []
    plain = _dedupe_search_results(plain)
    if plain:
        return plain

    try:
        plain_direct = await duckduckgo_search(normalized_query, max_results=max_results)
    except Exception:  # noqa: BLE001
        plain_direct = []
    return _dedupe_search_results(plain_direct)


def _profile_query_wants_repositories(query: str) -> bool:
    tokens = _text_tokens(query or "")
    if not tokens:
        return False
    repo_tokens = {
        "repo",
        "repos",
        "repository",
        "repositories",
        "project",
        "projects",
        "portfolio",
        "код",
        "репо",
        "репозиторий",
        "репозитории",
        "проект",
        "проекты",
    }
    return bool(tokens & repo_tokens)


def _query_mentions_topic(query: str, topic: str) -> bool:
    query_tokens = _text_tokens(query)
    topic_tokens = _text_tokens(_compact_search_query(topic, max_words=12))
    if not query_tokens or not topic_tokens:
        return False
    meaningful_query = {token for token in query_tokens if len(token) >= 3}
    meaningful_topic = {token for token in topic_tokens if len(token) >= 3}
    if meaningful_query and meaningful_topic:
        return bool(meaningful_query & meaningful_topic)
    return bool(query_tokens & topic_tokens)


def _strip_markdown_code_fence(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("```") and value.endswith("```"):
        lines = value.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return value


def _extract_query_from_llm_output(raw_output: str, *, fallback: str) -> tuple[str, bool]:
    """
    Parse query-rewrite output from the model.

    Expected shape: JSON object with keys `query` and `use_topic`.
    Falls back to permissive parsing for robustness.
    """
    cleaned = _strip_markdown_code_fence(raw_output)
    if not cleaned:
        return fallback, False

    try:
        parsed = json.loads(cleaned)
    except Exception:  # noqa: BLE001
        parsed = None

    if isinstance(parsed, dict):
        query = str(parsed.get("query", "")).strip()
        use_topic = bool(parsed.get("use_topic"))
        if query:
            return query, use_topic

    line_match = re.search(r"(?:^|\n)\s*query\s*[:=]\s*(.+)", cleaned, flags=re.IGNORECASE)
    if line_match:
        candidate = line_match.group(1).strip().strip("\"'")
        if candidate:
            return candidate, ("use_topic" in cleaned.lower() and "true" in cleaned.lower())

    first_line = next((line.strip() for line in cleaned.splitlines() if line.strip()), "")
    if first_line:
        compact = first_line.strip().strip("\"'")
        if compact:
            return compact, False

    return fallback, False


def _extract_search_decision_from_llm_output(raw_output: str) -> tuple[bool, float | None]:
    cleaned = _strip_markdown_code_fence(raw_output)
    if not cleaned:
        return False, None

    try:
        parsed = json.loads(cleaned)
    except Exception:  # noqa: BLE001
        parsed = None

    if isinstance(parsed, dict):
        search_flag = bool(parsed.get("search") or parsed.get("should_search"))
        confidence_raw = parsed.get("confidence")
        confidence: float | None
        if isinstance(confidence_raw, (int, float)):
            confidence = max(0.0, min(1.0, float(confidence_raw)))
        else:
            confidence = None
        return search_flag, confidence

    line_flag = re.search(r"(?:^|\n)\s*(?:search|should_search)\s*[:=]\s*(true|false|yes|no|1|0)", cleaned, re.I)
    if line_flag:
        token = line_flag.group(1).lower()
        return token in {"true", "yes", "1"}, None

    compact = cleaned.strip().lower()
    if compact in {"true", "yes", "1", "search"}:
        return True, None
    return False, None


def _should_try_llm_context_resolution(raw_query: str, topic_hint: str | None) -> bool:
    if not topic_hint:
        return False
    query = (raw_query or "").strip()
    if not query:
        return False
    if len(query) > 220:
        return False
    if _contains_domain_like(query):
        return False
    if _query_mentions_topic(query, topic_hint):
        return False

    tokens = _text_tokens(query)
    if not tokens:
        return False
    if len(tokens) <= 10:
        return True
    if _is_generic_search_phrase(query) or _looks_like_context_dependent_followup(query):
        return True
    return False


def _should_try_llm_search_decision(raw_text: str, topic_hint: str | None) -> bool:
    value = (raw_text or "").strip()
    if not value:
        return False
    if value.startswith("/"):
        return False
    if "```" in value:
        return False
    if len(value) > 320:
        return False
    if _contains_domain_like(value):
        return False

    tokens = _text_tokens(value)
    if not tokens:
        return False
    if topic_hint and len(tokens) <= 12:
        return True
    if "?" in value and len(tokens) <= 20:
        return True
    if len(tokens) <= 8:
        return True
    return False


def _looks_like_time_query(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    markers = (
        "time in",
        "time",
        "current time",
        "local time",
        "what time",
        "time difference",
        "time zone",
        "timezone",
        "utc",
        "gmt",
        "offset",
        "время",
        "который час",
        "часов",
        "разница во времени",
        "часовой пояс",
    )
    if any(m in value for m in markers):
        return True
    if re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", value):
        return True
    if re.search(r"\b\d{1,2}:\d{2}\b", value):
        return True
    return False


def _looks_like_current_time_query(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    markers = (
        "time in",
        "current time",
        "local time",
        "what time",
        "time now",
        "время в",
        "который час",
        "сколько времени",
        "сейчас",
    )
    if any(m in value for m in markers):
        return True
    return False


def _looks_like_utc_now_query(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    date_markers = {
        "what is the date",
        "today date",
        "date today",
        "какая сегодня дата",
        "какое сегодня число",
        "сегодняшняя дата",
    }
    has_date_marker = any(marker in value for marker in date_markers)
    if not _looks_like_time_query(value) and not has_date_marker:
        return False
    if _parse_time_conversion_query(value) is not None:
        return False

    # City/location queries should go through web search.
    if re.search(r"\btime in\s+[a-zа-я]", value):
        if not re.search(r"\btime in\s+(utc|gmt)\b", value):
            return False
    if "время в " in value and "время в utc" not in value and "время в gmt" not in value:
        return False
    if re.search(r"^\s*(?:in|в)\s*(?:utc|gmt)\s*[+-]\s*\d{1,2}(?::?\d{2})?\s*$", value):
        return False
    if re.search(r"\b(?:utc|gmt)\s*[+-]\s*\d{1,2}(?::?\d{2})?\b", value):
        return False

    utc_markers = {
        "what time is it",
        "what time now",
        "current time",
        "time now",
        "который час",
        "сколько времени",
        "какое сейчас время",
        "текущее время",
    }
    if has_date_marker or any(marker in value for marker in utc_markers):
        return True
    if re.search(r"\b(?:what\s+time|current\s+time|time\s+now|time)\s*(?:is\s+it\s*)?(?:in\s+)?(?:utc|gmt)\b", value):
        return True
    if re.search(r"\b(?:который\s+час|сколько\s+времени|какое\s+сейчас\s+время|текущее\s+время)\s*(?:в\s+)?(?:utc|gmt)\b", value):
        return True

    # Short generic asks like "time?" / "время?" should default to UTC.
    compact = re.sub(r"[^a-zа-я0-9 ]+", " ", value).strip()
    if compact in {"time", "время", "date", "дата"}:
        return True
    return False


def _parse_time_conversion_query(raw: str) -> tuple[int, bool, str, str] | None:
    text = (raw or "").strip()
    if not text:
        return None
    left = right = ""
    if "->" in text:
        left, right = text.split("->", maxsplit=1)
    elif " to " in text:
        left, right = text.split(" to ", maxsplit=1)
    elif " в " in text:
        left, right = text.split(" в ", maxsplit=1)

    if left and right:
        left = left.strip()
        right = right.strip()
        if not left or not right:
            return None
        match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+(.*)$", left, flags=re.IGNORECASE)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        ampm = (match.group(3) or "").lower()
        from_loc = match.group(4).strip()
        to_loc = right
    else:
        # Natural language: "if it's 10 am in Los Angeles, what time in Baku"
        match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", text, flags=re.IGNORECASE)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        ampm = (match.group(3) or "").lower()
        loc_matches = re.findall(
            r"\b(?:in|в)\s+([A-Za-zА-Яа-я ._-]+?)(?=\b(?:to|in|в)\b|\?|\.|,|$)",
            text,
            flags=re.IGNORECASE,
        )
        if len(loc_matches) < 2:
            to_match = re.search(r"\bto\s+([A-Za-zА-Яа-я ._-]+?)(?=\?|\.|,|$)", text, flags=re.IGNORECASE)
            if len(loc_matches) == 1 and to_match:
                loc_matches.append(to_match.group(1))
        if len(loc_matches) < 2:
            return None
        from_loc = loc_matches[0].strip()
        to_loc = loc_matches[1].strip()
    if not from_loc or not to_loc:
        return None

    if hour > 24 or minute > 59:
        return None

    had_am_pm = bool(ampm)
    if ampm:
        if hour == 12:
            hour = 0
        if ampm == "pm":
            hour += 12
    time_minutes = hour * 60 + minute
    return time_minutes, had_am_pm, from_loc, to_loc


async def _find_time_is_url(location: str) -> str | None:
    query = f"time in {location}".strip()
    results = await duckduckgo_search(query, max_results=8)
    for item in results:
        if "time.is/" in item.url:
            return item.url
    return None


def _detect_reply_language(text: str, *, fallback_lang: str) -> str:
    fallback = normalize_language(fallback_lang or "en")
    value = (text or "").strip()
    if not value:
        return fallback

    # Script-based detection for non-latin languages.
    if re.search(r"[\u0600-\u06FF]", value):
        return "ar"
    if re.search(r"[\u0900-\u097F]", value):
        return "hi"
    if re.search(r"[А-Яа-яЁёІіЇїЄєҐґ]", value):
        if re.search(r"[ІіЇїЄєҐґ]", value):
            return "uk"
        return "ru"

    # Lightweight token heuristics for latin-script languages.
    tokens = _text_tokens(value.lower())
    if not tokens:
        return fallback

    def _score(markers: set[str]) -> int:
        return sum(1 for token in tokens if token in markers)

    lang_markers: dict[str, set[str]] = {
        "es": {"que", "de", "para", "como", "hola", "gracias", "por", "donde", "cuando", "porque"},
        "fr": {"que", "pour", "avec", "bonjour", "merci", "est", "quoi", "comment", "vous", "dans"},
        "de": {"der", "die", "das", "und", "ist", "nicht", "wie", "was", "danke", "ich"},
        "it": {"che", "per", "con", "come", "ciao", "grazie", "sono", "non", "dove", "quando"},
        "pt": {"que", "para", "com", "como", "ola", "obrigado", "voce", "nao", "onde", "quando"},
        "tr": {"ve", "bir", "bu", "icin", "merhaba", "tesekkur", "nasil", "ne", "evet", "hayir"},
    }
    scores = {lang: _score(markers) for lang, markers in lang_markers.items()}
    best_lang = max(scores, key=scores.get)
    if scores[best_lang] >= 2:
        return best_lang
    return "en" if re.search(r"[A-Za-z]", value) else fallback


def _format_day_shift(lang: str, shift: int) -> str:
    if shift == 0:
        return ""
    if shift == 1:
        return t(lang, "convert_day_next")
    if shift == -1:
        return t(lang, "convert_day_prev")
    if shift > 1:
        return t(lang, "convert_day_in", days=str(shift))
    return t(lang, "convert_day_ago", days=str(abs(shift)))


def _should_auto_web_search(text: str, wants_search: bool, *, topic_hint: str | None = None) -> bool:
    if wants_search:
        return True
    value = (text or "").strip().lower()
    if not value:
        return False
    if value.startswith("/"):
        return False
    if "```" in value:
        return False

    tokens = _text_tokens(value)
    if _looks_like_time_query(value):
        return True
    if topic_hint and _looks_like_search_execution_confirmation(value):
        return True
    if _looks_like_context_dependent_followup(value) and topic_hint:
        return True
    if _has_semantic_search_intent(value, topic_hint=topic_hint):
        return True

    verification_tokens = {
        "check",
        "verify",
        "validation",
        "проверь",
        "проверка",
        "чекни",
        "чекай",
        "чек",
    }
    repo_tokens = {
        "github",
        "gitlab",
        "repo",
        "repository",
        "гитхаб",
        "репо",
        "репозиторий",
    }
    if (tokens & verification_tokens) and (tokens & repo_tokens):
        return True
    domain_like = _contains_domain_like(value)
    if domain_like and (tokens & verification_tokens):
        return True

    # Auto-search for up-to-date, verification-heavy, or link/source requests.
    phrase_triggers = (
        # Time / timezone / "current"
        "current time",
        "time in",
        "time now",
        "what time",
        "time difference",
        "time zone",
        "timezone",
        "utc",
        "gmt",
        "offset",
        "время в",
        "который час",
        "сколько времени",
        "разница во времени",
        "часовой пояс",
        "на данный момент",
        "прямо сейчас",
        "сейчас",
        "сегодня",
        "today",
        "right now",
        "live",
        # News / recent events
        "most recent",
        "latest news",
        "recent news",
        "breaking news",
        "последние новости",
        "свежие новости",
        # Prices / rates
        "exchange rate",
        "stock price",
        "crypto price",
        "live price",
        "курс валют",
        "сколько стоит",
        # Versions / releases / updates
        "latest version",
        "latest release",
        "what's new",
        "release date",
        "patch notes",
        "последняя версия",
        # Links / official sources
        "official site",
        "official website",
        "official docs",
        "github repo",
        "check github",
        "verify github",
        "официальный сайт",
        "проверь гитхаб",
        "чекни гитхаб",
        "проверь репо",
        # Places / contacts / availability (often changes)
        "opening hours",
        "in stock",
        "часы работы",
        "в наличии",
        # Sports / schedules / live status
        "score now",
        "live score",
        "match today",
        "game today",
        "кто выиграл",
        "счет матча",
        "расписание матчей",
    )
    if any(p in value for p in phrase_triggers):
        return True

    token_triggers = {
        "today",
        "now",
        "current",
        "latest",
        "recent",
        "live",
        "сегодня",
        "сейчас",
        "текущий",
        "последний",
        # News
        "news",
        "новости",
        # Prices / rates
        "price",
        "цена",
        "стоимость",
        "курс",
        "usd",
        "eur",
        "btc",
        "eth",
        # Versions / releases / updates
        "version",
        "release",
        "changelog",
        "update",
        "updated",
        "релиз",
        "версия",
        "вышел",
        "вышла",
        "вышли",
        "выйдет",
        # Policies / rules / law (often changes; high-stakes)
        "policy",
        "terms",
        "rules",
        "law",
        "регламент",
        "правила",
        "условия",
        "политика",
        "закон",
        "налог",
        "виза",
        # "current role holder" questions
        "ceo",
        "president",
        "министр",
        "президент",
        "премьер",
        "governor",
        "мэр",
        "senator",
        # Explicit sources / links / official info
        "source",
        "sources",
        "citation",
        "cite",
        "link",
        "documentation",
        "github",
        "gitlab",
        "repo",
        "repository",
        "источник",
        "источники",
        "ссылка",
        "ссылки",
        "документация",
        "доки",
        "гитхаб",
        "репо",
        "репозиторий",
        # Places / contacts
        "address",
        "phone",
        "адрес",
        "телефон",
        "контакты",
        # Weather (time-sensitive)
        "weather",
        "forecast",
        "погода",
        "прогноз",
        # Sports
        "score",
        "scores",
        "match",
        "game",
        "standings",
        "table",
        "счет",
        "матч",
        "игра",
        "турнир",
        "таблица",
    }
    if tokens & token_triggers:
        return True

    prefix_triggers = ("обнов", "patch", "cve", "cve-")
    if any(any(t.startswith(prefix) for t in tokens) for prefix in prefix_triggers):
        return True

    # Year-anchored questions are often time-sensitive.
    if re.search(r"\b20\d{2}\b", value) and ("?" in value or "latest" in tokens or "последн" in value):
        return True

    # Contextual follow-ups like "сколько стоит?" should search only if we have a topic to attach.
    if topic_hint:
        followup_phrases = ("сколько стоит", "официальный сайт", "часы работы", "где купить")
        followup_tokens = {
            "цена",
            "стоимость",
            "курс",
            "ссылка",
            "ссылки",
            "источник",
            "источники",
            "документация",
            "адрес",
            "телефон",
            "контакты",
            "download",
            "скачать",
            "купить",
            "заказать",
            "сейчас",
            "сегодня",
            "latest",
            "now",
        }
        if any(p in value for p in followup_phrases) or (tokens & followup_tokens):
            return True

    return False


def _search_answer_style_guardrail(personality_name: str, *, include_clarify: bool) -> str:
    label = (personality_name or "selected personality").strip()
    text = (
        "Do not invent facts. "
        "Use sources internally for factual grounding, but do not output source numbers/links unless the user explicitly asks. "
        "Stay strictly on the asked question: no unrelated comparisons, anecdotes, or extra trivia. "
        "For factual questions, answer directly in the first sentence. "
        f"Keep the selected assistant personality ({label}) in tone, structure, and wording; "
        "do not switch to a generic neutral assistant voice."
    )
    if include_clarify:
        text += " If results are insufficient, say what is missing and ask for clarification."
    return text


async def _build_search_evidence_context(
    results: list[WebSearchResult],
    *,
    max_pages: int = 3,
    max_chars_per_page: int = 1200,
) -> str:
    if not results:
        return ""
    try:
        extracts = await fetch_page_extracts(
            results,
            max_pages=max_pages,
            max_chars_per_page=max_chars_per_page,
        )
    except Exception:  # noqa: BLE001
        return ""
    if not extracts:
        return ""
    return format_page_extracts(extracts)


def _split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        parts.append(text[start:end])
        start = end
    return parts


def _normalize_shared_model_id(raw_model: str) -> str:
    value = (raw_model or "").strip().lower()
    aliases = {
        "gpt4": "gpt4",
        "gpt-4": "gpt4",
        "gpt_4": "gpt4",
        "llama3": "llama3",
        "llama-3": "llama3",
        "llama_3": "llama3",
        "llama4": "llama4_media",
        "llama-4": "llama4_media",
        "llama_4": "llama4_media",
        "llama4_media": "llama4_media",
    }
    model_id = aliases.get(value, value)
    if model_id in SHARED_MODEL_PRESETS:
        return model_id
    return DEFAULT_SHARED_MODEL_ID


def _shared_model_name(model_id: str) -> str:
    safe_model_id = _normalize_shared_model_id(model_id)
    return SHARED_MODEL_PRESETS[safe_model_id]["model_name"]


def _shared_model_label(lang: str, model_id: str) -> str:
    safe_model_id = _normalize_shared_model_id(model_id)
    return t(lang, SHARED_MODEL_PRESETS[safe_model_id]["label_key"])


def _is_llama4_active_for_assist(*, user: UserSettings, selected_model: str, using_personal_api: bool) -> bool:
    if not using_personal_api:
        return _normalize_shared_model_id(user.model) == "llama4_media"
    raw = (selected_model or user.model or "").strip().lower()
    return "llama-4" in raw or "llama4" in raw


def _payload_has_media(user_payload: dict[str, Any]) -> bool:
    content = user_payload.get("content")
    if not isinstance(content, list):
        return False
    for item in content:
        if isinstance(item, dict) and item.get("type") == "image_url":
            return True
    return False


def _estimate_shared_input_cost(*, model_id: str, text: str, has_media: bool) -> int:
    safe_model_id = _normalize_shared_model_id(model_id)
    profile = SHARED_TOKEN_COSTS[safe_model_id]
    text_units = max(1, (len(text.strip()) + 179) // 180)
    cost = profile["text_in"] + text_units * 12
    if has_media:
        cost += profile["media_extra"]
    return max(1, cost)


def _estimate_shared_output_cost(*, model_id: str, text: str) -> int:
    safe_model_id = _normalize_shared_model_id(model_id)
    profile = SHARED_TOKEN_COSTS[safe_model_id]
    output_units = max(1, (len(text.strip()) + 199) // 200)
    return output_units * profile["out_per_200_chars"]


async def _send_assistant_response(
    *,
    message: Message,
    response: str,
    lang: str,
    sources_token: str | None = None,
) -> None:
    display_response = _prepare_response_for_display(response)
    sources_markup = sources_keyboard(token=sources_token, language=lang) if sources_token else None

    if _should_send_response_as_image(response):
        if await _send_response_as_image(
            message=message,
            response=display_response,
            lang=lang,
            reply_markup=sources_markup,
        ):
            return

    try:
        chunks = _split_message(display_response)
        last_index = len(chunks) - 1
        for index, chunk in enumerate(chunks):
            escaped_chunk = render_llm_markdown_v2(chunk, parse_mode="MarkdownV2")
            reply_markup = sources_markup if index == last_index else None
            await message.answer(escaped_chunk, parse_mode="MarkdownV2", reply_markup=reply_markup)
        return
    except TelegramBadRequest:
        # If MarkdownV2 formatting fails, retry with image to preserve full content.
        if await _send_response_as_image(
            message=message,
            response=display_response,
            lang=lang,
            reply_markup=sources_markup,
        ):
            return

    chunks = _split_message(display_response)
    last_index = len(chunks) - 1
    for index, chunk in enumerate(chunks):
        reply_markup = sources_markup if index == last_index else None
        await message.answer(chunk, reply_markup=reply_markup)


def _should_send_response_as_image(text: str) -> bool:
    if not text.strip():
        return False

    lines = text.splitlines()
    if _looks_like_markdown_table(lines):
        return True
    if _contains_math_notation(text):
        return True
    if len(text) > 4000 and text.count("```") % 2 == 1:
        return True
    return False


def _looks_like_markdown_table(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False

    table_like_lines = [line for line in lines if line.count("|") >= 2]
    if len(table_like_lines) < 2:
        return False

    separator_re = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
    if any(separator_re.match(line) for line in lines):
        return True

    # Fallback heuristic for simple pipe tables without explicit separator row.
    return len(table_like_lines) >= 3


def _contains_math_notation(text: str) -> bool:
    markers = (
        "$$",
        r"\(",
        r"\)",
        r"\[",
        r"\]",
        r"\begin{",
        r"\end{",
        r"\frac",
        r"\sum",
        r"\int",
        r"\sqrt",
        r"\cdot",
        r"\times",
        r"\div",
        r"\leq",
        r"\geq",
        r"\alpha",
        r"\beta",
        r"\gamma",
        r"\delta",
        r"\theta",
        r"\lambda",
        r"\pi",
        r"\sigma",
        r"\phi",
        r"\omega",
        r"\log",
        r"\ln",
        r"\sin",
        r"\cos",
        r"\tan",
    )
    return any(marker in text for marker in markers)


def _prepare_response_for_display(text: str) -> str:
    normalized = text
    normalized = re.sub(r"\\+begin\{[^{}]+\}", "", normalized)
    normalized = re.sub(r"\\+end\{[^{}]+\}", "", normalized)
    normalized = re.sub(r"\\+text\{([^{}]*)\}", r"\1", normalized)
    normalized = _replace_simple_latex_frac(normalized)
    normalized = _replace_simple_latex_sqrt(normalized)
    normalized = normalized.replace(r"\;", " ").replace(r"\,", " ").replace(r"\:", " ").replace(r"\!", "")
    normalized = normalized.replace(r"\\;", " ").replace(r"\\,", " ").replace(r"\\:", " ").replace(r"\\!", "")

    # Telegram does not render TeX delimiters; remove them for readability.
    normalized = normalized.replace("$$", "")
    normalized = normalized.replace("$", "")

    # Convert known LaTeX commands to readable symbols/words.
    normalized = re.sub(r"\\+([A-Za-z]+)", _latex_command_replacer, normalized)
    normalized = normalized.replace(r"\{", "{").replace(r"\}", "}")
    normalized = normalized.replace(r"\_", "_").replace(r"\%", "%")
    normalized = re.sub(r"\\([^\w\s])", r"\1", normalized)
    normalized = re.sub(r"\\\s", " ", normalized)
    normalized = _convert_powers_and_indices(normalized)
    normalized = _replace_numeric_fractions(normalized)
    normalized = _replace_math_fraction_slashes(normalized)
    return normalized


def _latex_command_replacer(match: re.Match[str]) -> str:
    command = match.group(1)
    return LATEX_COMMAND_MAP.get(command, command)


def _replace_simple_latex_frac(text: str) -> str:
    pattern = re.compile(r"\\+frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
    current = text
    for _ in range(8):
        current, count = pattern.subn(
            lambda m: _format_fraction_for_display(m.group(1), m.group(2)),
            current,
        )
        if count == 0:
            break
    return current


def _replace_simple_latex_sqrt(text: str) -> str:
    pattern = re.compile(r"\\+sqrt\s*\{([^{}]+)\}")
    current = text
    for _ in range(8):
        current, count = pattern.subn(r"√(\1)", current)
        if count == 0:
            break
    return current


def _format_fraction_for_display(numerator: str, denominator: str) -> str:
    num = numerator.strip()
    den = denominator.strip()
    compact_key = f"{num}/{den}"
    if compact_key in UNICODE_FRACTION_MAP:
        return UNICODE_FRACTION_MAP[compact_key]

    if re.fullmatch(r"[0-9]+", num) and re.fullmatch(r"[0-9]+", den):
        num_super = _to_script(num, SUPERSCRIPT_CHAR_MAP)
        den_sub = _to_script(den, SUBSCRIPT_CHAR_MAP)
        if num_super and den_sub:
            return f"{num_super}⁄{den_sub}"

    return f"({num})⁄({den})"


def _replace_numeric_fractions(text: str) -> str:
    pattern = re.compile(r"(?<![\w)])(\d{1,2})/(\d{1,2})(?![\w(])")

    def repl(match: re.Match[str]) -> str:
        num = match.group(1)
        den = match.group(2)
        key = f"{num}/{den}"
        if key in UNICODE_FRACTION_MAP:
            return UNICODE_FRACTION_MAP[key]
        num_super = _to_script(num, SUPERSCRIPT_CHAR_MAP)
        den_sub = _to_script(den, SUBSCRIPT_CHAR_MAP)
        if num_super and den_sub:
            return f"{num_super}⁄{den_sub}"
        return f"{num}⁄{den}"

    return pattern.sub(repl, text)


def _convert_powers_and_indices(text: str) -> str:
    result = text
    result = re.sub(r"\^\{([^{}]+)\}", lambda m: _render_script(m.group(1), SUPERSCRIPT_CHAR_MAP, "^"), result)
    result = re.sub(r"_\{([^{}]+)\}", lambda m: _render_script(m.group(1), SUBSCRIPT_CHAR_MAP, "_"), result)
    result = re.sub(r"\^([A-Za-z0-9+\-=()])", lambda m: _render_script(m.group(1), SUPERSCRIPT_CHAR_MAP, "^"), result)
    result = re.sub(r"_([A-Za-z0-9+\-=()])", lambda m: _render_script(m.group(1), SUBSCRIPT_CHAR_MAP, "_"), result)
    return result


def _render_script(content: str, mapping: dict[str, str], marker: str) -> str:
    raw = content.strip()
    converted = _to_script(raw, mapping)
    if converted:
        return converted
    return f"{marker}({raw})"


def _to_script(text: str, mapping: dict[str, str]) -> str | None:
    chars: list[str] = []
    for ch in text:
        mapped = mapping.get(ch)
        if mapped is None:
            return None
        chars.append(mapped)
    return "".join(chars)


def _replace_math_fraction_slashes(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.split("\n"):
        line = raw_line
        if "/" not in line:
            lines.append(line)
            continue
        lowered = line.lower()
        if "http://" in lowered or "https://" in lowered:
            lines.append(line)
            continue
        if _looks_math_like_line(line):
            line = re.sub(r"(?<=\S)\s*/\s*(?=\S)", "⁄", line)
        lines.append(line)
    return "\n".join(lines)


def _looks_math_like_line(line: str) -> bool:
    return bool(
        re.search(r"[=+\-*/^()0-9]", line)
        or re.search(r"[A-Za-zА-Яа-я][₀-₉]", line)
    )


async def _send_response_as_image(
    *,
    message: Message,
    response: str,
    lang: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    clean_response = _prepare_response_for_display(response)
    pages = _render_response_text_to_jpg_pages(clean_response)
    if not pages:
        return False

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO)
    for index, page in enumerate(pages):
        if index == 0:
            await message.answer_photo(
                photo=page,
                caption=t(lang, "response_sent_as_image"),
                reply_markup=reply_markup,
            )
        else:
            await message.answer_photo(photo=page)
    return True


def _render_response_text_to_jpg_pages(text: str) -> list[BufferedInputFile]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:  # noqa: BLE001
        return []

    fonts = _load_render_fonts(ImageFont)
    page_width = RESPONSE_IMAGE_WIDTH
    max_text_width = page_width - RESPONSE_IMAGE_MARGIN_X * 2
    max_content_height = MAX_RESPONSE_IMAGE_PAGE_HEIGHT - RESPONSE_IMAGE_MARGIN_Y * 2

    measure_canvas = Image.new("RGB", (1, 1), color=RESPONSE_IMAGE_BG_COLOR)
    measure_draw = ImageDraw.Draw(measure_canvas)

    normalized_text = _normalize_text_for_image(text)
    rows = _layout_rows_for_image(
        normalized_text,
        draw=measure_draw,
        fonts=fonts,
        max_width=max_text_width,
    )
    if not rows:
        rows = [{"kind": "spacer", "height": 24}]

    pages_layout = _paginate_rows(rows, max_content_height=max_content_height)
    pages: list[BufferedInputFile] = []

    for page_number, page_rows in enumerate(pages_layout, start=1):
        content_height = sum(int(row.get("height", 0)) for row in page_rows)
        image_height = max(520, RESPONSE_IMAGE_MARGIN_Y * 2 + content_height)

        image = Image.new("RGB", (page_width, image_height), color=RESPONSE_IMAGE_BG_COLOR)
        draw = ImageDraw.Draw(image)
        y = RESPONSE_IMAGE_MARGIN_Y

        for row in page_rows:
            kind = str(row.get("kind") or "text")
            row_height = int(row.get("height", 0))
            if kind == "rule":
                center_y = y + row_height // 2
                draw.line(
                    (
                        RESPONSE_IMAGE_MARGIN_X,
                        center_y,
                        page_width - RESPONSE_IMAGE_MARGIN_X,
                        center_y,
                    ),
                    fill=RESPONSE_IMAGE_RULE_COLOR,
                    width=1,
                )
            elif kind == "text":
                x = RESPONSE_IMAGE_MARGIN_X + int(row.get("x_offset", 0))
                segments = row.get("segments") or []
                if isinstance(segments, list):
                    for segment in segments:
                        if not isinstance(segment, tuple) or len(segment) != 2:
                            continue
                        segment_text, font_key = segment
                        if not segment_text:
                            continue
                        font = fonts.get(str(font_key), fonts["body"])
                        draw.text((x, y), str(segment_text), font=font, fill=RESPONSE_IMAGE_TEXT_COLOR)
                        x += _measure_text_width(draw, str(segment_text), font)
            y += row_height

        output = BytesIO()
        image.save(output, format="JPEG", quality=92, optimize=True)
        pages.append(
            BufferedInputFile(
                output.getvalue(),
                filename=f"response_{page_number}.jpg",
            )
        )

    return pages


def _normalize_text_for_image(text: str) -> str:
    cleaned = _prepare_response_for_display(text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.replace("\t", "    ")
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"(?m)^\s*>\s?", "", cleaned)
    cleaned = re.sub(r"(?m)\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _load_render_fonts(image_font_module: Any) -> dict[str, Any]:
    regular = _load_first_available_font(
        image_font_module,
        RESPONSE_IMAGE_BODY_SIZE,
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ),
    )
    bold = _load_first_available_font(
        image_font_module,
        RESPONSE_IMAGE_BODY_SIZE,
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        ),
    )
    mono = _load_first_available_font(
        image_font_module,
        RESPONSE_IMAGE_BODY_SIZE,
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ),
    )
    mono_bold = _load_first_available_font(
        image_font_module,
        RESPONSE_IMAGE_BODY_SIZE,
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ),
    )
    heading = _load_first_available_font(
        image_font_module,
        RESPONSE_IMAGE_HEADING_SIZE,
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ),
    )
    return {
        "body": regular,
        "body_bold": bold,
        "mono": mono,
        "mono_bold": mono_bold,
        "heading": heading,
    }


def _load_first_available_font(image_font_module: Any, size: int, candidates: tuple[str, ...]) -> Any:
    for path in candidates:
        try:
            return image_font_module.truetype(path, size=size)
        except OSError:
            continue
    return image_font_module.load_default()


def _layout_rows_for_image(text: str, *, draw: Any, fonts: dict[str, Any], max_width: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    has_content = False

    for raw_line in text.split("\n"):
        line_info = _classify_image_line(raw_line)
        kind = line_info["kind"]

        if kind == "blank":
            if rows and rows[-1]["kind"] != "spacer":
                rows.append({"kind": "spacer", "height": 18})
            continue

        if kind == "rule":
            rows.append({"kind": "rule", "height": 26})
            continue

        last_non_spacer = _last_non_spacer_kind(rows)
        if kind in {"heading", "section"} and has_content and last_non_spacer != "rule":
            rows.append({"kind": "rule", "height": 22})
            rows.append({"kind": "spacer", "height": 8})

        if kind == "heading":
            text_line, _ = _strip_bold_markers(str(line_info["text"]))
            wrapped = _wrap_text_to_width(
                text_line,
                draw=draw,
                font=fonts["heading"],
                max_width=max_width,
            )
            row_height = _line_height_for_font(draw, fonts["heading"], extra=10)
            rows.extend(
                {
                    "kind": "text",
                    "segments": [(line, "heading")],
                    "x_offset": 0,
                    "height": row_height,
                }
                for line in wrapped
            )
            rows.append({"kind": "spacer", "height": 8})
            has_content = True
            continue

        if kind == "section":
            text_line, _ = _strip_bold_markers(str(line_info["text"]))
            wrapped = _wrap_text_to_width(
                text_line,
                draw=draw,
                font=fonts["body_bold"],
                max_width=max_width,
            )
            row_height = _line_height_for_font(draw, fonts["body_bold"], extra=7)
            rows.extend(
                {
                    "kind": "text",
                    "segments": [(line, "body_bold")],
                    "x_offset": 0,
                    "height": row_height,
                }
                for line in wrapped
            )
            rows.append({"kind": "spacer", "height": 8})
            has_content = True
            continue

        if kind == "mono":
            mono_text = str(line_info["text"])
            wrapped = _wrap_text_to_width(
                mono_text,
                draw=draw,
                font=fonts["mono"],
                max_width=max_width - 12,
                keep_leading_spaces=True,
            )
            row_height = _line_height_for_font(draw, fonts["mono"], extra=5)
            rows.extend(
                {
                    "kind": "text",
                    "segments": [(line, "mono")],
                    "x_offset": 10,
                    "height": row_height,
                }
                for line in wrapped
            )
            has_content = True
            continue

        if kind == "bullet":
            bullet_text, bold_inline = _strip_bold_markers(str(line_info["text"]))
            bullet_font_key = "body_bold" if bold_inline else "body"
            text_line = f"• {bullet_text}"
            wrapped = _wrap_text_to_width(
                text_line,
                draw=draw,
                font=fonts[bullet_font_key],
                max_width=max_width - 24,
            )
            row_height = _line_height_for_font(draw, fonts[bullet_font_key], extra=6)
            base_indent = 18 + int(line_info.get("indent", 0)) * 4
            rows.extend(
                {
                    "kind": "text",
                    "segments": [(line, bullet_font_key)],
                    "x_offset": base_indent,
                    "height": row_height,
                }
                for line in wrapped
            )
            has_content = True
            continue

        if kind == "numbered":
            number_text, bold_inline = _strip_bold_markers(str(line_info["text"]))
            label = str(line_info["label"])
            font_key = "body_bold" if bold_inline else "body"
            wrapped = _wrap_text_to_width(
                f"{label} {number_text}",
                draw=draw,
                font=fonts[font_key],
                max_width=max_width - 18,
            )
            row_height = _line_height_for_font(draw, fonts[font_key], extra=6)
            rows.extend(
                {
                    "kind": "text",
                    "segments": [(line, font_key)],
                    "x_offset": int(line_info.get("indent", 0)) * 4,
                    "height": row_height,
                }
                for line in wrapped
            )
            has_content = True
            continue

        paragraph_text, bold_inline = _strip_bold_markers(str(line_info["text"]))
        paragraph_font_key = "body_bold" if bold_inline else "body"
        wrapped = _wrap_text_to_width(
            paragraph_text,
            draw=draw,
            font=fonts[paragraph_font_key],
            max_width=max_width,
        )
        row_height = _line_height_for_font(draw, fonts[paragraph_font_key], extra=6)
        rows.extend(
            {
                "kind": "text",
                "segments": [(line, paragraph_font_key)],
                "x_offset": 0,
                "height": row_height,
            }
            for line in wrapped
        )
        has_content = True

    while rows and rows[-1]["kind"] == "spacer":
        rows.pop()
    return rows


def _classify_image_line(raw_line: str) -> dict[str, Any]:
    line = raw_line.rstrip()
    stripped = line.strip()
    if not stripped:
        return {"kind": "blank"}

    if re.fullmatch(r"[-=_]{3,}", stripped):
        return {"kind": "rule"}

    heading_match = re.match(r"^\s{0,3}(#{1,6})\s+(.*)$", line)
    if heading_match:
        return {"kind": "heading", "text": heading_match.group(2).strip()}

    if re.match(r"^\d+\.\s+\S", stripped) and len(stripped) <= 140:
        return {"kind": "section", "text": stripped}

    bullet_match = re.match(r"^(\s*)[-*•]\s+(.*)$", line)
    if bullet_match:
        return {
            "kind": "bullet",
            "indent": len(bullet_match.group(1)),
            "text": bullet_match.group(2),
        }

    numbered_match = re.match(r"^(\s*)(\d+[.)])\s+(.*)$", line)
    if numbered_match:
        return {
            "kind": "numbered",
            "indent": len(numbered_match.group(1)),
            "label": numbered_match.group(2),
            "text": numbered_match.group(3),
        }

    if line.startswith("    ") or re.fullmatch(r"[0-9xX+\-*/=()., ]{3,}", stripped):
        return {"kind": "mono", "text": line}

    return {"kind": "paragraph", "text": line}


def _last_non_spacer_kind(rows: list[dict[str, Any]]) -> str | None:
    for row in reversed(rows):
        kind = str(row.get("kind") or "")
        if kind != "spacer":
            return kind
    return None


def _strip_bold_markers(text: str) -> tuple[str, bool]:
    normalized = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    has_bold = bool(re.search(r"\*\*(.+?)\*\*", normalized, flags=re.DOTALL))
    normalized = re.sub(r"\*\*(.+?)\*\*", r"\1", normalized, flags=re.DOTALL)
    normalized = re.sub(r"__(.+?)__", r"\1", normalized, flags=re.DOTALL)
    normalized = re.sub(r"`([^`]*)`", r"\1", normalized)
    return normalized, has_bold


def _wrap_text_to_width(
    text: str,
    *,
    draw: Any,
    font: Any,
    max_width: int,
    keep_leading_spaces: bool = False,
) -> list[str]:
    source = text if keep_leading_spaces else text.strip()
    if source == "":
        return [""]

    tokens = re.findall(r"\S+\s*|\s+", source)
    lines: list[str] = []
    current = ""

    for token in tokens:
        candidate = f"{current}{token}"
        if current and _measure_text_width(draw, candidate, font) > max_width:
            lines.append(current.rstrip())
            token_for_new_line = token if keep_leading_spaces else token.lstrip()
            if token_for_new_line:
                if _measure_text_width(draw, token_for_new_line, font) <= max_width:
                    current = token_for_new_line
                else:
                    hard_parts = _hard_wrap_token(token_for_new_line, draw=draw, font=font, max_width=max_width)
                    if hard_parts:
                        lines.extend(hard_parts[:-1])
                        current = hard_parts[-1]
                    else:
                        current = ""
            else:
                current = ""
            continue

        if not current and not keep_leading_spaces:
            token = token.lstrip()
            if not token:
                continue
        current = f"{current}{token}"

    if current:
        lines.append(current.rstrip())
    return lines or [""]


def _hard_wrap_token(token: str, *, draw: Any, font: Any, max_width: int) -> list[str]:
    if not token:
        return []
    result: list[str] = []
    current = ""
    for ch in token:
        candidate = f"{current}{ch}"
        if current and _measure_text_width(draw, candidate, font) > max_width:
            result.append(current)
            current = ch
        else:
            current = candidate
    if current:
        result.append(current)
    return result


def _line_height_for_font(draw: Any, font: Any, *, extra: int) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return max(1, bbox[3] - bbox[1]) + extra + RESPONSE_IMAGE_LINE_SPACING


def _measure_text_width(draw: Any, text: str, font: Any) -> int:
    if not text:
        return 0
    bbox = draw.textbbox((0, 0), text, font=font)
    return max(0, bbox[2] - bbox[0])


def _paginate_rows(rows: list[dict[str, Any]], *, max_content_height: int) -> list[list[dict[str, Any]]]:
    pages: list[list[dict[str, Any]]] = []
    current_page: list[dict[str, Any]] = []
    current_height = 0

    for row in rows:
        row_height = int(row.get("height", 0))
        if current_page and current_height + row_height > max_content_height:
            pages.append(current_page)
            current_page = []
            current_height = 0
        current_page.append(row)
        current_height += row_height

    if current_page:
        pages.append(current_page)

    return pages or [[{"kind": "spacer", "height": 24}]]


async def _build_user_input_payload(
    *,
    message: Message,
    lang: str,
    llm: LLMService,
    provider_id: str,
    api_key: str,
    custom_base_url: str | None,
) -> tuple[dict[str, Any] | None, str | None, str | None, str]:
    text_input = _message_input_text(message)

    if message.photo:
        data_url, error_key = await _download_image_data_url(
            message=message,
            downloadable=message.photo[-1],
            mime_type="image/jpeg",
        )
        if error_key:
            return None, None, error_key, ""
        prompt_text = text_input or t(lang, "media_image_default_prompt")
        history_text = f"[image] {text_input}" if text_input else "[image]"
        return (
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
            history_text,
            None,
            text_input,
        )

    if message.document:
        mime_type = _resolve_image_document_mime(message)
        if not mime_type:
            return None, None, "unsupported_media_type", ""
        data_url, error_key = await _download_image_data_url(
            message=message,
            downloadable=message.document,
            mime_type=mime_type,
        )
        if error_key:
            return None, None, error_key, ""
        prompt_text = text_input or t(lang, "media_image_default_prompt")
        file_name = message.document.file_name or "image"
        history_text = f"[image:{file_name}] {text_input}" if text_input else f"[image:{file_name}]"
        return (
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
            history_text,
            None,
            text_input,
        )

    if message.voice or message.audio or message.video_note:
        downloadable = message.voice or message.audio or message.video_note
        mime_type = _resolve_audio_mime(message) or ("video/mp4" if message.video_note else "audio/ogg")
        if downloadable is None:
            return None, None, "unsupported_media_type", ""
        audio_bytes, error_key = await _download_file_bytes(
            message=message,
            downloadable=downloadable,
            max_bytes=MAX_AUDIO_BYTES,
            too_large_error_key="voice_too_large",
        )
        if error_key:
            return None, None, error_key, ""

        try:
            if message.audio and message.audio.file_name:
                filename = message.audio.file_name
            elif message.video_note:
                filename = "video_note.mp4"
            else:
                filename = "voice.ogg"
            transcript = await llm.transcribe_audio(
                provider_id=provider_id,
                api_key=api_key,
                audio_bytes=audio_bytes,
                filename=filename,
                mime_type=mime_type,
                custom_base_url=custom_base_url,
                language=normalize_language(lang),
            )
        except LLMServiceError:
            return None, None, "voice_transcription_failed", ""

        clean_transcript = transcript.strip()
        if not clean_transcript:
            return None, None, "voice_transcription_failed", ""

        combined_text = clean_transcript
        if text_input:
            combined_text = f"{text_input}\n\n{clean_transcript}"

        if message.video_note:
            history_text = f"[video_note] {clean_transcript}"
        else:
            history_text = f"[voice] {clean_transcript}"
        return {"role": "user", "content": combined_text}, history_text, None, clean_transcript

    if message.video or message.animation:
        return None, None, "unsupported_media_type", ""

    if text_input:
        return {"role": "user", "content": text_input}, text_input, None, text_input

    return None, None, "unsupported_media_type", ""


def _message_input_text(message: Message) -> str:
    return ((message.text or message.caption) or "").strip()


def _resolve_image_document_mime(message: Message) -> str | None:
    document = message.document
    if document is None:
        return None

    mime_type = (document.mime_type or "").strip().lower()
    if mime_type.startswith("image/"):
        return mime_type

    guessed_mime, _ = mimetypes.guess_type(document.file_name or "")
    if guessed_mime and guessed_mime.startswith("image/"):
        return guessed_mime.lower()
    return None


def _resolve_audio_mime(message: Message) -> str | None:
    if message.voice:
        mime_type = (message.voice.mime_type or "").strip().lower()
        return mime_type or "audio/ogg"

    if message.audio:
        mime_type = (message.audio.mime_type or "").strip().lower()
        if mime_type.startswith("audio/"):
            return mime_type
        guessed_mime, _ = mimetypes.guess_type(message.audio.file_name or "")
        if guessed_mime and guessed_mime.startswith("audio/"):
            return guessed_mime.lower()
        return "audio/mpeg"

    if message.video_note:
        mime_type = (getattr(message.video_note, "mime_type", "") or "").strip().lower()
        if mime_type.startswith("video/") or mime_type.startswith("audio/"):
            return mime_type
        return "video/mp4"

    return None


async def _download_file_bytes(
    *,
    message: Message,
    downloadable: Any,
    max_bytes: int,
    too_large_error_key: str,
) -> tuple[bytes | None, str | None]:
    file_size = getattr(downloadable, "file_size", None)
    if isinstance(file_size, int) and file_size > max_bytes:
        return None, too_large_error_key

    buffer = BytesIO()
    try:
        await message.bot.download(downloadable, destination=buffer)
    except Exception:  # noqa: BLE001
        return None, "media_download_failed"

    raw_bytes = buffer.getvalue()
    if not raw_bytes:
        return None, "media_download_failed"
    if len(raw_bytes) > max_bytes:
        return None, too_large_error_key
    return raw_bytes, None


async def _download_image_data_url(
    *,
    message: Message,
    downloadable: Any,
    mime_type: str,
) -> tuple[str | None, str | None]:
    raw_bytes, error_key = await _download_file_bytes(
        message=message,
        downloadable=downloadable,
        max_bytes=MAX_IMAGE_BYTES,
        too_large_error_key="media_too_large",
    )
    if error_key:
        return None, error_key
    if raw_bytes is None:
        return None, "media_download_failed"

    encoded = base64.b64encode(raw_bytes).decode("ascii")
    safe_mime_type = mime_type.strip().lower() or "image/jpeg"
    return f"data:{safe_mime_type};base64,{encoded}", None


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _guess_provider_from_key(api_key: str) -> str | None:
    token = api_key.strip()
    if token.startswith("gsk_"):
        return "groq"
    if token.startswith("sk-or-v1-"):
        return "openrouter"
    if token.startswith("sk-"):
        return "openai"
    if token.startswith("together_"):
        return "together"
    return None


def _humanize_error(*, lang: str, provider_id: str, api_key: str, raw_error: str) -> str:
    compact = raw_error.replace("\n", " ").strip()
    lowered = compact.lower()

    if "incorrect api key provided" in lowered or "invalid_api_key" in lowered:
        base = t(lang, "invalid_api_key", provider=provider_label(provider_id))
    elif "401" in compact:
        base = t(lang, "invalid_api_key", provider=provider_label(provider_id))
    else:
        base = compact

    if len(base) > 220:
        base = base[:217] + "..."

    maybe_provider = _guess_provider_from_key(api_key)
    if maybe_provider and maybe_provider != provider_id and ("401" in compact or "api key" in lowered):
        hint = t(
            lang,
            "provider_mismatch_hint",
            current=provider_label(provider_id),
            suggested=provider_label(maybe_provider),
        )
        return f"{base} {hint}"

    return base


async def _generate_chat_title(
    *,
    llm: LLMService,
    provider_id: str,
    api_key: str,
    model: str | None,
    custom_base_url: str | None,
    language_name: str,
    first_message: str,
) -> str:
    fallback = _fallback_chat_title(first_message)
    try:
        raw_title = await llm.generate_reply(
            provider_id=provider_id,
            api_key=api_key,
            model=model,
            custom_base_url=custom_base_url,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a concise title for this chat.\n"
                        "Rules:\n"
                        "- 2 to 6 words.\n"
                        "- Use the user's language.\n"
                        "- No quotes, no emojis, no markdown, no trailing punctuation.\n"
                        "- Return only the title."
                    ),
                },
                {
                    "role": "user",
                    "content": f"User language: {language_name}\nFirst user message: {first_message}",
                },
            ],
        )
    except LLMServiceError:
        return fallback
    return _normalize_chat_title(raw_title, fallback=fallback)


def _normalize_chat_title(raw_title: str, *, fallback: str) -> str:
    if not raw_title:
        return fallback
    title = raw_title.strip().replace("\n", " ")
    title = re.sub(r"\s+", " ", title)
    title = title.strip(" \"'`.,;:!?-")
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    return title or fallback


def _fallback_chat_title(first_message: str) -> str:
    text = first_message.strip().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    if len(text) > 60:
        text = text[:57].rstrip() + "..."
    return text or "New Chat"


async def _save_api_key_with_auto_provider(
    *,
    db: Database,
    user: UserSettings,
    api_key: str,
) -> tuple[str, bool, str]:
    current_provider = user.provider
    detected_provider = _guess_provider_from_key(api_key) or current_provider
    target_provider = detected_provider if detected_provider in PROVIDERS else current_provider
    auto_switched = target_provider != current_provider

    if auto_switched:
        await db.set_provider(user.user_id, target_provider)

    await db.set_api_key(user.user_id, target_provider, api_key)
    return target_provider, auto_switched, current_provider
