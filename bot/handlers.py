from __future__ import annotations

import base64
import mimetypes
import re
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import Settings
from bot.db import Database, UserSettings
from bot.i18n import LANGUAGE_LABELS, SUPPORTED_LANGUAGES, SUPPORTED_PERSONALITIES, normalize_personality, personality_label, t
from bot.keyboards import (
    cancel_input_keyboard,
    history_keyboard,
    language_keyboard,
    main_menu_keyboard,
    model_preset_keyboard,
    personality_keyboard,
    provider_keyboard,
)
from bot.llm.providers import PROVIDERS, provider_label
from bot.llm.service import LLMService, LLMServiceError
from bot.markdown import escape_markdown_v2, render_llm_markdown_v2
from bot.states import SetupStates

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
}

MAX_IMAGE_BYTES = 8 * 1024 * 1024
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

DEFAULT_SHARED_MODEL_ID = "llama3"
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

    def _md(lang: str, key: str, **kwargs: str) -> str:
        return escape_markdown_v2(t(lang, key, **kwargs))

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

    async def _system_prompt_for(*, user_id: int, lang: str, personality: str) -> str:
        base_prompt = t(
            lang,
            "system_prompt",
            language_name=LANGUAGE_LABELS.get(lang, "English"),
        )
        formatting_guardrail = (
            "Formatting: do not use LaTeX commands like \\cdot, \\frac, \\sqrt, \\begin, \\end. "
            "Write formulas in plain text with Unicode symbols (for example: ·, ×, ÷, ≤, ≥, √)."
        )
        if personality.startswith("custom_"):
            custom = await db.get_custom_personality(user_id, personality)
            if custom:
                return (
                    f"{base_prompt}\n"
                    f"{formatting_guardrail}\n"
                    "Role: custom persona from user instructions.\n"
                    f"Follow these custom instructions:\n{custom.instructions}"
                )
        normalized_personality = normalize_personality(personality)
        personality_prompt = PERSONALITY_PROMPTS.get(normalized_personality, PERSONALITY_PROMPTS["default"])
        return f"{base_prompt}\n{formatting_guardrail}\n{personality_prompt}"

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
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        await message.answer(
            _md(lang, "welcome"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
        )

    @router.message(Command("menu"))
    async def on_menu(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        await _show_menu(message, lang)

    @router.message(Command("help"))
    async def on_help(message: Message) -> None:
        if message.from_user is None:
            return
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return
        await message.answer(
            _md(lang, "help"),
            reply_markup=main_menu_keyboard(lang),
            parse_mode="MarkdownV2",
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

    @router.message(Command("language"))
    async def on_language(message: Message, command: CommandObject) -> None:
        if message.from_user is None:
            return
        await db.ensure_user(message.from_user.id)
        lang = await _user_lang(message.from_user.id)
        if await _deny_if_not_private(message, lang):
            return

        raw = (command.args or "").strip().lower() if command else ""
        if raw:
            if raw not in SUPPORTED_LANGUAGES:
                await message.answer(
                    _md(lang, "choose_language"),
                    reply_markup=language_keyboard(language=lang, with_back=True),
                    parse_mode="MarkdownV2",
                )
                return
            await db.set_language(message.from_user.id, raw)
            await message.answer(
                _md(raw, "language_changed", language=LANGUAGE_LABELS[raw]),
                reply_markup=main_menu_keyboard(raw),
                parse_mode="MarkdownV2",
            )
            return

        await message.answer(
            _md(lang, "choose_language"),
            reply_markup=language_keyboard(language=lang, with_back=True),
            parse_mode="MarkdownV2",
        )

    @router.callback_query(F.data.startswith("lang:"))
    async def on_language_callback(query: CallbackQuery) -> None:
        if query.from_user is None:
            return
        lang_code = query.data.split(":", maxsplit=1)[1].strip().lower()
        if lang_code not in SUPPORTED_LANGUAGES:
            user_lang = await _user_lang(query.from_user.id)
            await query.answer(t(user_lang, "unsupported_language"), show_alert=True)
            return

        await db.set_language(query.from_user.id, lang_code)
        await query.answer()
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

        raw = (command.args or "").strip().lower() if command else ""
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

        raw = (command.args or "").strip().lower() if command and command.args else ""
        if raw:
            if raw not in SUPPORTED_PERSONALITIES:
                custom_items = await _custom_personality_items(message.from_user.id)
                await message.answer(
                    _md(lang, "choose_personality"),
                    reply_markup=personality_keyboard(language=lang, custom_personalities=custom_items, with_back=True),
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
            reply_markup=personality_keyboard(language=lang, custom_personalities=custom_items, with_back=True),
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
            _md(lang, "ask_api_key", provider=provider_label(user.provider)),
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

        raw = (command.args or "").strip().lower() if command else ""
        if not user.use_personal_api:
            if raw:
                if raw in {"own", "own_api", "personal", "myapi"}:
                    await db.set_use_personal_api(message.from_user.id, True)
                    await message.answer(
                        _md(lang, "model_personal_api_enabled"),
                        reply_markup=main_menu_keyboard(lang),
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
        text, lang = await _render_settings(message.from_user.id)
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
            await state.clear()
            await query.answer()
            await _safe_edit(query, _md(lang, "model_personal_api_enabled"), lang=lang)
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
            text, lang = await _render_settings(query.from_user.id)
            await query.answer()
            await _safe_edit(query, text, lang=lang)
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
                        _md(lang, "choose_language"),
                        reply_markup=language_keyboard(language=lang, with_back=True),
                        parse_mode="MarkdownV2",
                    )
                except TelegramBadRequest:
                    await query.message.answer(
                        _md(lang, "choose_language"),
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
                            page=page,
                            with_back=True,
                        ),
                        parse_mode="MarkdownV2",
                    )
            return

        if data == "menu:custom_instructions":
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
                    _md(lang, "ask_api_key", provider=provider_label(user.provider)),
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
        if await state.get_state() is not None:
            return
        user = await db.get_user_settings(message.from_user.id)
        lang = user.language
        if await _deny_if_not_private(message, lang):
            return

        user_payload, user_content_for_history, media_error_key = await _build_user_input_payload(
            message=message,
            lang=lang,
        )
        if media_error_key:
            extra: dict[str, str] = {}
            if media_error_key == "media_too_large":
                extra["max_mb"] = str(MAX_IMAGE_BYTES // (1024 * 1024))
            await message.answer(
                _md(lang, media_error_key, **extra),
                reply_markup=main_menu_keyboard(lang),
                parse_mode="MarkdownV2",
            )
            return
        if user_payload is None or user_content_for_history is None:
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

        if api_key is None:
            await message.answer(
                _md(lang, "shared_ai_not_configured"),
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

        history = await db.get_recent_messages(
            message.from_user.id,
            settings.memory_messages,
            chat_id=chat_id,
        )
        if history:
            history[-1] = user_payload
        else:
            history = [user_payload]
        system_prompt = await _system_prompt_for(
            user_id=message.from_user.id,
            lang=lang,
            personality=user.personality,
        )
        context = [
            {
                "role": "system",
                "content": system_prompt,
            },
            *history,
        ]

        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        try:
            response = await llm.generate_reply(
                provider_id=provider_id,
                api_key=api_key,
                model=selected_model,
                messages=context,
                custom_base_url=custom_base_url,
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
            shared_total_cost = shared_input_cost + _estimate_shared_output_cost(
                model_id=shared_model_id,
                text=response,
            )
            await db.add_quota_used(message.from_user.id, shared_total_cost)

        await db.add_message(message.from_user.id, "assistant", response, chat_id=chat_id)
        await _send_assistant_response(
            message=message,
            response=response,
            lang=lang,
        )

    return router


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


async def _send_assistant_response(*, message: Message, response: str, lang: str) -> None:
    display_response = _prepare_response_for_display(response)

    if _should_send_response_as_image(response):
        if await _send_response_as_image(message=message, response=display_response, lang=lang):
            return

    try:
        for chunk in _split_message(display_response):
            escaped_chunk = render_llm_markdown_v2(chunk, parse_mode="MarkdownV2")
            await message.answer(escaped_chunk, parse_mode="MarkdownV2")
        return
    except TelegramBadRequest:
        # If MarkdownV2 formatting fails, retry with image to preserve full content.
        if await _send_response_as_image(message=message, response=display_response, lang=lang):
            return

    for chunk in _split_message(display_response):
        await message.answer(chunk)


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


async def _send_response_as_image(*, message: Message, response: str, lang: str) -> bool:
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
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    text_input = _message_input_text(message)

    if message.photo:
        data_url, error_key = await _download_image_data_url(
            message=message,
            downloadable=message.photo[-1],
            mime_type="image/jpeg",
        )
        if error_key:
            return None, None, error_key
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
        )

    if message.document:
        mime_type = _resolve_image_document_mime(message)
        if not mime_type:
            return None, None, "unsupported_media_type"
        data_url, error_key = await _download_image_data_url(
            message=message,
            downloadable=message.document,
            mime_type=mime_type,
        )
        if error_key:
            return None, None, error_key
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
        )

    if message.video or message.audio or message.voice or message.animation or message.video_note:
        return None, None, "unsupported_media_type"

    if text_input:
        return {"role": "user", "content": text_input}, text_input, None

    return None, None, "unsupported_media_type"


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


async def _download_image_data_url(
    *,
    message: Message,
    downloadable: Any,
    mime_type: str,
) -> tuple[str | None, str | None]:
    file_size = getattr(downloadable, "file_size", None)
    if isinstance(file_size, int) and file_size > MAX_IMAGE_BYTES:
        return None, "media_too_large"

    buffer = BytesIO()
    try:
        await message.bot.download(downloadable, destination=buffer)
    except Exception:  # noqa: BLE001
        return None, "media_download_failed"

    raw_bytes = buffer.getvalue()
    if not raw_bytes:
        return None, "media_download_failed"
    if len(raw_bytes) > MAX_IMAGE_BYTES:
        return None, "media_too_large"

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
