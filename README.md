# Telegram AI Bot (User API Keys)

Телеграм-бот, который отвечает через ИИ только по API-ключу самого пользователя.

## Возможности

- Поддержка провайдеров: OpenAI, Groq, OpenRouter, Together AI, DeepInfra, Custom OpenAI-compatible.
- Для каждого пользователя: свой провайдер, свой API-ключ, своя модель.
- API-ключи хранятся в SQLite в зашифрованном виде (Fernet).
- Память/контекст диалога и история чата.
- Интерфейс на 6 языках: English, Русский, Espanol, Francais, Turkce, العربية.

## Структура

- `app.py` - точка входа
- `bot/main.py` - запуск polling
- `bot/handlers.py` - Telegram команды и чат-логика
- `bot/db.py` - SQLite + зашифрованные ключи
- `bot/llm/service.py` - вызов LLM через OpenAI SDK
- `bot/llm/providers.py` - конфигурация провайдеров
- `bot/i18n.py` - локализация

## Установка (в venv)

```bash
python -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

## Настройка

1. Скопируйте `.env.example` в `.env`.
2. Создайте ключ шифрования:

```bash
venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

3. Заполните `.env`:

```env
TELEGRAM_BOT_TOKEN=...
DATA_ENCRYPTION_KEY=...
DATABASE_PATH=data/bot.db
DEFAULT_LANGUAGE=en
DEFAULT_PROVIDER=openai
MEMORY_MESSAGES=20
```

## Запуск

```bash
venv/bin/python app.py
```

## Команды бота

- `/language` - выбор языка интерфейса
- `/menu` - открыть inline-меню с навигацией
- `/provider` - выбор AI-провайдера
- `/apikey` - сохранить API-ключ текущего провайдера
- `/deletekey` - удалить API-ключ текущего провайдера
- `/model` - установить модель
- `/baseurl` - установить base URL (для custom-провайдера)
- `/settings` - показать текущие настройки
- `/history` - показать последние сообщения
- `/newchat` - очистить историю/память
- `/cancel` - выйти из режима ввода значения

## Примечания

- Бот не использует глобальные LLM-ключи: ответ возможен только если пользователь сам сохранил ключ.
- Для `custom` провайдера нужно задать `/baseurl`.
- История и ключи привязаны к `telegram user_id`.
