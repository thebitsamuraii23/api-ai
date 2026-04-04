from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.i18n import SUPPORTED_PERSONALITIES, LANGUAGE_LABELS, SUPPORTED_LANGUAGES, normalize_language, personality_label, t
from bot.llm.providers import PROVIDERS, provider_label

_SETTINGS_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "model": "🤖 Model",
        "provider": "🔌 Provider",
        "personality": "🎭 Role",
        "language": "🌐 Language",
        "apikey": "🔐 API key",
        "baseurl": "🔗 Base URL",
        "instructions": "🧾 Instructions",
        "tokens": "🧮 Tokens",
        "history": "🗂️ History",
        "newchat": "🆕 New chat",
        "close": "🏠 Close",
        "realtime": "⚡ Realtime",
        "realtime_on": "⚡ Realtime: ON",
        "realtime_off": "⚡ Realtime: OFF",
    },
    "ru": {
        "model": "🤖 Модель",
        "provider": "🔌 Провайдер",
        "personality": "🎭 Роль",
        "language": "🌐 Язык",
        "apikey": "🔐 API-ключ",
        "baseurl": "🔗 Base URL",
        "instructions": "🧾 Инструкции",
        "tokens": "🧮 Токены",
        "history": "🗂️ История",
        "newchat": "🆕 Новый чат",
        "close": "🏠 Закрыть",
        "realtime": "⚡ Реал-тайм",
        "realtime_on": "⚡ Реал-тайм: ВКЛ",
        "realtime_off": "⚡ Реал-тайм: ВЫКЛ",
    },
    "es": {
        "model": "🤖 Modelo",
        "provider": "🔌 Proveedor",
        "personality": "🎭 Rol",
        "language": "🌐 Idioma",
        "apikey": "🔐 Clave API",
        "baseurl": "🔗 URL base",
        "instructions": "🧾 Instrucciones",
        "tokens": "🧮 Tokens",
        "history": "🗂️ Historial",
        "newchat": "🆕 Nuevo chat",
        "close": "🏠 Cerrar",
        "realtime": "⚡ Tiempo real",
        "realtime_on": "⚡ Tiempo real: ACTIVADO",
        "realtime_off": "⚡ Tiempo real: DESACTIVADO",
    },
    "fr": {
        "model": "🤖 Modèle",
        "provider": "🔌 Fournisseur",
        "personality": "🎭 Rôle",
        "language": "🌐 Langue",
        "apikey": "🔐 Clé API",
        "baseurl": "🔗 URL de base",
        "instructions": "🧾 Instructions",
        "tokens": "🧮 Tokens",
        "history": "🗂️ Historique",
        "newchat": "🆕 Nouveau chat",
        "close": "🏠 Fermer",
        "realtime": "⚡ Temps réel",
        "realtime_on": "⚡ Temps réel: ACTIVÉ",
        "realtime_off": "⚡ Temps réel: DÉSACTIVÉ",
    },
    "tr": {
        "model": "🤖 Model",
        "provider": "🔌 Sağlayıcı",
        "personality": "🎭 Rol",
        "language": "🌐 Dil",
        "apikey": "🔐 API anahtarı",
        "baseurl": "🔗 Temel URL",
        "instructions": "🧾 Talimatlar",
        "tokens": "🧮 Tokenler",
        "history": "🗂️ Geçmiş",
        "newchat": "🆕 Yeni sohbet",
        "close": "🏠 Kapat",
        "realtime": "⚡ Gerçek zaman",
        "realtime_on": "⚡ Gerçek zaman: AÇIK",
        "realtime_off": "⚡ Gerçek zaman: KAPALI",
    },
    "ar": {
        "model": "🤖 النموذج",
        "provider": "🔌 المزود",
        "personality": "🎭 الدور",
        "language": "🌐 اللغة",
        "apikey": "🔐 مفتاح API",
        "baseurl": "🔗 الرابط الأساسي",
        "instructions": "🧾 التعليمات",
        "tokens": "🧮 التوكنات",
        "history": "🗂️ السجل",
        "newchat": "🆕 دردشة جديدة",
        "close": "🏠 إغلاق",
        "realtime": "⚡ فوري",
        "realtime_on": "⚡ فوري: تشغيل",
        "realtime_off": "⚡ فوري: إيقاف",
    },
    "de": {
        "model": "🤖 Modell",
        "provider": "🔌 Anbieter",
        "personality": "🎭 Rolle",
        "language": "🌐 Sprache",
        "apikey": "🔐 API-Schlüssel",
        "baseurl": "🔗 Base URL",
        "instructions": "🧾 Anweisungen",
        "tokens": "🧮 Tokens",
        "history": "🗂️ Verlauf",
        "newchat": "🆕 Neuer Chat",
        "close": "🏠 Schließen",
        "realtime": "⚡ Echtzeit",
        "realtime_on": "⚡ Echtzeit: AN",
        "realtime_off": "⚡ Echtzeit: AUS",
    },
    "it": {
        "model": "🤖 Modello",
        "provider": "🔌 Provider",
        "personality": "🎭 Ruolo",
        "language": "🌐 Lingua",
        "apikey": "🔐 Chiave API",
        "baseurl": "🔗 URL base",
        "instructions": "🧾 Istruzioni",
        "tokens": "🧮 Token",
        "history": "🗂️ Cronologia",
        "newchat": "🆕 Nuova chat",
        "close": "🏠 Chiudi",
        "realtime": "⚡ Tempo reale",
        "realtime_on": "⚡ Tempo reale: ATTIVO",
        "realtime_off": "⚡ Tempo reale: DISATTIVO",
    },
    "pt": {
        "model": "🤖 Modelo",
        "provider": "🔌 Provedor",
        "personality": "🎭 Papel",
        "language": "🌐 Idioma",
        "apikey": "🔐 Chave API",
        "baseurl": "🔗 URL base",
        "instructions": "🧾 Instruções",
        "tokens": "🧮 Tokens",
        "history": "🗂️ Histórico",
        "newchat": "🆕 Novo chat",
        "close": "🏠 Fechar",
        "realtime": "⚡ Tempo real",
        "realtime_on": "⚡ Tempo real: ATIVADO",
        "realtime_off": "⚡ Tempo real: DESATIVADO",
    },
    "uk": {
        "model": "🤖 Модель",
        "provider": "🔌 Провайдер",
        "personality": "🎭 Роль",
        "language": "🌐 Мова",
        "apikey": "🔐 API-ключ",
        "baseurl": "🔗 Базовий URL",
        "instructions": "🧾 Інструкції",
        "tokens": "🧮 Токени",
        "history": "🗂️ Історія",
        "newchat": "🆕 Новий чат",
        "close": "🏠 Закрити",
        "realtime": "⚡ Реальний час",
        "realtime_on": "⚡ Реальний час: УВІМК.",
        "realtime_off": "⚡ Реальний час: ВИМК.",
    },
    "hi": {
        "model": "🤖 मॉडल",
        "provider": "🔌 प्रोवाइडर",
        "personality": "🎭 भूमिका",
        "language": "🌐 भाषा",
        "apikey": "🔐 API key",
        "baseurl": "🔗 Base URL",
        "instructions": "🧾 निर्देश",
        "tokens": "🧮 टोकन",
        "history": "🗂️ इतिहास",
        "newchat": "🆕 नई चैट",
        "close": "🏠 बंद करें",
        "realtime": "⚡ रियल-टाइम",
        "realtime_on": "⚡ रियल-टाइम: चालू",
        "realtime_off": "⚡ रियल-टाइम: बंद",
    },
}

