from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "ru", "es", "fr", "tr", "ar")
SUPPORTED_PERSONALITIES = (
    "default",
    "lawyer",
    "advocate",
    "psychologist",
    "programmer",
    "teacher",
    "marketer",
    "product_manager",
    "writer",
    "comedian",
    "poet",
    "philosopher",
    "genius",
    "manipulator",
    "liar",
    "historian",
    "critic",
)

LANGUAGE_LABELS: dict[str, str] = {
    "en": "🇺🇸 English",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Espanol",
    "fr": "🇫🇷 Francais",
    "tr": "🇹🇷 Turkce",
    "ar": "🇸🇦 العربية",
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
            "3. Start chatting"
        ),
        "help": (
            "📚 Commands:\n"
            "• /menu - open the main inline menu\n"
            "• /language - choose interface language\n"
            "• /provider - choose AI provider\n"
            "• /personality - choose AI personality\n"
            "• /apikey - save API key for current provider\n"
            "• /deletekey - remove API key for current provider\n"
            "• /model - set model name\n"
            "• /baseurl - set base URL (custom provider)\n"
            "• /settings - show your settings\n"
            "• /history - show saved chats\n"
            "• /newchat - start a new chat\n"
            "• /cancel - cancel current input"
        ),
        "choose_language": "🌐 Choose interface language:",
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
        "api_key_saved": "✅ API key saved for {provider}.",
        "provider_auto_switched": "🔄 Detected {detected} key. Provider switched: {from_provider} → {to_provider}.",
        "api_key_removed": "🗑️ API key deleted for {provider}.",
        "ask_model": "🧠 Send model name (example: gpt-4o-mini).",
        "model_saved": "✅ Model set: {model}",
        "choose_model_preset": "🧠 Choose model for shared AI:",
        "model_preset_changed": "✅ Shared AI model set: {model}",
        "model_personal_api_enabled": (
            "🔐 Personal API mode enabled.\n"
            "Now use /apikey for your own key and /model for manual model name."
        ),
        "model_personal_api_missing_key": "⚠️ Personal API mode is enabled, but your key is missing. Use /apikey.",
        "shared_quota_exceeded": "⚠️ You reached your shared quota ({limit} tokens). Switch to Own API or wait for reset.",
        "shared_ai_not_configured": "⚠️ Shared AI is temporarily unavailable. Contact admin.",
        "access_mode_shared": "Shared AI",
        "access_mode_personal": "Own API",
        "model_gpt4": "GPT 4",
        "model_llama3": "LLAMA 3",
        "model_llama4_media": "LLAMA 4 (Media)",
        "btn_own_api": "🔐 Own API",
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
        "history_cleared": "🗑️ History cleared.",
        "new_chat_started": "🆕 New chat started.",
        "new_chat_already_empty": "ℹ️ Current chat has no messages. History unchanged.",
        "no_history": "📭 History is empty.",
        "history_title": "🕘 Recent messages:",
        "history_chat_view": "🗂️ Chat {current}/{total}\n🏷️ Title: {title}\n💬 Messages: {messages}\n🕘 Last: {content}",
        "untitled_chat": "Untitled chat",
        "processing": "⏳ Thinking...",
        "media_image_default_prompt": "Describe this image.",
        "unsupported_media_type": "⚠️ This media type is not supported yet. Send text, photo, or image file.",
        "media_too_large": "⚠️ Image is too large. Maximum size is {max_mb} MB.",
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
        "btn_custom_instructions": "🧾 Custom instructions",
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
        "personality_marketer": "📈 Marketer",
        "personality_product_manager": "🗂️ Product manager",
        "personality_writer": "✍️ Writer",
        "personality_comedian": "😂 Comedian",
        "personality_poet": "🪶 Poet",
        "personality_philosopher": "🏛️ Philosopher",
        "personality_genius": "🧬 Genius",
        "personality_manipulator": "🎭 Manipulator",
        "personality_liar": "🤥 Liar",
        "personality_historian": "📜 Historian",
        "personality_critic": "🔍 Critic",
        "system_prompt": "You are a helpful AI assistant. Always answer in {language_name}.",
        "invalid_url": "⚠️ Invalid URL. Send full URL starting with http:// or https://",
        "history_item_view": "🗂️ History {current}/{total}\n{role}: {content}",
    },
    "ru": {
        "lang_name": "Русский",
        "welcome": (
            "👋 Добро пожаловать!\n"
            "Бот работает только с вашим личным API-ключом.\n\n"
            "🚀 Быстрый старт:\n"
            "1. Выберите провайдера\n"
            "2. Добавьте API-ключ\n"
            "3. Начинайте диалог"
        ),
        "help": (
            "📚 Команды:\n"
            "• /menu - открыть главное inline-меню\n"
            "• /language - выбрать язык интерфейса\n"
            "• /provider - выбрать AI-провайдера\n"
            "• /personality - выбрать личность AI\n"
            "• /apikey - сохранить API-ключ текущего провайдера\n"
            "• /deletekey - удалить API-ключ текущего провайдера\n"
            "• /model - задать модель\n"
            "• /baseurl - задать base URL (custom-провайдер)\n"
            "• /settings - показать настройки\n"
            "• /history - история сохранённых чатов\n"
            "• /newchat - начать новый чат\n"
            "• /cancel - отменить ввод"
        ),
        "choose_language": "🌐 Выберите язык интерфейса:",
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
        "api_key_saved": "✅ API-ключ сохранён для {provider}.",
        "provider_auto_switched": "🔄 Определён ключ {detected}. Провайдер переключён: {from_provider} → {to_provider}.",
        "api_key_removed": "🗑️ API-ключ удалён для {provider}.",
        "ask_model": "🧠 Отправьте имя модели (пример: gpt-4o-mini).",
        "model_saved": "✅ Модель установлена: {model}",
        "choose_model_preset": "🧠 Выберите модель моего ИИ:",
        "model_preset_changed": "✅ Модель моего ИИ изменена: {model}",
        "model_personal_api_enabled": (
            "🔐 Режим своего API включён.\n"
            "Теперь используйте /apikey для своего ключа и /model для ввода имени модели."
        ),
        "model_personal_api_missing_key": "⚠️ Включён режим своего API, но ключ не задан. Используйте /apikey.",
        "shared_quota_exceeded": "⚠️ Вы израсходовали лимит общего ИИ ({limit} токенов). Переключитесь на Свой API.",
        "shared_ai_not_configured": "⚠️ Общий ИИ временно недоступен. Свяжитесь с админом.",
        "access_mode_shared": "Мой ИИ",
        "access_mode_personal": "Свой API",
        "model_gpt4": "GPT 4",
        "model_llama3": "LLAMA 3",
        "model_llama4_media": "LLAMA 4 (Media)",
        "btn_own_api": "🔐 Свой API",
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
        "history_cleared": "🗑️ История очищена.",
        "new_chat_started": "🆕 Начат новый чат.",
        "new_chat_already_empty": "ℹ️ В текущем чате нет сообщений. История не изменена.",
        "no_history": "📭 История пуста.",
        "history_title": "🕘 Последние сообщения:",
        "history_chat_view": "🗂️ Чат {current}/{total}\n🏷️ Название: {title}\n💬 Сообщений: {messages}\n🕘 Последнее: {content}",
        "untitled_chat": "Без названия",
        "processing": "⏳ Думаю...",
        "media_image_default_prompt": "Опиши это изображение.",
        "unsupported_media_type": "⚠️ Этот тип медиа пока не поддерживается. Отправьте текст, фото или файл-изображение.",
        "media_too_large": "⚠️ Изображение слишком большое. Максимальный размер: {max_mb} МБ.",
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
        "btn_custom_instructions": "🧾 Кастомные инструкции",
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
        "personality_marketer": "📈 Маркетолог",
        "personality_product_manager": "🗂️ Продакт-менеджер",
        "personality_writer": "✍️ Писатель",
        "personality_comedian": "😂 Юморист",
        "personality_poet": "🪶 Поэт",
        "personality_philosopher": "🏛️ Философ",
        "personality_genius": "🧬 Гений",
        "personality_manipulator": "🎭 Манипулятор",
        "personality_liar": "🤥 Лжец",
        "personality_historian": "📜 Историк",
        "personality_critic": "🔍 Критик",
        "system_prompt": "Ты полезный AI-ассистент. Всегда отвечай на {language_name}.",
        "invalid_url": "⚠️ Неверный URL. Отправьте полный URL, начинающийся с http:// или https://",
        "history_item_view": "🗂️ История {current}/{total}\n{role}: {content}",
    },
    "es": {
        "lang_name": "Espanol",
        "welcome": (
            "Bienvenido. Este bot funciona solo con tu propia clave API.\n"
            "Configura proveedor y clave, luego empieza a chatear."
        ),
        "help": (
            "Comandos:\n"
            "/language - elegir idioma\n"
            "/provider - elegir proveedor de IA\n"
            "/personality - elegir personalidad de IA\n"
            "/apikey - guardar clave API del proveedor actual\n"
            "/deletekey - borrar clave del proveedor actual\n"
            "/model - definir modelo\n"
            "/baseurl - definir URL base (proveedor custom)\n"
            "/settings - mostrar configuracion\n"
            "/history - mostrar historial reciente\n"
            "/newchat - limpiar memoria/historial"
        ),
        "choose_language": "Elige idioma:",
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
        "btn_personality": "🎭 Personalidad",
        "btn_custom_instructions": "🧾 Instrucciones custom",
        "personality_default": "🧩 Asistente universal",
        "personality_lawyer": "⚖️ Jurista",
        "personality_advocate": "🛡️ Abogado defensor",
        "personality_psychologist": "🧠 Psicologo",
        "personality_programmer": "💻 Programador",
        "personality_teacher": "📚 Profesor",
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
            "/language - choisir la langue\n"
            "/provider - choisir le fournisseur IA\n"
            "/personality - choisir une personnalite IA\n"
            "/apikey - enregistrer la cle API du fournisseur actuel\n"
            "/deletekey - supprimer la cle du fournisseur actuel\n"
            "/model - definir le modele\n"
            "/baseurl - definir URL de base (fournisseur custom)\n"
            "/settings - afficher les parametres\n"
            "/history - afficher l'historique recent\n"
            "/newchat - effacer la memoire/historique"
        ),
        "choose_language": "Choisissez la langue:",
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
        "btn_personality": "🎭 Personnalite",
        "btn_custom_instructions": "🧾 Instructions custom",
        "personality_default": "🧩 Assistant universel",
        "personality_lawyer": "⚖️ Juriste",
        "personality_advocate": "🛡️ Avocat",
        "personality_psychologist": "🧠 Psychologue",
        "personality_programmer": "💻 Programmeur",
        "personality_teacher": "📚 Enseignant",
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
            "/language - dil sec\n"
            "/provider - AI saglayici sec\n"
            "/personality - AI kisiligi sec\n"
            "/apikey - mevcut saglayici icin API anahtari kaydet\n"
            "/deletekey - mevcut saglayici anahtarini sil\n"
            "/model - model adi ayarla\n"
            "/baseurl - temel URL ayarla (custom saglayici)\n"
            "/settings - ayarlari goster\n"
            "/history - son sohbet gecmisini goster\n"
            "/newchat - hafiza/gecmisi temizle"
        ),
        "choose_language": "Dil secin:",
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
        "btn_personality": "🎭 Kisilik",
        "btn_custom_instructions": "🧾 Ozel talimatlar",
        "personality_default": "🧩 Evrensel asistan",
        "personality_lawyer": "⚖️ Hukukcu",
        "personality_advocate": "🛡️ Avukat",
        "personality_psychologist": "🧠 Psikolog",
        "personality_programmer": "💻 Programci",
        "personality_teacher": "📚 Ogretmen",
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
        "system_prompt": "Yardimci bir AI asistansiniz. Her zaman {language_name} dilinde cevap verin.",
        "invalid_url": "Gecersiz URL. http:// veya https:// ile tam URL gonderin",
    },
    "ar": {
        "lang_name": "العربية",
        "welcome": "مرحبا. هذا البوت يعمل فقط بمفتاح API الخاص بك. اختر المزود والمفتاح ثم ابدأ المحادثة.",
        "help": (
            "الاوامر:\n"
            "/language - اختيار اللغة\n"
            "/provider - اختيار مزود الذكاء الاصطناعي\n"
            "/personality - اختيار شخصية الذكاء الاصطناعي\n"
            "/apikey - حفظ مفتاح API للمزود الحالي\n"
            "/deletekey - حذف مفتاح المزود الحالي\n"
            "/model - تحديد اسم النموذج\n"
            "/baseurl - تحديد الرابط الاساسي (للمزود المخصص)\n"
            "/settings - عرض الاعدادات\n"
            "/history - عرض اخر سجل محادثة\n"
            "/newchat - مسح الذاكرة والسجل"
        ),
        "choose_language": "اختر اللغة:",
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
        "btn_personality": "🎭 الشخصية",
        "btn_custom_instructions": "🧾 تعليمات مخصصة",
        "personality_default": "🧩 مساعد عام",
        "personality_lawyer": "⚖️ مستشار قانوني",
        "personality_advocate": "🛡️ محامي دفاع",
        "personality_psychologist": "🧠 اخصائي نفسي",
        "personality_programmer": "💻 مبرمج",
        "personality_teacher": "📚 معلم",
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
        "system_prompt": "انت مساعد ذكاء اصطناعي مفيد. اجب دائما باللغة {language_name}.",
        "invalid_url": "رابط غير صالح. ارسل رابطا كاملا يبدأ بـ http:// او https://",
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
