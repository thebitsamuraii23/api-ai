from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "ru", "es", "fr", "tr", "ar", "de", "it", "pt", "uk", "hi")
SUPPORTED_PERSONALITIES = (
    "default",
    "lawyer",
    "advocate",
    "psychologist",
    "programmer",
    "teacher",
    "mentor",
    "marketer",
    "product_manager",
    "writer",
    "comedian",
    "poet",
    "philosopher",
    "genius",
    "bro",
    "manipulator",
    "liar",
    "historian",
    "critic",
    "mathematician",
    "dushnila",
)

LANGUAGE_LABELS: dict[str, str] = {
    "en": "🇺🇸 English",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Espanol",
    "fr": "🇫🇷 Francais",
    "tr": "🇹🇷 Turkce",
    "ar": "🇸🇦 العربية",
    "de": "🇩🇪 Deutsch",
    "it": "🇮🇹 Italiano",
    "pt": "🇵🇹 Portugues",
    "uk": "🇺🇦 Українська",
    "hi": "🇮🇳 हिन्दी",
}

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "lang_name": "English",
        "welcome": (
            "👋 Welcome!\n"
            "This bot works only with your personal API key.\n\n"
            "🚀 Quick start:\n"
            "1. Choose provider\n"
            "2. Add API key\n"
            "3. Start chatting\n\n"
            "🌐 Internet search: use /i \"query\""
        ),
        "help": (
            "📚 Commands:\n"
            "• /languages - choose interface language\n"
            "• /provider - choose AI provider\n"
            "• /personality - choose AI personality\n"
            "• /apikey - save API key for current provider\n"
            "• /deletekey - remove API key for current provider\n"
            "• /model - set model name\n"
            "• /baseurl - set base URL (custom provider)\n"
            "• /settings - show your settings\n"
            "• /limit - show remaining tokens\n"
            "• /tokens - show remaining tokens\n"
            "• /history - show saved chats\n"
            "• /newchat - start a new chat\n"
            "• /i \"query\" - internet search\n"
            "• /cancel - cancel current input"
        ),
        "help_ai_assist_hint": "❓ If something is unclear, ask the AI assistant for help and it will guide you step by step.",
        "internet_search_usage": "Usage: /i \"query\" (example: /i \"current time in Baku\")",
        "internet_search_header": "🔎 Web search results:",
        "internet_search_no_results": "⚠️ No results found. Try another query.",
        "internet_search_failed": "⚠️ Web search failed. Try again later.",
        "internet_search_answer_hint": "Tip: save an API key with /apikey to also get an AI summary from sources.",
        "convert_failed": "⚠️ Could not convert time. Try another format or locations.",
        "convert_result": "Converted time in {to_loc}: {time}",
        "convert_day_next": "next day",
        "convert_day_prev": "previous day",
        "convert_day_in": "in {days} days",
        "convert_day_ago": "{days} days earlier",
        "choose_language": (
            "🌐 Language center\n"
            "Pick your interface language below.\n"
            "✅ Current: {current}\n"
            "🧭 Available: {total}"
        ),
        "language_changed": "✅ Language updated: {language}",
        "choose_provider": "🤖 Choose provider:",
        "provider_changed": "✅ Provider set: {provider}",
        "choose_personality": "🎭 Choose AI personality:",
        "personality_changed": "✅ Personality selected: {personality}",
        "ask_custom_instruction_name": (
            "🧾 Send a name for your custom instruction.\n"
            "This name will be shown on the inline personality button."
        ),
        "ask_custom_instructions": (
            "✍️ Great. Now send the instruction text for the bot in one message."
        ),
        "custom_instructions_saved": "✅ Custom instructions saved: {personality}",
        "unknown_provider": "⚠️ Unknown provider. Use /provider.",
        "unsupported_language": "⚠️ Unsupported language.",
        "ask_api_key": "🔐 Send your API key for {provider}.",
        "apikey_privacy_reminder": "🛡️ API-key storage is end-to-end encrypted. more learn at: /privacy",
        "apikey_cancel_hint": "❌ To cancel input, send /cancel",
        "api_key_saved": "✅ API key saved for {provider}.",
        "provider_auto_switched": "🔄 Detected {detected} key. Provider switched: {from_provider} → {to_provider}.",
        "api_key_removed": "🗑️ API key deleted for {provider}.",
        "ask_model": "🧠 Send model name (example: gpt-4o-mini).",
        "model_saved": "✅ Model set: {model}",
        "choose_model_preset": "🧠 Choose model for UrAI:",
        "model_preset_changed": "✅ UrAI model set: {model}",
        "model_personal_api_enabled": (
            "🔐 Personal API mode enabled.\n"
            "Now use /apikey for your own key and /model for manual model name."
        ),
        "model_personal_api_missing_key": "⚠️ Personal API mode is enabled, but your key is missing. Use /apikey.",
        "shared_quota_exceeded": "⚠️ You reached your UrAI quota ({limit} tokens). Switch to Own API or wait for reset.",
        "shared_quota_low_warning": (
            "⚠️ Low token balance: {remaining} left.\n"
            "To avoid interruption, switch to Own API mode or monitor usage via /limit."
        ),
        "shared_ai_not_configured": "⚠️ UrAI is temporarily unavailable. Contact admin.",
        "access_mode_shared": "UrAI",
        "access_mode_personal": "Own API",
        "model_gpt4": "GPT 4",
        "model_llama3": "LLaMA 3",
        "model_groq_compound": "Groq Compound",
        "model_llama4_media": "LLaMA 4 (Media)",
        "btn_own_api": "🔐 Own API",
        "btn_use_bot_ai": "Use UrAI (With limits)",
        "ask_base_url": "🔗 Send API base URL (example: https://api.example.com/v1)",
        "base_url_saved": "✅ Base URL saved: {base_url}",
        "custom_base_url_required": "⚠️ Custom provider requires /baseurl before chat.",
        "missing_api_key": "⚠️ No API key for {provider}. Use /apikey.",
        "settings_view": (
            "⚙️ Your settings:\n"
            "🌐 Language: {language}\n"
            "🛂 Mode: {access_mode}\n"
            "🤖 Provider: {provider}\n"
            "🎭 Personality: {personality}\n"
            "🧠 Model: {model}\n"
            "🔗 Base URL: {base_url}\n"
            "🔐 API key: {has_key}\n"
            "🧮 Tokens left: {tokens_left}"
        ),
        "realtime_answers_on": "ON",
        "realtime_answers_off": "OFF",
        "realtime_answers_toggled": "✅ Real-time answers: {status}",
        "limit_shared": (
            "🪙 Token balance\n"
            "{status} UrAI quota\n"
            "📊 Used: {used} / {limit} ({percent}%)\n"
            "💎 Available: {remaining}\n"
            "{bar}\n"
            "🗓️ UrAI quota resets every month."
        ),
        "limit_personal": (
            "🔐 Own API mode\n"
            "🌟 Bot token quota doesn't apply here\n"
            "🪙 Available tokens: ∞\n"
            "🗓️ UrAI quota resets every month."
        ),
        "history_cleared": "🗑️ History cleared.",
        "new_chat_started": "🆕 New chat started.",
        "new_chat_already_empty": "ℹ️ Current chat has no messages. History unchanged.",
        "no_history": "📭 History is empty.",
        "history_title": "🕘 Recent messages:",
        "history_chat_view": "🗂️ Chat {current}/{total}\n🏷️ Title: {title}\n💬 Messages: {messages}\n🕘 Last: {content}",
        "untitled_chat": "Untitled chat",
        "processing": "⏳ Thinking...",
        "media_image_default_prompt": "Describe this image.",
        "unsupported_media_type": "⚠️ This media type is not supported yet. Send text, voice, video note, photo, or image file.",
        "media_too_large": "⚠️ Image is too large. Maximum size is {max_mb} MB.",
        "voice_too_large": "⚠️ Voice message is too large. Maximum size is {max_mb} MB.",
        "voice_transcription_failed": "⚠️ Failed to transcribe voice message. Try another voice note or provider.",
        "media_download_failed": "⚠️ Failed to download media. Please try another file.",
        "response_sent_as_image": "📷 Sent as image for better readability.",
        "error": "❌ Request failed: {error}",
        "invalid_api_key": "🔐 API key is invalid for {provider}.",
        "provider_mismatch_hint": (
            "💡 Your key looks like {suggested} key, but current provider is {current}. "
            "Switch provider in /provider or inline menu."
        ),
        "menu_title": "✨ Main menu:",
        "btn_settings": "⚙️ Settings",
        "btn_history": "🗂️ History",
        "btn_provider": "🤖 Provider",
        "btn_language": "🌐 Language",
        "btn_personality": "🎭 Personality",
        "btn_internet_search": "🔎 Internet search",
        "btn_sources": "📚 Sources",
        "btn_close_sources": "❌ Close",
        "sources_expired": "Sources expired.",
        "btn_limit": "🧮 Limit",
        "btn_custom_instructions": "🧾 Custom instructions",
        "btn_custom_instructions_new": "➕ Add custom instructions",
        "btn_apikey": "🔐 Set API key",
        "btn_model": "🧠 Set model",
        "btn_baseurl": "🔗 Set base URL",
        "btn_newchat": "🆕 New chat",
        "btn_open_chat": "↩️ Open chat",
        "btn_delete_chat": "🗑️ Delete chat",
        "btn_cancel": "❌ Cancel",
        "btn_back": "⬅️ Back",
        "chat_opened": "✅ Chat selected: {title}",
        "chat_deleted": "🗑️ Chat deleted.",
        "only_private": "🔒 Use this bot in private chat.",
        "personality_default": "🧩 Universal assistant",
        "personality_lawyer": "⚖️ Lawyer",
        "personality_advocate": "🛡️ Advocate",
        "personality_psychologist": "🧠 Psychologist",
        "personality_programmer": "💻 Programmer",
        "personality_teacher": "📚 Teacher",
        "personality_mentor": "🧭 Mentor",
        "personality_marketer": "📈 Marketer",
        "personality_product_manager": "🗂️ Product manager",
        "personality_writer": "✍️ Writer",
        "personality_comedian": "😂 Comedian",
        "personality_poet": "🪶 Poet",
        "personality_philosopher": "🏛️ Philosopher",
        "personality_genius": "🧬 Genius",
        "personality_bro": "🧢 Bro",
        "personality_manipulator": "🎭 Manipulator",
        "personality_liar": "🤥 Liar",
        "personality_historian": "📜 Historian",
        "personality_critic": "🔍 Critic",
        "personality_mathematician": "🧮 Mathematician",
        "personality_dushnila": "🤓 Nitpicker",
        "system_prompt": "You are a helpful AI assistant. Always answer in {language_name}.",
        "invalid_url": "⚠️ Invalid URL. Send full URL starting with http:// or https://",
        "history_item_view": "🗂️ History {current}/{total}\n{role}: {content}",
        "custom_instructions_manage_title": "🧾 Custom instructions (edit existing):",
        "custom_instructions_manage_empty": "🧾 You don't have custom instructions yet. Add one first.",
        "custom_instructions_edit_actions": "🧾 Selected: {personality}\nChoose what to edit:",
        "custom_instructions_edit_prompt": "✍️ Editing: {personality}\nSend the new instruction text in one message.",
        "custom_instructions_rename_prompt": "🏷️ Renaming: {personality}\nSend a new personality name in one message.",
        "custom_instructions_updated": "✅ Custom instructions updated: {personality}",
        "custom_instructions_renamed": "✅ Custom personality renamed: {personality}",
        "custom_instructions_current": "Current instructions:",
        "custom_instructions_not_found": "⚠️ Custom instructions not found. It may have been removed.",
        "btn_edit_custom_instructions_text": "✍️ Edit instruction text",
        "btn_edit_custom_instructions_name": "🏷️ Edit personality name",
        "btn_delete_custom_instructions": "🗑️ Delete custom instructions",
        "btn_confirm_delete": "✅ Yes, delete",
        "custom_instructions_delete_confirm": "🗑️ Delete {personality}? This cannot be undone.",
        "custom_instructions_deleted": "🗑️ Deleted: {personality}",
        "custom_instructions_delete_failed": "⚠️ Delete failed. It may have been already removed.",
        "feature_request_contact_dev": (
            "💡 Looks like this feature is missing right now.\n"
            "Please message the developer in Telegram: @thebitsamurai"
        ),
    },
    "ru": {
        "lang_name": "Русский",
        "welcome": (
            "👋 Добро пожаловать!\n"
            "Бот работает только с вашим личным API-ключом.\n\n"
            "🚀 Быстрый старт:\n"
            "1. Выберите провайдера\n"
            "2. Добавьте API-ключ\n"
            "3. Начинайте диалог\n\n"
            "🌐 Интернет-поиск: используйте /i \"запрос\""
        ),
        "help": (
            "📚 Команды:\n"
            "• /languages - выбрать язык интерфейса\n"
            "• /provider - выбрать AI-провайдера\n"
            "• /personality - выбрать личность AI\n"
            "• /apikey - сохранить API-ключ текущего провайдера\n"
            "• /deletekey - удалить API-ключ текущего провайдера\n"
            "• /model - задать модель\n"
            "• /baseurl - задать base URL (custom-провайдер)\n"
            "• /settings - показать настройки\n"
            "• /limit - остаток токенов\n"
            "• /tokens - остаток токенов\n"
            "• /history - история сохранённых чатов\n"
            "• /newchat - начать новый чат\n"
            "• /i \"запрос\" - интернет-поиск\n"
            "• /cancel - отменить ввод"
        ),
        "help_ai_assist_hint": "❓ Если что-то непонятно или не получается, просто попросите ИИ помочь — он проведёт вас шаг за шагом.",
        "internet_search_usage": "Использование: /i \"запрос\" (пример: /i \"время в Баку сейчас\"). Поиск выполняется на сервере бота.",
        "internet_search_header": "🔎 Результаты интернет-поиска:",
        "internet_search_no_results": "⚠️ Ничего не найдено. Попробуйте другой запрос.",
        "internet_search_failed": "⚠️ Ошибка интернет-поиска. Попробуйте позже.",
        "internet_search_answer_hint": "Подсказка: сохраните API-ключ через /apikey, чтобы бот ещё и сделал краткий ответ по источникам.",
        "convert_failed": "⚠️ Не удалось конвертировать время. Попробуйте другой формат или города.",
        "convert_result": "Время в {to_loc}: {time}",
        "convert_day_next": "следующий день",
        "convert_day_prev": "предыдущий день",
        "convert_day_in": "через {days} дн.",
        "convert_day_ago": "{days} дн. назад",
        "choose_language": (
            "🌐 Центр языков\n"
            "Выберите язык интерфейса ниже.\n"
            "✅ Текущий: {current}\n"
            "🧭 Доступно: {total}"
        ),
        "language_changed": "✅ Язык обновлён: {language}",
        "choose_provider": "🤖 Выберите провайдера:",
        "provider_changed": "✅ Провайдер установлен: {provider}",
        "choose_personality": "🎭 Выберите личность AI:",
        "personality_changed": "✅ Личность выбрана: {personality}",
        "ask_custom_instruction_name": (
            "🧾 Отправьте название для вашей кастомной инструкции.\n"
            "Это название будет отображаться на inline-кнопке личности."
        ),
        "ask_custom_instructions": (
            "✍️ Отлично. Теперь отправьте саму инструкцию для бота одним сообщением."
        ),
        "custom_instructions_saved": "✅ Кастомные инструкции сохранены: {personality}",
        "unknown_provider": "⚠️ Неизвестный провайдер. Используйте /provider.",
        "unsupported_language": "⚠️ Неподдерживаемый язык.",
        "ask_api_key": "🔐 Отправьте API-ключ для {provider}.",
        "apikey_privacy_reminder": "🛡️ Хранение API-ключей работает с end-to-end шифрованием. more learn at: /privacy",
        "apikey_cancel_hint": "❌ Чтобы отменить ввод, отправьте /cancel",
        "api_key_saved": "✅ API-ключ сохранён для {provider}.",
        "provider_auto_switched": "🔄 Определён ключ {detected}. Провайдер переключён: {from_provider} → {to_provider}.",
        "api_key_removed": "🗑️ API-ключ удалён для {provider}.",
        "ask_model": "🧠 Отправьте имя модели (пример: gpt-4o-mini).",
        "model_saved": "✅ Модель установлена: {model}",
        "choose_model_preset": "🧠 Выберите модель UrAI:",
        "model_preset_changed": "✅ Модель UrAI изменена: {model}",
        "model_personal_api_enabled": (
            "🔐 Режим своего API включён.\n"
            "Теперь используйте /apikey для своего ключа и /model для ввода имени модели."
        ),
        "model_personal_api_missing_key": "⚠️ Включён режим своего API, но ключ не задан. Используйте /apikey.",
        "shared_quota_exceeded": "⚠️ Вы израсходовали лимит UrAI ({limit} токенов). Переключитесь на Свой API.",
        "shared_quota_low_warning": (
            "⚠️ У вас мало токенов: осталось {remaining}.\n"
            "Чтобы не прерывать работу, переключитесь на Свой API или проверьте остаток через /limit."
        ),
        "shared_ai_not_configured": "⚠️ UrAI временно недоступен. Свяжитесь с админом.",
        "access_mode_shared": "UrAI",
        "access_mode_personal": "Свой API",
        "model_gpt4": "GPT 4",
        "model_llama3": "LLaMA 3",
        "model_groq_compound": "Groq Compound",
        "model_llama4_media": "LLaMA 4 (Media)",
        "btn_own_api": "🔐 Свой API",
        "btn_use_bot_ai": "Use UrAI (With limits)",
        "ask_base_url": "🔗 Отправьте базовый URL API (пример: https://api.example.com/v1)",
        "base_url_saved": "✅ Base URL сохранён: {base_url}",
        "custom_base_url_required": "⚠️ Для custom-провайдера перед чатом нужен /baseurl.",
        "missing_api_key": "⚠️ Нет API-ключа для {provider}. Используйте /apikey.",
        "settings_view": (
            "⚙️ Ваши настройки:\n"
            "🌐 Язык: {language}\n"
            "🛂 Режим: {access_mode}\n"
            "🤖 Провайдер: {provider}\n"
            "🎭 Личность: {personality}\n"
            "🧠 Модель: {model}\n"
            "🔗 Base URL: {base_url}\n"
            "🔐 API-ключ: {has_key}\n"
            "🧮 Остаток токенов: {tokens_left}"
        ),
        "realtime_answers_on": "ВКЛ",
        "realtime_answers_off": "ВЫКЛ",
        "realtime_answers_toggled": "✅ Ответы в реальном времени: {status}",
        "limit_shared": (
            "🪙 Баланс токенов\n"
            "{status} Квота UrAI\n"
            "📊 Использовано: {used} / {limit} ({percent}%)\n"
            "💎 Доступно: {remaining}\n"
            "{bar}\n"
            "🗓️ Квота UrAI обновляется каждый месяц."
        ),
        "limit_personal": (
            "🔐 Режим Свой API\n"
            "🌟 Лимит токенов бота здесь не применяется\n"
            "🪙 Доступно токенов: ∞\n"
            "🗓️ Квота UrAI обновляется каждый месяц."
        ),
        "history_cleared": "🗑️ История очищена.",
        "new_chat_started": "🆕 Начат новый чат.",
        "new_chat_already_empty": "ℹ️ В текущем чате нет сообщений. История не изменена.",
        "no_history": "📭 История пуста.",
        "history_title": "🕘 Последние сообщения:",
        "history_chat_view": "🗂️ Чат {current}/{total}\n🏷️ Название: {title}\n💬 Сообщений: {messages}\n🕘 Последнее: {content}",
        "untitled_chat": "Без названия",
        "processing": "⏳ Думаю...",
        "media_image_default_prompt": "Опиши это изображение.",
        "unsupported_media_type": "⚠️ Этот тип медиа пока не поддерживается. Отправьте текст, голосовое, кружок, фото или файл-изображение.",
        "media_too_large": "⚠️ Изображение слишком большое. Максимальный размер: {max_mb} МБ.",
        "voice_too_large": "⚠️ Голосовое сообщение слишком большое. Максимальный размер: {max_mb} МБ.",
        "voice_transcription_failed": "⚠️ Не удалось распознать голосовое сообщение. Попробуйте другое голосовое или другого провайдера.",
        "media_download_failed": "⚠️ Не удалось загрузить медиа. Попробуйте другой файл.",
        "response_sent_as_image": "📷 Отправил ответ как изображение для корректного отображения.",
        "error": "❌ Ошибка запроса: {error}",
        "invalid_api_key": "🔐 API-ключ недействителен для {provider}.",
        "provider_mismatch_hint": (
            "💡 Ваш ключ похож на ключ {suggested}, но текущий провайдер — {current}. "
            "Смените провайдера в /provider или в inline-меню."
        ),
        "menu_title": "✨ Главное меню:",
        "btn_settings": "⚙️ Настройки",
        "btn_history": "🗂️ История",
        "btn_provider": "🤖 Провайдер",
        "btn_language": "🌐 Язык",
        "btn_personality": "🎭 Личности",
        "btn_internet_search": "🔎 Интернет-поиск",
        "btn_sources": "📚 Источники",
        "btn_close_sources": "❌ Закрыть",
        "sources_expired": "Источники устарели.",
        "btn_limit": "🧮 Лимит",
        "btn_custom_instructions": "🧾 Кастомные инструкции",
        "btn_custom_instructions_new": "➕ Добавить кастомные инструкции",
        "btn_apikey": "🔐 Задать API-ключ",
        "btn_model": "🧠 Задать модель",
        "btn_baseurl": "🔗 Задать Base URL",
        "btn_newchat": "🆕 Новый чат",
        "btn_open_chat": "↩️ Открыть чат",
        "btn_delete_chat": "🗑️ Удалить чат",
        "btn_cancel": "❌ Отмена",
        "btn_back": "⬅️ Назад",
        "chat_opened": "✅ Чат выбран: {title}",
        "chat_deleted": "🗑️ Чат удалён.",
        "only_private": "🔒 Используйте бота только в приватном чате.",
        "personality_default": "🧩 Универсальный ассистент",
        "personality_lawyer": "⚖️ Юрист",
        "personality_advocate": "🛡️ Адвокат",
        "personality_psychologist": "🧠 Психолог",
        "personality_programmer": "💻 Программист",
        "personality_teacher": "📚 Преподаватель",
        "personality_mentor": "🧭 Ментор",
        "personality_marketer": "📈 Маркетолог",
        "personality_product_manager": "🗂️ Продакт-менеджер",
        "personality_writer": "✍️ Писатель",
        "personality_comedian": "😂 Юморист",
        "personality_poet": "🪶 Поэт",
        "personality_philosopher": "🏛️ Философ",
        "personality_genius": "🧬 Гений",
        "personality_bro": "🧢 Бро",
        "personality_manipulator": "🎭 Манипулятор",
        "personality_liar": "🤥 Лжец",
        "personality_historian": "📜 Историк",
        "personality_critic": "🔍 Критик",
        "personality_mathematician": "🧮 Математик",
        "personality_dushnila": "🤓 Душнила",
        "system_prompt": "Ты полезный AI-ассистент. Всегда отвечай на {language_name}.",
        "invalid_url": "⚠️ Неверный URL. Отправьте полный URL, начинающийся с http:// или https://",
        "history_item_view": "🗂️ История {current}/{total}\n{role}: {content}",
        "custom_instructions_manage_title": "🧾 Кастомные инструкции (редактирование):",
        "custom_instructions_manage_empty": "🧾 У вас пока нет кастомных инструкций. Сначала добавьте одну.",
        "custom_instructions_edit_actions": "🧾 Выбрано: {personality}\nЧто изменить?",
        "custom_instructions_edit_prompt": "✍️ Редактирование: {personality}\nОтправьте новый текст инструкции одним сообщением.",
        "custom_instructions_rename_prompt": "🏷️ Переименование: {personality}\nОтправьте новое имя персональности одним сообщением.",
        "custom_instructions_updated": "✅ Кастомные инструкции обновлены: {personality}",
        "custom_instructions_renamed": "✅ Кастомная персональность переименована: {personality}",
        "custom_instructions_current": "Текущие инструкции:",
        "custom_instructions_not_found": "⚠️ Кастомные инструкции не найдены. Возможно, они уже удалены.",
        "btn_edit_custom_instructions_text": "✍️ Изменить текст инструкции",
        "btn_edit_custom_instructions_name": "🏷️ Изменить имя персональности",
        "btn_delete_custom_instructions": "🗑️ Удалить кастомные инструкции",
        "btn_confirm_delete": "✅ Да, удалить",
        "custom_instructions_delete_confirm": "🗑️ Удалить {personality}? Это действие нельзя отменить.",
        "custom_instructions_deleted": "🗑️ Удалено: {personality}",
        "custom_instructions_delete_failed": "⚠️ Не удалось удалить. Возможно, уже удалено.",
        "feature_request_contact_dev": (
            "💡 Похоже, этой функции сейчас нет в боте.\n"
            "Напишите разработчику в Telegram: @thebitsamurai"
        ),
    },
    "es": {
        "lang_name": "Espanol",
        "welcome": (
            "Bienvenido. Este bot funciona solo con tu propia clave API.\n"
            "Configura proveedor y clave, luego empieza a chatear."
        ),
        "help": (
            "Comandos:\n"
            "/languages - elegir idioma\n"
            "/provider - elegir proveedor de IA\n"
            "/personality - elegir personalidad de IA\n"
            "/apikey - guardar clave API del proveedor actual\n"
            "/deletekey - borrar clave del proveedor actual\n"
            "/model - definir modelo\n"
            "/baseurl - definir URL base (proveedor custom)\n"
            "/settings - mostrar configuracion\n"
            "/history - mostrar historial reciente\n"
            "/newchat - limpiar memoria/historial\n"
            "/i \"consulta\" - busqueda en internet"
        ),
        "help_ai_assist_hint": "❓ Si algo no esta claro, pide ayuda al asistente de IA y te guiara paso a paso.",
        "internet_search_usage": "Uso: /i \"consulta\" (ejemplo: /i \"hora actual en Baku\")",
        "internet_search_header": "🔎 Resultados de busqueda web:",
        "internet_search_no_results": "⚠️ No se encontraron resultados. Prueba otra consulta.",
        "internet_search_failed": "⚠️ Fallo la busqueda web. Intentalo mas tarde.",
        "internet_search_answer_hint": "Consejo: guarda una clave con /apikey para recibir tambien un resumen con fuentes.",
        "choose_language": (
            "🌐 Centro de idiomas\n"
            "Elige el idioma de la interfaz abajo.\n"
            "✅ Actual: {current}\n"
            "🧭 Disponibles: {total}"
        ),
        "language_changed": "Idioma cambiado a {language}.",
        "choose_provider": "Elige proveedor:",
        "provider_changed": "Proveedor cambiado a {provider}.",
        "choose_personality": "🎭 Elige personalidad de IA:",
        "personality_changed": "✅ Personalidad seleccionada: {personality}",
        "ask_custom_instruction_name": (
            "🧾 Envia un nombre para tu instruccion personalizada.\n"
            "Este nombre se mostrara en el boton inline de personalidad."
        ),
        "ask_custom_instructions": (
            "✍️ Bien. Ahora envia el texto de instrucciones para el bot en un solo mensaje."
        ),
        "custom_instructions_saved": "✅ Instrucciones personalizadas guardadas: {personality}",
        "unknown_provider": "Proveedor desconocido. Usa /provider.",
        "ask_api_key": "Envia tu clave API para {provider}.",
        "api_key_saved": "Clave API guardada para {provider}.",
        "api_key_removed": "Clave API eliminada para {provider}.",
        "ask_model": "Envia el nombre del modelo (ejemplo: gpt-4o-mini).",
        "model_saved": "Modelo establecido: {model}",
        "ask_base_url": "Envia la URL base API (ejemplo: https://api.example.com/v1)",
        "base_url_saved": "URL base guardada: {base_url}",
        "custom_base_url_required": "El proveedor custom necesita /baseurl antes de chatear.",
        "missing_api_key": "No hay clave API para {provider}. Usa /apikey.",
        "settings_view": (
            "Tu configuracion:\n"
            "Idioma: {language}\n"
            "Proveedor: {provider}\n"
            "Personalidad: {personality}\n"
            "Modelo: {model}\n"
            "URL base: {base_url}\n"
            "Clave API: {has_key}"
        ),
        "history_cleared": "Historial borrado.",
        "no_history": "El historial esta vacio.",
        "history_title": "Mensajes recientes:",
        "processing": "Pensando...",
        "error": "Fallo en la solicitud: {error}",
        "only_private": "Usa este bot en chat privado.",
        "btn_settings": "⚙️ Configuracion",
        "btn_provider": "🤖 Proveedor",
        "btn_language": "🌐 Idioma",
        "btn_personality": "🎭 Personalidad",
        "btn_internet_search": "🔎 Busqueda en internet",
        "btn_sources": "📚 Fuentes",
        "btn_close_sources": "❌ Cerrar",
        "sources_expired": "Las fuentes caducaron.",
        "btn_limit": "🧮 Limite",
        "btn_model": "🧠 Modelo",
        "btn_newchat": "🆕 Nuevo chat",
        "btn_history": "🗂️ Historial",
        "btn_custom_instructions": "🧾 Instrucciones custom",
        "personality_default": "🧩 Asistente universal",
        "personality_lawyer": "⚖️ Jurista",
        "personality_advocate": "🛡️ Abogado defensor",
        "personality_psychologist": "🧠 Psicologo",
        "personality_programmer": "💻 Programador",
        "personality_teacher": "📚 Profesor",
        "personality_mentor": "🧭 Mentor",
        "personality_marketer": "📈 Especialista en marketing",
        "personality_product_manager": "🗂️ Product manager",
        "personality_writer": "✍️ Escritor",
        "personality_comedian": "😂 Humorista",
        "personality_poet": "🪶 Poeta",
        "personality_philosopher": "🏛️ Filosofo",
        "personality_genius": "🧬 Genio",
        "personality_manipulator": "🎭 Manipulador",
        "personality_liar": "🤥 Mentiroso",
        "personality_historian": "📜 Historiador",
        "personality_critic": "🔍 Critico",
        "personality_mathematician": "🧮 Matemático",
        "personality_dushnila": "🤓 Pedante",
        "system_prompt": "Eres un asistente de IA util. Responde siempre en {language_name}.",
        "invalid_url": "URL invalida. Envia URL completa con http:// o https://",
    },
    "fr": {
        "lang_name": "Francais",
        "welcome": (
            "Bienvenue. Ce bot fonctionne uniquement avec votre propre cle API.\n"
            "Choisissez un fournisseur et une cle, puis commencez a discuter."
        ),
        "help": (
            "Commandes:\n"
            "/languages - choisir la langue\n"
            "/provider - choisir le fournisseur IA\n"
            "/personality - choisir une personnalite IA\n"
            "/apikey - enregistrer la cle API du fournisseur actuel\n"
            "/deletekey - supprimer la cle du fournisseur actuel\n"
            "/model - definir le modele\n"
            "/baseurl - definir URL de base (fournisseur custom)\n"
            "/settings - afficher les parametres\n"
            "/history - afficher l'historique recent\n"
            "/newchat - effacer la memoire/historique\n"
            "/i \"requete\" - recherche internet"
        ),
        "help_ai_assist_hint": "❓ Si quelque chose n'est pas clair, demande de l'aide a l'assistant IA: il te guidera pas a pas.",
        "internet_search_usage": "Usage: /i \"requete\" (exemple: /i \"heure actuelle a Bakou\")",
        "internet_search_header": "🔎 Resultats de recherche web:",
        "internet_search_no_results": "⚠️ Aucun resultat. Essayez une autre requete.",
        "internet_search_failed": "⚠️ Echec de la recherche web. Reessayez plus tard.",
        "internet_search_answer_hint": "Astuce: enregistrez une cle avec /apikey pour obtenir aussi un resume avec sources.",
        "choose_language": (
            "🌐 Centre des langues\n"
            "Choisissez la langue de l'interface ci-dessous.\n"
            "✅ Actuelle: {current}\n"
            "🧭 Disponibles: {total}"
        ),
        "language_changed": "Langue changee en {language}.",
        "choose_provider": "Choisissez le fournisseur:",
        "provider_changed": "Fournisseur defini sur {provider}.",
        "choose_personality": "🎭 Choisissez la personnalite IA:",
        "personality_changed": "✅ Personnalite selectionnee: {personality}",
        "ask_custom_instruction_name": (
            "🧾 Envoyez un nom pour votre instruction personnalisee.\n"
            "Ce nom sera affiche sur le bouton inline de personnalite."
        ),
        "ask_custom_instructions": (
            "✍️ Parfait. Envoyez maintenant le texte d'instruction pour le bot en un seul message."
        ),
        "custom_instructions_saved": "✅ Instructions personnalisees enregistrees: {personality}",
        "unknown_provider": "Fournisseur inconnu. Utilisez /provider.",
        "ask_api_key": "Envoyez votre cle API pour {provider}.",
        "api_key_saved": "Cle API enregistree pour {provider}.",
        "api_key_removed": "Cle API supprimee pour {provider}.",
        "ask_model": "Envoyez le nom du modele (exemple: gpt-4o-mini).",
        "model_saved": "Modele defini: {model}",
        "ask_base_url": "Envoyez l'URL de base API (exemple: https://api.example.com/v1)",
        "base_url_saved": "URL de base enregistree: {base_url}",
        "custom_base_url_required": "Le fournisseur custom exige /baseurl avant de discuter.",
        "missing_api_key": "Aucune cle API pour {provider}. Utilisez /apikey.",
        "settings_view": (
            "Vos parametres:\n"
            "Langue: {language}\n"
            "Fournisseur: {provider}\n"
            "Personnalite: {personality}\n"
            "Modele: {model}\n"
            "URL de base: {base_url}\n"
            "Cle API: {has_key}"
        ),
        "history_cleared": "Historique efface.",
        "no_history": "Historique vide.",
        "history_title": "Messages recents:",
        "processing": "Reflexion...",
        "error": "Echec de la requete: {error}",
        "only_private": "Utilisez ce bot en chat prive.",
        "btn_settings": "⚙️ Parametres",
        "btn_provider": "🤖 Fournisseur",
        "btn_language": "🌐 Langue",
        "btn_personality": "🎭 Personnalite",
        "btn_internet_search": "🔎 Recherche internet",
        "btn_sources": "📚 Sources",
        "btn_close_sources": "❌ Fermer",
        "sources_expired": "Les sources ont expire.",
        "btn_limit": "🧮 Limite",
        "btn_model": "🧠 Modele",
        "btn_newchat": "🆕 Nouveau chat",
        "btn_history": "🗂️ Historique",
        "btn_custom_instructions": "🧾 Instructions custom",
        "personality_default": "🧩 Assistant universel",
        "personality_lawyer": "⚖️ Juriste",
        "personality_advocate": "🛡️ Avocat",
        "personality_psychologist": "🧠 Psychologue",
        "personality_programmer": "💻 Programmeur",
        "personality_teacher": "📚 Enseignant",
        "personality_mentor": "🧭 Mentor",
        "personality_marketer": "📈 Marketeur",
        "personality_product_manager": "🗂️ Chef de produit",
        "personality_writer": "✍️ Ecrivain",
        "personality_comedian": "😂 Humoriste",
        "personality_poet": "🪶 Poete",
        "personality_philosopher": "🏛️ Philosophe",
        "personality_genius": "🧬 Genie",
        "personality_manipulator": "🎭 Manipulateur",
        "personality_liar": "🤥 Menteur",
        "personality_historian": "📜 Historien",
        "personality_critic": "🔍 Critique",
        "personality_mathematician": "🧮 Mathématicien",
        "personality_dushnila": "🤓 Pedant",
        "system_prompt": "Vous etes un assistant IA utile. Repondez toujours en {language_name}.",
        "invalid_url": "URL invalide. Envoyez une URL complete commencant par http:// ou https://",
    },
    "tr": {
        "lang_name": "Turkce",
        "welcome": (
            "Hos geldiniz. Bu bot sadece kendi API anahtarinizla calisir.\n"
            "Saglayici ve anahtar ayarlayin, sonra sohbete baslayin."
        ),
        "help": (
            "Komutlar:\n"
            "/languages - dil sec\n"
            "/provider - AI saglayici sec\n"
            "/personality - AI kisiligi sec\n"
            "/apikey - mevcut saglayici icin API anahtari kaydet\n"
            "/deletekey - mevcut saglayici anahtarini sil\n"
            "/model - model adi ayarla\n"
            "/baseurl - temel URL ayarla (custom saglayici)\n"
            "/settings - ayarlari goster\n"
            "/history - son sohbet gecmisini goster\n"
            "/newchat - hafiza/gecmisi temizle\n"
            "/i \"sorgu\" - internet aramasi"
        ),
        "help_ai_assist_hint": "❓ Eger bir sey net degilse, AI asistandan yardim iste; seni adim adim yonlendirecek.",
        "internet_search_usage": "Kullanim: /i \"sorgu\" (ornek: /i \"Bakude saat kac\")",
        "internet_search_header": "🔎 Web arama sonuclari:",
        "internet_search_no_results": "⚠️ Sonuc bulunamadi. Baska bir sorgu deneyin.",
        "internet_search_failed": "⚠️ Web arama basarisiz. Daha sonra tekrar deneyin.",
        "internet_search_answer_hint": "Ipuclari: /apikey ile anahtar kaydedin, kaynaklara dayali kisa cevap da alin.",
        "choose_language": (
            "🌐 Dil merkezi\n"
            "Arayuz dilini asagidan secin.\n"
            "✅ Mevcut: {current}\n"
            "🧭 Mevcut diller: {total}"
        ),
        "language_changed": "Dil {language} olarak guncellendi.",
        "choose_provider": "Saglayici secin:",
        "provider_changed": "Saglayici {provider} olarak ayarlandi.",
        "choose_personality": "🎭 AI kisiligi secin:",
        "personality_changed": "✅ Secilen kisilik: {personality}",
        "ask_custom_instruction_name": (
            "🧾 Ozel talimatiniz icin bir ad gonderin.\n"
            "Bu ad inline kisilik dugmesinde gorunecek."
        ),
        "ask_custom_instructions": (
            "✍️ Harika. Simdi bot icin talimat metnini tek bir mesajla gonderin."
        ),
        "custom_instructions_saved": "✅ Ozel talimatlar kaydedildi: {personality}",
        "unknown_provider": "Bilinmeyen saglayici. /provider kullanin.",
        "ask_api_key": "{provider} icin API anahtarinizi gonderin.",
        "api_key_saved": "API anahtari {provider} icin kaydedildi.",
        "api_key_removed": "API anahtari {provider} icin silindi.",
        "ask_model": "Model adini gonderin (ornek: gpt-4o-mini).",
        "model_saved": "Model ayarlandi: {model}",
        "ask_base_url": "API base URL gonderin (ornek: https://api.example.com/v1)",
        "base_url_saved": "Base URL kaydedildi: {base_url}",
        "custom_base_url_required": "Custom saglayici sohbetten once /baseurl ister.",
        "missing_api_key": "{provider} icin API anahtari yok. /apikey kullanin.",
        "settings_view": (
            "Ayarlariniz:\n"
            "Dil: {language}\n"
            "Saglayici: {provider}\n"
            "Kisilik: {personality}\n"
            "Model: {model}\n"
            "Base URL: {base_url}\n"
            "API anahtari: {has_key}"
        ),
        "history_cleared": "Gecmis temizlendi.",
        "no_history": "Gecmis bos.",
        "history_title": "Son mesajlar:",
        "processing": "Dusunuyor...",
        "error": "Istek hatasi: {error}",
        "only_private": "Bu botu ozel sohbette kullanin.",
        "btn_settings": "⚙️ Ayarlar",
        "btn_provider": "🤖 Saglayici",
        "btn_language": "🌐 Dil",
        "btn_personality": "🎭 Kisilik",
        "btn_internet_search": "🔎 Internet arama",
        "btn_sources": "📚 Kaynaklar",
        "btn_close_sources": "❌ Kapat",
        "sources_expired": "Kaynaklarin suresi doldu.",
        "btn_limit": "🧮 Limit",
        "btn_model": "🧠 Model",
        "btn_newchat": "🆕 Yeni sohbet",
        "btn_history": "🗂️ Gecmis",
        "btn_custom_instructions": "🧾 Ozel talimatlar",
        "personality_default": "🧩 Evrensel asistan",
        "personality_lawyer": "⚖️ Hukukcu",
        "personality_advocate": "🛡️ Avukat",
        "personality_psychologist": "🧠 Psikolog",
        "personality_programmer": "💻 Programci",
        "personality_teacher": "📚 Ogretmen",
        "personality_mentor": "🧭 Mentor",
        "personality_marketer": "📈 Pazarlamaci",
        "personality_product_manager": "🗂️ Urun yoneticisi",
        "personality_writer": "✍️ Yazar",
        "personality_comedian": "😂 Komedyen",
        "personality_poet": "🪶 Sair",
        "personality_philosopher": "🏛️ Filozof",
        "personality_genius": "🧬 Dahi",
        "personality_manipulator": "🎭 Manipulator",
        "personality_liar": "🤥 Yalanci",
        "personality_historian": "📜 Tarihci",
        "personality_critic": "🔍 Elestirmen",
        "personality_mathematician": "🧮 Matematikçi",
        "personality_dushnila": "🤓 Bilmis",
        "system_prompt": "Yardimci bir AI asistansiniz. Her zaman {language_name} dilinde cevap verin.",
        "invalid_url": "Gecersiz URL. http:// veya https:// ile tam URL gonderin",
    },
    "ar": {
        "lang_name": "العربية",
        "welcome": "مرحبا. هذا البوت يعمل فقط بمفتاح API الخاص بك. اختر المزود والمفتاح ثم ابدأ المحادثة.",
        "help": (
            "الاوامر:\n"
            "/languages - اختيار اللغة\n"
            "/provider - اختيار مزود الذكاء الاصطناعي\n"
            "/personality - اختيار شخصية الذكاء الاصطناعي\n"
            "/apikey - حفظ مفتاح API للمزود الحالي\n"
            "/deletekey - حذف مفتاح المزود الحالي\n"
            "/model - تحديد اسم النموذج\n"
            "/baseurl - تحديد الرابط الاساسي (للمزود المخصص)\n"
            "/settings - عرض الاعدادات\n"
            "/history - عرض اخر سجل محادثة\n"
            "/newchat - مسح الذاكرة والسجل\n"
            "/i \"استعلام\" - بحث في الانترنت"
        ),
        "help_ai_assist_hint": "❓ اذا كان شيء غير واضح، اطلب المساعدة من مساعد الذكاء الاصطناعي وسيرشدك خطوة بخطوة.",
        "internet_search_usage": "الاستخدام: /i \"استعلام\" (مثال: /i \"الوقت الان في باكو\")",
        "internet_search_header": "🔎 نتائج البحث على الويب:",
        "internet_search_no_results": "⚠️ لا توجد نتائج. جرب استعلاما اخر.",
        "internet_search_failed": "⚠️ فشل البحث على الويب. حاول لاحقا.",
        "internet_search_answer_hint": "معلومة: احفظ مفتاح API عبر /apikey للحصول ايضا على ملخص يعتمد على المصادر.",
        "choose_language": (
            "🌐 مركز اللغات\n"
            "اختر لغة الواجهة من الازرار بالاسفل.\n"
            "✅ الحالية: {current}\n"
            "🧭 المتاحة: {total}"
        ),
        "language_changed": "تم تغيير اللغة الى {language}.",
        "choose_provider": "اختر المزود:",
        "provider_changed": "تم تعيين المزود الى {provider}.",
        "choose_personality": "🎭 اختر شخصية الذكاء الاصطناعي:",
        "personality_changed": "✅ تم اختيار الشخصية: {personality}",
        "ask_custom_instruction_name": (
            "🧾 ارسل اسما للتعليمات المخصصة.\n"
            "سيظهر هذا الاسم على زر الشخصية داخل القائمة."
        ),
        "ask_custom_instructions": (
            "✍️ ممتاز. الان ارسل نص التعليمات للبوت في رسالة واحدة."
        ),
        "custom_instructions_saved": "✅ تم حفظ التعليمات المخصصة: {personality}",
        "unknown_provider": "مزود غير معروف. استخدم /provider.",
        "ask_api_key": "ارسل مفتاح API الخاص بك لـ {provider}.",
        "api_key_saved": "تم حفظ مفتاح API لـ {provider}.",
        "api_key_removed": "تم حذف مفتاح API لـ {provider}.",
        "ask_model": "ارسل اسم النموذج (مثال: gpt-4o-mini).",
        "model_saved": "تم تعيين النموذج: {model}",
        "ask_base_url": "ارسل رابط API الاساسي (مثال: https://api.example.com/v1)",
        "base_url_saved": "تم حفظ الرابط الاساسي: {base_url}",
        "custom_base_url_required": "المزود المخصص يحتاج /baseurl قبل المحادثة.",
        "missing_api_key": "لا يوجد مفتاح API لـ {provider}. استخدم /apikey.",
        "settings_view": (
            "اعداداتك:\n"
            "اللغة: {language}\n"
            "المزود: {provider}\n"
            "الشخصية: {personality}\n"
            "النموذج: {model}\n"
            "الرابط الاساسي: {base_url}\n"
            "مفتاح API: {has_key}"
        ),
        "history_cleared": "تم مسح السجل.",
        "no_history": "السجل فارغ.",
        "history_title": "اخر الرسائل:",
        "processing": "جاري التفكير...",
        "error": "فشل الطلب: {error}",
        "only_private": "استخدم البوت في محادثة خاصة.",
        "btn_settings": "⚙️ الاعدادات",
        "btn_provider": "🤖 المزود",
        "btn_language": "🌐 اللغة",
        "btn_personality": "🎭 الشخصية",
        "btn_internet_search": "🔎 بحث على الانترنت",
        "btn_sources": "📚 المصادر",
        "btn_close_sources": "❌ اغلاق",
        "sources_expired": "انتهت صلاحية المصادر.",
        "btn_limit": "🧮 الحد",
        "btn_model": "🧠 النموذج",
        "btn_newchat": "🆕 دردشة جديدة",
        "btn_history": "🗂️ السجل",
        "btn_custom_instructions": "🧾 تعليمات مخصصة",
        "personality_default": "🧩 مساعد عام",
        "personality_lawyer": "⚖️ مستشار قانوني",
        "personality_advocate": "🛡️ محامي دفاع",
        "personality_psychologist": "🧠 اخصائي نفسي",
        "personality_programmer": "💻 مبرمج",
        "personality_teacher": "📚 معلم",
        "personality_mentor": "🧭 Mentor",
        "personality_marketer": "📈 مسوق",
        "personality_product_manager": "🗂️ مدير منتج",
        "personality_writer": "✍️ كاتب",
        "personality_comedian": "😂 فكاهي",
        "personality_poet": "🪶 شاعر",
        "personality_philosopher": "🏛️ فيلسوف",
        "personality_genius": "🧬 عبقري",
        "personality_manipulator": "🎭 متلاعب",
        "personality_liar": "🤥 كاذب",
        "personality_historian": "📜 مؤرخ",
        "personality_critic": "🔍 ناقد",
        "personality_mathematician": "🧮 رياضي",
        "personality_dushnila": "🤓 مدقق متحذلق",
        "system_prompt": "انت مساعد ذكاء اصطناعي مفيد. اجب دائما باللغة {language_name}.",
        "invalid_url": "رابط غير صالح. ارسل رابطا كاملا يبدأ بـ http:// او https://",
    },
    "de": {
        "lang_name": "Deutsch",
        "help_ai_assist_hint": "❓ Wenn etwas unklar ist, frag den KI-Assistenten um Hilfe. Er fuehrt dich Schritt fuer Schritt.",
        "choose_language": (
            "🌐 Sprachzentrum\n"
            "Waehle unten deine Interface-Sprache.\n"
            "✅ Aktuell: {current}\n"
            "🧭 Verfuegbar: {total}"
        ),
        "language_changed": "✅ Sprache aktualisiert: {language}",
        "unsupported_language": "⚠️ Nicht unterstuetzte Sprache.",
        "menu_title": "✨ Hauptmenue:",
        "btn_back": "⬅️ Zurueck",
        "btn_language": "🌐 Sprache",
        "btn_sources": "📚 Quellen",
        "btn_close_sources": "❌ Schliessen",
        "sources_expired": "Quellen sind abgelaufen.",
        "only_private": "🔒 Bitte nutze den Bot im privaten Chat.",
        "system_prompt": "Du bist ein hilfreicher KI-Assistent. Antworte immer auf {language_name}.",
    },
    "it": {
        "lang_name": "Italiano",
        "help_ai_assist_hint": "❓ Se qualcosa non e chiaro, chiedi aiuto all'assistente AI: ti guidera passo dopo passo.",
        "choose_language": (
            "🌐 Centro lingue\n"
            "Scegli qui sotto la lingua dell'interfaccia.\n"
            "✅ Attuale: {current}\n"
            "🧭 Disponibili: {total}"
        ),
        "language_changed": "✅ Lingua aggiornata: {language}",
        "unsupported_language": "⚠️ Lingua non supportata.",
        "menu_title": "✨ Menu principale:",
        "btn_back": "⬅️ Indietro",
        "btn_language": "🌐 Lingua",
        "btn_sources": "📚 Fonti",
        "btn_close_sources": "❌ Chiudi",
        "sources_expired": "Le fonti sono scadute.",
        "only_private": "🔒 Usa il bot nella chat privata.",
        "system_prompt": "Sei un assistente AI utile. Rispondi sempre in {language_name}.",
    },
    "pt": {
        "lang_name": "Portugues",
        "help_ai_assist_hint": "❓ Se algo nao estiver claro, peca ajuda ao assistente de IA. Ele vai guiar voce passo a passo.",
        "choose_language": (
            "🌐 Centro de idiomas\n"
            "Escolha abaixo o idioma da interface.\n"
            "✅ Atual: {current}\n"
            "🧭 Disponiveis: {total}"
        ),
        "language_changed": "✅ Idioma atualizado: {language}",
        "unsupported_language": "⚠️ Idioma nao suportado.",
        "menu_title": "✨ Menu principal:",
        "btn_back": "⬅️ Voltar",
        "btn_language": "🌐 Idioma",
        "btn_sources": "📚 Fontes",
        "btn_close_sources": "❌ Fechar",
        "sources_expired": "As fontes expiraram.",
        "only_private": "🔒 Use o bot no chat privado.",
        "system_prompt": "Voce e um assistente de IA util. Responda sempre em {language_name}.",
    },
    "uk": {
        "lang_name": "Українська",
        "help_ai_assist_hint": "❓ Якщо щось незрозуміло, попросіть AI-асистента про допомогу — він проведе вас крок за кроком.",
        "choose_language": (
            "🌐 Центр мов\n"
            "Оберіть мову інтерфейсу нижче.\n"
            "✅ Поточна: {current}\n"
            "🧭 Доступно: {total}"
        ),
        "language_changed": "✅ Мову оновлено: {language}",
        "unsupported_language": "⚠️ Непідтримувана мова.",
        "menu_title": "✨ Головне меню:",
        "btn_back": "⬅️ Назад",
        "btn_language": "🌐 Мова",
        "btn_sources": "📚 Джерела",
        "btn_close_sources": "❌ Закрити",
        "sources_expired": "Джерела застаріли.",
        "only_private": "🔒 Використовуйте бота в приватному чаті.",
        "system_prompt": "Ти корисний AI-асистент. Завжди відповідай {language_name}.",
    },
    "hi": {
        "lang_name": "हिन्दी",
        "help_ai_assist_hint": "❓ अगर कुछ समझ में नहीं आए, तो AI असिस्टेंट से मदद मांगें। वह आपको कदम-दर-कदम मार्गदर्शन देगा।",
        "choose_language": (
            "🌐 भाषा केंद्र\n"
            "नीचे इंटरफेस भाषा चुनें।\n"
            "✅ वर्तमान: {current}\n"
            "🧭 उपलब्ध: {total}"
        ),
        "language_changed": "✅ भाषा अपडेट हुई: {language}",
        "unsupported_language": "⚠️ यह भाषा समर्थित नहीं है।",
        "menu_title": "✨ मुख्य मेन्यू:",
        "btn_back": "⬅️ वापस",
        "btn_language": "🌐 भाषा",
        "btn_sources": "📚 स्रोत",
        "btn_close_sources": "❌ बंद करें",
        "sources_expired": "स्रोतों की समय-सीमा समाप्त हो गई।",
        "only_private": "🔒 कृपया बोट को निजी चैट में उपयोग करें।",
        "system_prompt": "आप एक सहायक AI असिस्टेंट हैं। हमेशा {language_name} में उत्तर दें।",
    },
}


def normalize_language(lang: str) -> str:
    lang = lang.lower().strip()
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return "en"


def normalize_personality(personality: str) -> str:
    value = personality.lower().strip()
    if value in SUPPORTED_PERSONALITIES:
        return value
    return "default"


def personality_label(lang: str, personality: str) -> str:
    normalized = normalize_personality(personality)
    key = f"personality_{normalized}"
    return t(lang, key)


def t(lang: str, key: str, **kwargs: str) -> str:
    normalized = normalize_language(lang)
    template = TEXTS.get(normalized, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