_MENU_ORIGINS = {"menu", "settings"}


def _normalize_menu_origin(origin: str | None, *, default: str = "menu") -> str:
    candidate = (origin or "").strip().lower()
    if candidate in _MENU_ORIGINS:
        return candidate
    return default


def model_preset_keyboard(
    *,
    language: str,
    active_model: str,
    personal_api_enabled: bool,
    origin: str = "menu",
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    safe_origin = _normalize_menu_origin(origin, default="menu")
    builder = InlineKeyboardBuilder()
    items = [
        ("gpt4", t(language, "model_gpt4")),
        ("llama4_media", t(language, "model_llama4_media")),
        ("llama3", t(language, "model_llama3")),
        ("groq_compound", t(language, "model_groq_compound")),
    ]
    for model_id, label in items:
        prefix = "✅ " if (not personal_api_enabled and active_model == model_id) else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"modelpreset:{model_id}:{safe_origin}")

    own_api_prefix = "✅ " if personal_api_enabled else ""
    builder.button(text=f"{own_api_prefix}{t(language, 'btn_own_api')}", callback_data=f"modelpreset:own_api:{safe_origin}")
    builder.button(text=t(language, "btn_back"), callback_data=back_callback)
    builder.adjust(1, 1, 1, 1, 1, 1)
    return builder.as_markup()


