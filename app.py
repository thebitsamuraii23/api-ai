from __future__ import annotations

import argparse
import asyncio
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from bot.main import run


APP_NAME = "UrAI"
APP_VERSION = "1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="Run Telegram bot that uses user-provided API keys.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable startup banner output.",
    )
    parser.add_argument(
        "--show-env-hint",
        action="store_true",
        help="Show .env file status before startup.",
    )
    return parser


def print_banner(*, show_env_hint: bool) -> None:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"🚀 {APP_NAME} v{APP_VERSION}")
    print(f"🕒 Started at: {now_utc}")
    print(f"🐍 Python: {platform.python_version()} ({platform.system()})")
    print(f"📁 Working dir: {Path.cwd()}")

    if show_env_hint:
        env_path = Path(".env")
        status = "✅ found" if env_path.exists() else "⚠️ missing"
        print(f"🔧 .env status: {status}")


def main() -> None:
    args = build_parser().parse_args()

    if not args.quiet:
        print_banner(show_env_hint=args.show_env_hint)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
