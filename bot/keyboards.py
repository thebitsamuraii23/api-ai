from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.i18n import SUPPORTED_PERSONALITIES, LANGUAGE_LABELS, SUPPORTED_LANGUAGES, personality_label, t
from bot.llm.providers import PROVIDERS, provider_label


def model_preset_keyboard(*, language: str, active_model: str, personal_api_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = [
        ("gpt4", t(language, "model_gpt4")),
        ("llama3", t(language, "model_llama3")),
        ("llama4_media", t(language, "model_llama4_media")),
    ]
    for model_id, label in items:
        prefix = "✅ " if (not personal_api_enabled and active_model == model_id) else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"modelpreset:{model_id}")

    own_api_prefix = "✅ " if personal_api_enabled else ""
    builder.button(text=f"{own_api_prefix}{t(language, 'btn_own_api')}", callback_data="modelpreset:own_api")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()


def language_keyboard(
    *,
    language: str | None = None,
    with_back: bool = False,
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lang in SUPPORTED_LANGUAGES:
        builder.button(text=LANGUAGE_LABELS[lang], callback_data=f"lang:{lang}")
    if with_back:
        back_label = t(language, "btn_back") if language else "⬅️ Back"
        builder.button(text=back_label, callback_data=back_callback)
    builder.adjust(2)
    return builder.as_markup()


def provider_keyboard(
    *,
    language: str | None = None,
    with_back: bool = False,
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for provider in PROVIDERS.values():
        builder.button(text=provider_label(provider.id), callback_data=f"provider:{provider.id}")
    if with_back:
        back_label = t(language, "btn_back") if language else "⬅️ Back"
        builder.button(text=back_label, callback_data=back_callback)
    builder.adjust(2)
    return builder.as_markup()


def main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_settings"), callback_data="menu:settings")
    builder.button(text=t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text=t(language, "btn_provider"), callback_data="menu:provider")
    builder.button(text=t(language, "btn_language"), callback_data="menu:language")
    builder.button(text=t(language, "btn_personality"), callback_data="menu:personality")
    builder.button(text=t(language, "btn_apikey"), callback_data="menu:apikey")
    builder.button(text=t(language, "btn_model"), callback_data="menu:model")
    builder.button(text=t(language, "btn_baseurl"), callback_data="menu:baseurl")
    builder.button(text=t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def personality_keyboard(
    *,
    language: str,
    custom_personalities: list[tuple[str, str]] | None = None,
    page: int = 0,
    page_size: int = 10,
    with_back: bool = False,
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    all_personalities: list[tuple[str, str]] = [
        (f"personality:{personality}", personality_label(language, personality))
        for personality in SUPPORTED_PERSONALITIES
    ]
    all_personalities.extend(
        (f"personality:{personality_id}", f"🧾 {personality_title}")
        for personality_id, personality_title in (custom_personalities or [])
    )

    total_items = len(all_personalities)
    if total_items == 0:
        safe_page = 0
        total_pages = 1
        page_items: list[tuple[str, str]] = []
    else:
        total_pages = (total_items + page_size - 1) // page_size
        safe_page = min(max(page, 0), total_pages - 1)
        start = safe_page * page_size
        end = start + page_size
        page_items = all_personalities[start:end]

    layout: list[int] = []
    for callback_data, text in page_items:
        builder.button(text=text, callback_data=callback_data)
        layout.append(1)

    if total_pages > 1:
        nav_count = 0
        if safe_page > 0:
            builder.button(text="⬅️", callback_data=f"menu:personality:page:{safe_page - 1}")
            nav_count += 1
        builder.button(text=f"{safe_page + 1}/{total_pages}", callback_data="menu:noop")
        nav_count += 1
        if safe_page < total_pages - 1:
            builder.button(text="➡️", callback_data=f"menu:personality:page:{safe_page + 1}")
            nav_count += 1
        layout.append(nav_count)

    builder.button(text=t(language, "btn_custom_instructions"), callback_data="menu:custom_instructions")
    layout.append(1)
    if with_back:
        builder.button(text=t(language, "btn_back"), callback_data=back_callback)
        layout.append(1)

    builder.adjust(*layout)
    return builder.as_markup()


def history_keyboard(*, language: str, page: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    layout: list[int] = []
    if total > 1:
        nav_count = 0
        if page > 0:
            builder.button(text="⬅️", callback_data=f"menu:history:{page - 1}")
            nav_count += 1
        builder.button(text=f"{page + 1}/{total}", callback_data="menu:noop")
        nav_count += 1
        if page < total - 1:
            builder.button(text="➡️", callback_data=f"menu:history:{page + 1}")
            nav_count += 1
        layout.append(nav_count)
    builder.button(text=t(language, "btn_open_chat"), callback_data=f"menu:openchat:{page}")
    builder.button(text=t(language, "btn_delete_chat"), callback_data=f"menu:deletechat:{page}")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    layout.append(3)
    builder.adjust(*layout)
    return builder.as_markup()


def cancel_input_keyboard(*, language: str, callback_data: str = "menu:cancel") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_cancel"), callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def quick_model_selection_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Быстрый выбор модели для shared AI."""
    builder = InlineKeyboardBuilder()
    models = [
        ("llama3", "🦙 Llama 3"),
        ("gpt4", "🧠 GPT-4"),
        ("llama4_media", "🎬 Llama 4 Media"),
    ]
    for model_id, label in models:
        builder.button(text=label, callback_data=f"modelpreset:{model_id}")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def personality_quick_keyboard(
    *,
    language: str,
    custom_personalities: list[tuple[str, str]] | None = None,
) -> InlineKeyboardMarkup:
    """Быстрый выбор личности со стандартными вариантами."""
    builder = InlineKeyboardBuilder()
    
    # Quick personality selection
    quick_personalities = [
        ("default", "🤖 Default"),
        ("teacher", "👨‍🏫 Teacher"),
        ("creative", "🎨 Creative"),
        ("technical", "⚙️ Technical"),
    ]
    
    for personality_id, label in quick_personalities:
        callback = f"personality:{personality_id}"
        builder.button(text=label, callback_data=callback)
    
    # Custom personalities if available
    if custom_personalities:
        for personality_id, title in custom_personalities[:3]:  # Show first 3 custom
            builder.button(text=f"🧾 {title}", callback_data=f"personality:{personality_id}")
    
    builder.button(text="📋 " + t(language, "btn_personality"), callback_data="menu:personality")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 2)
    return builder.as_markup()


def new_chat_confirm_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Подтверждение создания нового чата."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ " + t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text="❌ " + t(language, "btn_cancel"), callback_data="menu:home")
    builder.adjust(1, 1)
    return builder.as_markup()


def settings_quick_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Быстрая навигация по основным настройкам."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 " + t(language, "btn_provider"), callback_data="menu:provider")
    builder.button(text="🎭 " + t(language, "btn_personality"), callback_data="menu:personality")
    builder.button(text="💾 " + t(language, "btn_model"), callback_data="menu:model")
    builder.button(text="🔑 " + t(language, "btn_apikey"), callback_data="menu:apikey")
    builder.button(text="🌐 " + t(language, "btn_language"), callback_data="menu:language")
    builder.button(text="🔗 " + t(language, "btn_baseurl"), callback_data="menu:baseurl")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def chat_actions_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Действия с чатом и быстрый доступ."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 " + t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text="📜 " + t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text="⚙️ " + t(language, "btn_settings"), callback_data="menu:settings")
    builder.button(text="🏠 Home", callback_data="menu:home")
    builder.adjust(2, 2)
    return builder.as_markup()


def provider_with_shared_keyboard(
    *,
    language: str,
    show_shared: bool = True,
    with_back: bool = False,
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    """Выбор провайдера с выделением shared AI."""
    builder = InlineKeyboardBuilder()
    
    # Show Shared AI first if enabled
    if show_shared:
        builder.button(text="🤖 Shared AI", callback_data="provider:shared_ai")
    
    # Other providers
    for provider in PROVIDERS.values():
        if provider.id != "shared_ai":  # Skip shared_ai as it's already added
            builder.button(text=provider_label(provider.id), callback_data=f"provider:{provider.id}")
    
    if with_back:
        back_label = t(language, "btn_back") if language else "⬅️ Back"
        builder.button(text=back_label, callback_data=back_callback)
    
    builder.adjust(2)
    return builder.as_markup()


def main_menu_horizontal_keyboard(language: str) -> InlineKeyboardMarkup:
    """Горизонтальное меню с основными функциями."""
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 " + t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text="📜 " + t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text="⚙️ " + t(language, "btn_settings"), callback_data="menu:settings")
    builder.button(text="🏠 " + t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 2)
    return builder.as_markup()


def api_mode_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Выбор между личным API и shared."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 Shared AI", callback_data="modelpreset:llama3")
    builder.button(text="🔑 Own API Key", callback_data="modelpreset:own_api")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(1, 1, 1)
    return builder.as_markup()


def language_quick_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Быстрый выбор языка с основными вариантами."""
    builder = InlineKeyboardBuilder()
    
    # Most common languages
    quick_langs = ["en", "ru", "es", "fr"]
    for lang_code in quick_langs:
        if lang_code in LANGUAGE_LABELS:
            prefix = "✅ " if lang_code == language else ""
            builder.button(
                text=f"{prefix}{LANGUAGE_LABELS[lang_code]}",
                callback_data=f"lang:{lang_code}"
            )
    
    builder.button(text="🌐 " + t(language, "btn_language"), callback_data="menu:language")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 1, 1)
    return builder.as_markup()