def language_keyboard(
    *,
    language: str | None = None,
    with_back: bool = False,
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    current_lang = normalize_language(language) if language else None
    is_ru = normalize_language(language or "en") == "ru"
    builder = InlineKeyboardBuilder()
    layout: list[int] = []

    if current_lang in LANGUAGE_LABELS:
        current_text = LANGUAGE_LABELS[current_lang]
        badge = f"✅ Текущий: {current_text}" if is_ru else f"✅ Current: {current_text}"
        builder.button(text=badge, callback_data="menu:noop")
        layout.append(1)

    for lang_code in SUPPORTED_LANGUAGES:
        prefix = "✅ " if lang_code == current_lang else "▫️ "
        label = LANGUAGE_LABELS.get(lang_code, lang_code)
        builder.button(text=f"{prefix}{label}", callback_data=f"lang:{lang_code}")

    full_rows = len(SUPPORTED_LANGUAGES) // 2
    layout.extend([2] * full_rows)
    if len(SUPPORTED_LANGUAGES) % 2:
        layout.append(1)

    if with_back:
        back_label = ("⬅️ Назад" if is_ru else "⬅️ Back") if not language else t(language, "btn_back")
        builder.button(text=back_label, callback_data=back_callback)
        layout.append(1)

    builder.adjust(*layout)
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
    builder.button(text=t(language, "btn_personality"), callback_data="menu:personality:menu")
    builder.button(text=t(language, "btn_apikey"), callback_data="menu:apikey:menu")
    builder.button(text=t(language, "btn_model"), callback_data="menu:model:menu")
    builder.button(text=t(language, "btn_baseurl"), callback_data="menu:baseurl:menu")
    builder.button(text=t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def settings_keyboard(language: str, *, realtime_answers_enabled: bool | None = None) -> InlineKeyboardMarkup:
    labels = _SETTINGS_LABELS.get(normalize_language(language), _SETTINGS_LABELS["en"])
    builder = InlineKeyboardBuilder()
    builder.button(text=labels["model"], callback_data="menu:model:settings")
    builder.button(text=labels["provider"], callback_data="menu:provider:settings")
    builder.button(text=labels["personality"], callback_data="menu:personality:settings")
    builder.button(text=labels["language"], callback_data="menu:language:settings")
    builder.button(text=labels["apikey"], callback_data="menu:apikey:settings")
    builder.button(text=labels["baseurl"], callback_data="menu:baseurl:settings")
    builder.button(text=labels["instructions"], callback_data="menu:custom_instructions:manage:settings")
    builder.button(text=labels["tokens"], callback_data="menu:limit:settings")
    if realtime_answers_enabled is None:
        realtime_label = labels["realtime"]
    elif realtime_answers_enabled:
        realtime_label = labels["realtime_on"]
    else:
        realtime_label = labels["realtime_off"]
    builder.button(text=realtime_label, callback_data="menu:realtime_answers:toggle")
    builder.button(text=labels["history"], callback_data="menu:history:settings:0")
    builder.button(text=labels["newchat"], callback_data="menu:newchat")
    builder.button(text=labels["close"], callback_data="menu:home")
    builder.adjust(2, 2, 2, 2, 1, 2, 1)
    return builder.as_markup()


def reply_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Постоянная reply-клавиатура с основными командами."""
    def _label(label_key: str) -> KeyboardButton:
        return KeyboardButton(text=t(language, label_key))

    rows = [
        [_label("btn_model"), _label("btn_history")],
        [_label("btn_settings"), _label("btn_personality")],
        [_label("btn_newchat"), _label("btn_limit")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder=t(language, "menu_title"),
    )

def custom_instructions_manage_keyboard(
    *,
    language: str,
    custom_personalities: list[tuple[str, str]] | None = None,
    origin: str = "settings",
    page: int = 0,
    page_size: int = 10,
    with_back: bool = True,
    back_callback: str = "menu:settings",
) -> InlineKeyboardMarkup:
    safe_origin = _normalize_menu_origin(origin, default="settings")
    items = custom_personalities or []
    builder = InlineKeyboardBuilder()
    total_items = len(items)

    if total_items == 0:
        safe_page = 0
        total_pages = 1
        page_items: list[tuple[str, str]] = []
    else:
        total_pages = (total_items + page_size - 1) // page_size
        safe_page = min(max(page, 0), total_pages - 1)
        start = safe_page * page_size
        end = start + page_size
        page_items = items[start:end]

    layout: list[int] = []
    for personality_id, title in page_items:
        builder.button(text=f"🧾 {title}", callback_data=f"customedit:{personality_id}:{safe_origin}")
        layout.append(1)

    if total_pages > 1:
        nav_count = 0
        if safe_page > 0:
            builder.button(text="⬅️", callback_data=f"menu:custom_instructions:manage:{safe_origin}:page:{safe_page - 1}")
            nav_count += 1
        builder.button(text=f"{safe_page + 1}/{total_pages}", callback_data="menu:noop")
        nav_count += 1
        if safe_page < total_pages - 1:
            builder.button(text="➡️", callback_data=f"menu:custom_instructions:manage:{safe_origin}:page:{safe_page + 1}")
            nav_count += 1
        layout.append(nav_count)

    builder.button(text=t(language, "btn_custom_instructions_new"), callback_data=f"menu:custom_instructions:new:{safe_origin}")
    layout.append(1)

    if with_back:
        builder.button(text=t(language, "btn_back"), callback_data=back_callback)
        layout.append(1)

    builder.adjust(*layout)
    return builder.as_markup()


def custom_instructions_edit_keyboard(
    *,
    language: str,
    personality_id: str,
    origin: str = "settings",
    manage_callback: str | None = None,
) -> InlineKeyboardMarkup:
    safe_origin = _normalize_menu_origin(origin, default="settings")
    manage_cb = manage_callback or f"menu:custom_instructions:manage:{safe_origin}"
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_edit_custom_instructions_text"), callback_data=f"customedittext:{personality_id}:{safe_origin}")
    builder.button(text=t(language, "btn_edit_custom_instructions_name"), callback_data=f"customrename:{personality_id}:{safe_origin}")
    builder.button(text=t(language, "btn_delete_custom_instructions"), callback_data=f"customdelete:{personality_id}:{safe_origin}")
    builder.button(text=t(language, "btn_back"), callback_data=manage_cb)
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def custom_instructions_delete_confirm_keyboard(*, language: str, personality_id: str, origin: str = "settings") -> InlineKeyboardMarkup:
    safe_origin = _normalize_menu_origin(origin, default="settings")
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_confirm_delete"), callback_data=f"customdelete_confirm:{personality_id}:{safe_origin}")
    builder.button(text=t(language, "btn_cancel"), callback_data=f"customdelete_cancel:{personality_id}:{safe_origin}")
    builder.adjust(1, 1)
    return builder.as_markup()


def personality_keyboard(
    *,
    language: str,
    custom_personalities: list[tuple[str, str]] | None = None,
    active_personality: str | None = None,
    page: int = 0,
    page_size: int = 10,
    with_back: bool = False,
    back_callback: str = "menu:home",
    callback_prefix: str = "menu:personality",
    custom_instructions_callback: str = "menu:custom_instructions:manage",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    active = (active_personality or "").strip().lower()
    all_personalities: list[tuple[str, str]] = []
    for personality in SUPPORTED_PERSONALITIES:
        label = personality_label(language, personality)
        if personality == active:
            label = f"✅ {label}"
        all_personalities.append((f"personality:{personality}", label))

    for personality_id, personality_title in (custom_personalities or []):
        label = f"🧾 {personality_title}"
        if personality_id == active:
            label = f"✅ {label}"
        all_personalities.append((f"personality:{personality_id}", label))

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
            builder.button(text="⬅️", callback_data=f"{callback_prefix}:page:{safe_page - 1}")
            nav_count += 1
        builder.button(text=f"{safe_page + 1}/{total_pages}", callback_data="menu:noop")
        nav_count += 1
        if safe_page < total_pages - 1:
            builder.button(text="➡️", callback_data=f"{callback_prefix}:page:{safe_page + 1}")
            nav_count += 1
        layout.append(nav_count)

    builder.button(text=t(language, "btn_custom_instructions"), callback_data=custom_instructions_callback)
    layout.append(1)
    if with_back:
        builder.button(text=t(language, "btn_back"), callback_data=back_callback)
        layout.append(1)

    builder.adjust(*layout)
    return builder.as_markup()


def history_keyboard(
    *,
    language: str,
    page: int,
    total: int,
    callback_prefix: str = "menu:history",
    openchat_prefix: str = "menu:openchat",
    deletechat_prefix: str = "menu:deletechat",
    back_callback: str = "menu:home",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    layout: list[int] = []
    if total > 1:
        nav_count = 0
        if page > 0:
            builder.button(text="⬅️", callback_data=f"{callback_prefix}:{page - 1}")
            nav_count += 1
        builder.button(text=f"{page + 1}/{total}", callback_data="menu:noop")
        nav_count += 1
        if page < total - 1:
            builder.button(text="➡️", callback_data=f"{callback_prefix}:{page + 1}")
            nav_count += 1
        layout.append(nav_count)
    builder.button(text=t(language, "btn_open_chat"), callback_data=f"{openchat_prefix}:{page}")
    builder.button(text=t(language, "btn_delete_chat"), callback_data=f"{deletechat_prefix}:{page}")
    builder.button(text=t(language, "btn_back"), callback_data=back_callback)
    layout.append(3)
    builder.adjust(*layout)
    return builder.as_markup()


def cancel_input_keyboard(*, language: str, callback_data: str = "menu:cancel") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_cancel"), callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def sources_keyboard(*, token: str, language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_sources"), callback_data=f"sources:{token}")
    builder.adjust(1)
    return builder.as_markup()


def sources_close_keyboard(*, token: str, language: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_close_sources"), callback_data=f"sources_close:{token}")
    builder.adjust(1)
    return builder.as_markup()


def use_bot_ai_keyboard(*, language: str, callback_data: str = "model:use_bot_ai") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t(language, "btn_use_bot_ai"), callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def history_button_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Кнопка для открытия истории чатов."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 " + t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(1, 1)
    return builder.as_markup()


def history_menu_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Меню для работы с историей чатов."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📜 " + t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text="📝 " + t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text="⚙️ " + t(language, "btn_settings"), callback_data="menu:settings")
    builder.button(text="🏠 " + t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 2)
    return builder.as_markup()


def history_navigation_keyboard(*, language: str, page: int, total: int, show_manage: bool = True) -> InlineKeyboardMarkup:
    """Навигация по истории с управлением чатами."""
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons
    layout: list[int] = []
    if total > 1:
        nav_count = 0
        if page > 0:
            builder.button(text="⬅️ " + t(language, "btn_back"), callback_data=f"menu:history:{page - 1}")
            nav_count += 1
        builder.button(text=f"{page + 1}/{total}", callback_data="menu:noop")
        nav_count += 1
        if page < total - 1:
            builder.button(text=t(language, "btn_back") + " ➡️", callback_data=f"menu:history:{page + 1}")
            nav_count += 1
        layout.append(nav_count)
    
    # Chat management
    if show_manage:
        builder.button(text="📂 " + t(language, "btn_open_chat"), callback_data=f"menu:openchat:{page}")
        builder.button(text="🗑️ " + t(language, "btn_delete_chat"), callback_data=f"menu:deletechat:{page}")
        layout.append(2)
    
    builder.button(text="📝 " + t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text="🏠 " + t(language, "btn_back"), callback_data="menu:home")
    layout.append(2)
    
    builder.adjust(*layout)
    return builder.as_markup()


def quick_model_selection_keyboard(*, language: str) -> InlineKeyboardMarkup:
    """Быстрый выбор модели для UrAI."""
    builder = InlineKeyboardBuilder()
    models = [
        ("gpt4", "🧠 GPT-4"),
        ("llama4_media", "🎬 Llama 4 Media"),
        ("llama3", "🦙 Llama 3"),
        ("groq_compound", "⚡ Groq Compound"),
    ]
    for model_id, label in models:
        builder.button(text=label, callback_data=f"modelpreset:{model_id}:menu")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(1, 1, 1, 1, 1)
    return builder.as_markup()


def personality_quick_keyboard(
    *,
    language: str,
    custom_personalities: list[tuple[str, str]] | None = None,
) -> InlineKeyboardMarkup:
    """Быстрый выбор личности со стандартными вариантами."""
    builder = InlineKeyboardBuilder()

    # Quick personality selection (localized)
    quick_personalities = [
        "default",
        "teacher",
        "programmer",
        "mathematician",
    ]

    for personality_id in quick_personalities:
        if personality_id not in SUPPORTED_PERSONALITIES:
            continue
        callback = f"personality:{personality_id}"
        builder.button(text=personality_label(language, personality_id), callback_data=callback)
    
    # Custom personalities if available
    if custom_personalities:
        for personality_id, title in custom_personalities[:3]:  # Show first 3 custom
            builder.button(text=f"🧾 {title}", callback_data=f"personality:{personality_id}")
    
    builder.button(text=t(language, "btn_personality"), callback_data="menu:personality:menu")
    builder.button(text=t(language, "btn_newchat"), callback_data="menu:newchat")
    builder.button(text=t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2)
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
    builder.button(text="🧠 " + t(language, "btn_provider"), callback_data="menu:provider:menu")
    builder.button(text="🎭 " + t(language, "btn_personality"), callback_data="menu:personality:menu")
    builder.button(text="💾 " + t(language, "btn_model"), callback_data="menu:model:menu")
    builder.button(text="🔑 " + t(language, "btn_apikey"), callback_data="menu:apikey:menu")
    builder.button(text="🌐 " + t(language, "btn_language"), callback_data="menu:language:menu")
    builder.button(text="🔗 " + t(language, "btn_baseurl"), callback_data="menu:baseurl:menu")
    builder.button(text="📜 " + t(language, "btn_history"), callback_data="menu:history:0")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 2, 2, 2)
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
    """Выбор провайдера с выделением UrAI."""
    builder = InlineKeyboardBuilder()
    
    # Show UrAI first if enabled
    if show_shared:
        builder.button(text="🤖 UrAI", callback_data="provider:shared_ai")
    
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
    builder.button(text="🤖 UrAI", callback_data="modelpreset:llama3:menu")
    builder.button(text="🔑 Own API Key", callback_data="modelpreset:own_api:menu")
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
    
    builder.button(text="🌐 " + t(language, "btn_language"), callback_data="menu:language:menu")
    builder.button(text=t(language, "btn_back"), callback_data="menu:home")
    builder.adjust(2, 1, 1)
    return builder.as_markup()
