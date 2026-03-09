from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import load_settings
from bot.db import Database
from bot.handlers import build_router
from bot.llm.service import LLMService


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = load_settings()

    db = Database(
        db_path=settings.database_path,
        encryption_key=settings.data_encryption_key,
        default_language=settings.default_language,
        default_provider=settings.default_provider,
    )
    await db.init()

    llm = LLMService()
    router = build_router(db=db, llm=llm, settings=settings)

    bot = Bot(token=settings.telegram_bot_token)
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="👋 Start bot"),
            BotCommand(command="menu", description="✨ Open menu"),
            BotCommand(command="help", description="📚 Help"),
            BotCommand(command="language", description="🌐 Change language"),
            BotCommand(command="provider", description="🤖 Choose provider"),
            BotCommand(command="personality", description="🎭 Choose personality"),
            BotCommand(command="apikey", description="🔐 Set API key"),
            BotCommand(command="deletekey", description="🗑️ Delete API key"),
            BotCommand(command="model", description="🧠 Set model"),
            BotCommand(command="baseurl", description="🔗 Set base URL"),
            BotCommand(command="settings", description="⚙️ View settings"),
            BotCommand(command="history", description="🗂️ Chat history"),
            BotCommand(command="newchat", description="🆕 New chat"),
            BotCommand(command="cancel", description="❌ Cancel input"),
        ]
    )
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
