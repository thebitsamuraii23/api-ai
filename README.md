# UrAI Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge)](https://github.com/aiogram/aiogram)
[![OpenAI SDK](https://img.shields.io/badge/OpenAI%20SDK-1.x-412991?style=for-the-badge)](https://github.com/openai/openai-python)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Encryption](https://img.shields.io/badge/API%20Keys-End--to--End%20Encrypted-0A7B34?style=for-the-badge)](#security--encryption)
[![Privacy Deep Dive](https://img.shields.io/badge/Privacy-PRIVACY__AND__ENCRYPTION.md-1f6feb?style=for-the-badge)](https://github.com/thebitsamuraii23/api-ai/blob/main/PRIVACY_AND_ENCRYPTION.md)

Production-ready Telegram AI bot with per-user provider settings, per-user model control, encrypted API key storage, chat history, persona switching, media support, and multilingual interface.

more learn at: https://github.com/thebitsamuraii23/api-ai/blob/main/PRIVACY_AND_ENCRYPTION.md

## Visual Preview

![UrAI Repository Preview](https://opengraph.githubassets.com/1/thebitsamuraii23/api-ai)

## Table of Contents

- [Key Features](#key-features)
- [Security & Encryption](#security--encryption)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Bot Commands](#bot-commands)
- [Web Search Modes](#web-search-modes)
- [Privacy Quick Links](#privacy-quick-links)
- [Development Notes](#development-notes)
- [Other Projects](#other-projects)
- [Credits](#credits)

## Key Features

- Multi-provider support: OpenAI, Groq, OpenRouter, Together AI, DeepInfra, and custom OpenAI-compatible endpoints.
- Per-user runtime isolation:
  - independent provider selection
  - independent API key
  - independent model and personality
- Shared AI mode with token quota controls.
- Personal API mode with user-owned credentials.
- Built-in chat memory and chat history navigation.
- Media-ready flow (text, images, voice, files).
- Internet search integration with configurable backend strategy.
- Rich Telegram UI:
  - reply keyboard for daily actions
  - inline settings hub and navigation menus
- Multilingual interface (11 languages):
  - English (`en`)
  - Russian (`ru`)
  - Spanish (`es`)
  - French (`fr`)
  - Turkish (`tr`)
  - Arabic (`ar`)
  - German (`de`)
  - Italian (`it`)
  - Portuguese (`pt`)
  - Ukrainian (`uk`)
  - Hindi (`hi`)

## Security & Encryption

All user API keys are handled through an end-to-end encrypted storage flow.

- API keys are encrypted before being persisted.
- Encrypted values are stored in SQLite (`api_keys.encrypted_key`).
- Decryption requires the private `DATA_ENCRYPTION_KEY` configured on your deployment.
- The bot developer does not have access to your plaintext API keys.

For encryption key generation and operational recommendations, see [`ENCRYPTION_SETUP.md`](ENCRYPTION_SETUP.md).

For the full privacy and data-flow deep dive:
- more learn at: https://github.com/thebitsamuraii23/api-ai/blob/main/PRIVACY_AND_ENCRYPTION.md
- in bot: use `/privacy`

## Architecture

- Runtime: `aiogram`-based Telegram polling bot.
- LLM transport: OpenAI-compatible SDK abstraction (`bot/llm/service.py`).
- Storage: SQLite with async access via `aiosqlite`.
- Secrets protection: Fernet encryption for API keys.
- Orchestration: command handlers + callback routing in `bot/handlers.py`.

```mermaid
flowchart LR
    User[Telegram User] --> Bot[UrAI Bot Runtime]
    Bot --> DB[(SQLite)]
    Bot --> Provider[AI Provider API]
    Key[DATA_ENCRYPTION_KEY] --> Bot
    Bot -->|Encrypt API key (Fernet)| DB
```

## Project Structure

```text
.
├── app.py                      # CLI entrypoint
├── bot/
│   ├── main.py                 # bot startup, command registration, polling
│   ├── handlers.py             # commands, callbacks, chat workflow
│   ├── keyboards.py            # inline/reply keyboard builders
│   ├── i18n.py                 # localization dictionary
│   ├── db.py                   # SQLite schema and data access
│   ├── config.py               # environment config loader
│   ├── web_search.py           # web search integration layer
│   └── llm/
│       ├── providers.py        # provider definitions
│       └── service.py          # provider-agnostic LLM calls
├── data/                       # local database files
├── .env.example                # environment template
└── README.md
```

## Requirements

- Python 3.10+
- Telegram bot token from BotFather
- Optional provider API keys (per user or shared mode)

## Quick Start

1. Clone the repository.
2. Create a virtual environment.
3. Install dependencies.
4. Create `.env` from `.env.example`.
5. Generate and set `DATA_ENCRYPTION_KEY`.
6. Start the bot.

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Run

```bash
python app.py
```

## Configuration

Copy `.env.example` to `.env` and configure at least:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATA_ENCRYPTION_KEY=your_fernet_key
DATABASE_PATH=data/bot.db
DEFAULT_LANGUAGE=en
DEFAULT_PROVIDER=openai
MEMORY_MESSAGES=20
```

Important optional settings:

- `SHARED_API_KEY`, `SHARED_PROVIDER`, `SHARED_TOKEN_QUOTA`
- `OPENAI_WEB_SEARCH`, `OPENAI_WEB_SEARCH_TOOL_CHOICE`
- `EXTERNAL_WEB_SEARCH_MODE`, `EXTERNAL_WEB_SEARCH_MAX_RESULTS`
- `WEB_SEARCH_BACKEND`

## Bot Commands

- `/start` - quick onboarding and control keyboard
- `/privacy` - detailed privacy, encryption, and data-flow overview
- `/settings` - settings hub and configuration shortcuts
- `/languages` - switch interface language
- `/provider` - choose provider
- `/apikey` - save API key for active provider
- `/deletekey` - delete API key for active provider
- `/model` - set model or shared model preset
- `/baseurl` - set custom provider base URL
- `/personality` - select assistant persona
- `/tokens` or `/limit` - view token status
- `/history` - open saved chat history
- `/newchat` - start a fresh chat context
- `/i "query"` - internet search flow
- `/cancel` - exit input mode

Privacy hint for users:
- more learn at: https://github.com/thebitsamuraii23/api-ai/blob/main/PRIVACY_AND_ENCRYPTION.md

## Web Search Modes

`WEB_SEARCH_BACKEND` controls where search is executed:

- `server`: search runs from your bot server/network
- `openai`: search runs through OpenAI built-in tooling
- `hybrid`: both modes available depending on runtime logic

## Privacy Quick Links

- Command: `/privacy`
- Deep dive: [PRIVACY_AND_ENCRYPTION.md](PRIVACY_AND_ENCRYPTION.md)
- more learn at: https://github.com/thebitsamuraii23/api-ai/blob/main/PRIVACY_AND_ENCRYPTION.md

## Development Notes

- Command definitions are registered in `bot/main.py`.
- Core business logic lives in `bot/handlers.py`.
- Localization fallback resolves missing keys to English.
- The repository includes additional technical docs:
  - `ENCRYPTION_SETUP.md`
  - `PRIVACY_AND_ENCRYPTION.md`
  - `MARKDOWN_IMPLEMENTATION.md`
  - `MARKDOWNV2_ESCAPING_GUIDE.md`

## Other Projects

- UrZen: [urzen.site](https://urzen.site)
- Repository: [github.com/thebitsamuraii23/UrZen-player](https://github.com/thebitsamuraii23/UrZen-player)

![UrZen Repository Preview](https://opengraph.githubassets.com/1/thebitsamuraii23/UrZen-player)

## Credits

Bot developed by thebitsamurai ([github.com/thebitsamuraii23](https://github.com/thebitsamuraii23)).
