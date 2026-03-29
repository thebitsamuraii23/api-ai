from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import uuid4

import aiosqlite
from cryptography.fernet import Fernet


@dataclass(slots=True)
class UserSettings:
    user_id: int
    language: str
    language_confirmed: bool
    provider: str
    model: str
    personality: str
    custom_base_url: str | None
    active_chat_id: int | None
    use_personal_api: bool
    quota_used: int


@dataclass(slots=True)
class ChatSummary:
    chat_id: int
    title: str
    message_count: int
    last_message: str
    updated_at: str


@dataclass(slots=True)
class CustomPersonality:
    personality_id: str
    title: str
    instructions: str


class Database:
    def __init__(
        self,
        *,
        db_path: str,
        encryption_key: str,
        default_language: str,
        default_provider: str,
    ) -> None:
        self.db_path = db_path
        self.default_language = default_language
        self.default_provider = default_provider
        self._fernet = Fernet(encryption_key.encode("utf-8"))

    @asynccontextmanager
    async def _connect(self):
        conn = await aiosqlite.connect(self.db_path, timeout=30.0)
        try:
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")
            await conn.execute("PRAGMA busy_timeout = 30000")
            yield conn
        finally:
            await conn.close()

    async def init(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        async with self._connect() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT '',
                    personality TEXT NOT NULL DEFAULT 'default',
                    custom_base_url TEXT,
                    active_chat_id INTEGER,
                    language_confirmed INTEGER NOT NULL DEFAULT 0,
                    use_personal_api INTEGER NOT NULL DEFAULT 0,
                    quota_used INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            if not await self._column_exists(conn, "users", "active_chat_id"):
                await conn.execute("ALTER TABLE users ADD COLUMN active_chat_id INTEGER")
            if not await self._column_exists(conn, "users", "personality"):
                await conn.execute("ALTER TABLE users ADD COLUMN personality TEXT NOT NULL DEFAULT 'default'")
            if not await self._column_exists(conn, "users", "language_confirmed"):
                await conn.execute(
                    "ALTER TABLE users ADD COLUMN language_confirmed INTEGER NOT NULL DEFAULT 0"
                )
                await conn.execute("UPDATE users SET language_confirmed = 1")
            if not await self._column_exists(conn, "users", "use_personal_api"):
                await conn.execute("ALTER TABLE users ADD COLUMN use_personal_api INTEGER NOT NULL DEFAULT 0")
            if not await self._column_exists(conn, "users", "quota_used"):
                await conn.execute("ALTER TABLE users ADD COLUMN quota_used INTEGER NOT NULL DEFAULT 0")
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, provider),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            if not await self._column_exists(conn, "messages", "chat_id"):
                await conn.execute("ALTER TABLE messages ADD COLUMN chat_id INTEGER")
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_personalities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    personality_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """
            )
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_chat_id ON messages(user_id, chat_id, id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_updated ON chats(user_id, updated_at DESC)")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_custom_personalities_user_updated "
                "ON custom_personalities(user_id, updated_at DESC, id DESC)"
            )
            await self._migrate_messages_to_chats(conn)
            await conn.commit()

    async def ensure_user(self, user_id: int) -> None:
        async with self._connect() as conn:
            await conn.execute(
                """
                INSERT INTO users(user_id, language, language_confirmed, provider, model, personality, use_personal_api, quota_used)
                VALUES (?, ?, 0, ?, 'llama4_media', 'default', 0, 0)
                ON CONFLICT(user_id) DO NOTHING
                """,
                (user_id, self.default_language, self.default_provider),
            )
            await conn.commit()

    async def get_user_settings(self, user_id: int) -> UserSettings:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT
                    user_id,
                    language,
                    language_confirmed,
                    provider,
                    model,
                    personality,
                    custom_base_url,
                    active_chat_id,
                    use_personal_api,
                    quota_used
                FROM users
                WHERE user_id = ?
                """,
                (user_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return UserSettings(
                user_id=user_id,
                language=self.default_language,
                language_confirmed=False,
                provider=self.default_provider,
                model="",
                personality="default",
                custom_base_url=None,
                active_chat_id=None,
                use_personal_api=False,
                quota_used=0,
            )
        return UserSettings(
            user_id=row["user_id"],
            language=row["language"],
            language_confirmed=bool(row["language_confirmed"]),
            provider=row["provider"],
            model=row["model"],
            personality=row["personality"] or "default",
            custom_base_url=row["custom_base_url"],
            active_chat_id=row["active_chat_id"],
            use_personal_api=bool(row["use_personal_api"]),
            quota_used=int(row["quota_used"] or 0),
        )

    async def set_language(self, user_id: int, language: str, *, confirmed: bool = True) -> None:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            await conn.execute(
                """
                UPDATE users
                SET language = ?,
                    language_confirmed = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (language, int(confirmed), user_id),
            )
            await conn.commit()

    async def set_provider(self, user_id: int, provider: str) -> None:
        await self.ensure_user(user_id)
        await self._set_user_field(user_id, "provider", provider)

    async def set_model(self, user_id: int, model: str) -> None:
        await self.ensure_user(user_id)
        await self._set_user_field(user_id, "model", model.strip())

    async def set_personality(self, user_id: int, personality: str) -> None:
        await self.ensure_user(user_id)
        await self._set_user_field(user_id, "personality", personality.strip())

    async def set_use_personal_api(self, user_id: int, enabled: bool) -> None:
        await self.ensure_user(user_id)
        await self._set_user_field(user_id, "use_personal_api", int(enabled))

    async def set_quota_used(self, user_id: int, quota_used: int) -> None:
        await self.ensure_user(user_id)
        value = max(0, int(quota_used))
        await self._set_user_field(user_id, "quota_used", value)

    async def add_quota_used(self, user_id: int, delta: int) -> None:
        await self.ensure_user(user_id)
        delta_value = int(delta)
        async with self._connect() as conn:
            await conn.execute(
                """
                UPDATE users
                SET quota_used = MAX(0, COALESCE(quota_used, 0) + ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (delta_value, user_id),
            )
            await conn.commit()

    async def create_custom_personality(
        self,
        user_id: int,
        instructions: str,
        *,
        title: str | None = None,
    ) -> CustomPersonality:
        await self.ensure_user(user_id)
        clean_instructions = instructions.strip()
        if not clean_instructions:
            raise ValueError("Instructions cannot be empty")
        clean_title = self._normalize_custom_personality_title(title)
        if not clean_title:
            clean_title = self._custom_personality_title(clean_instructions)
        temporary_personality_id = f"tmp_{uuid4().hex}"

        async with self._connect() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO custom_personalities(user_id, personality_id, title, instructions)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, temporary_personality_id, clean_title, clean_instructions),
            )
            row_id = int(cursor.lastrowid)
            personality_id = f"custom_{row_id}"
            await conn.execute(
                """
                UPDATE custom_personalities
                SET personality_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (personality_id, row_id, user_id),
            )
            await conn.commit()

        return CustomPersonality(
            personality_id=personality_id,
            title=clean_title,
            instructions=clean_instructions,
        )

    async def get_custom_personality(self, user_id: int, personality_id: str) -> CustomPersonality | None:
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT personality_id, title, instructions
                FROM custom_personalities
                WHERE user_id = ? AND personality_id = ?
                """,
                (user_id, personality_id.strip()),
            )
            row = await cursor.fetchone()

        if row is None:
            return None
        return CustomPersonality(
            personality_id=row["personality_id"],
            title=row["title"],
            instructions=row["instructions"],
        )

    async def update_custom_personality_instructions(
        self,
        user_id: int,
        personality_id: str,
        instructions: str,
    ) -> CustomPersonality | None:
        await self.ensure_user(user_id)
        clean_instructions = instructions.strip()
        if not clean_instructions:
            raise ValueError("Instructions cannot be empty")

        pid = personality_id.strip()
        updated = 0
        async with self._connect() as conn:
            cursor = await conn.execute(
                """
                UPDATE custom_personalities
                SET instructions = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND personality_id = ?
                """,
                (clean_instructions, user_id, pid),
            )
            updated = int(cursor.rowcount or 0)
            await conn.commit()

        if updated == 0:
            return None
        return await self.get_custom_personality(user_id, pid)

    async def update_custom_personality_title(
        self,
        user_id: int,
        personality_id: str,
        title: str,
    ) -> CustomPersonality | None:
        await self.ensure_user(user_id)
        clean_title = self._normalize_custom_personality_title(title)
        if not clean_title:
            raise ValueError("Title cannot be empty")

        pid = personality_id.strip()
        async with self._connect() as conn:
            cursor = await conn.execute(
                """
                UPDATE custom_personalities
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND personality_id = ?
                """,
                (clean_title, user_id, pid),
            )
            updated = int(cursor.rowcount or 0)
            await conn.commit()

        if updated == 0:
            return None
        return await self.get_custom_personality(user_id, pid)

    async def list_custom_personalities(self, user_id: int, limit: int = 20) -> list[CustomPersonality]:
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT personality_id, title, instructions
                FROM custom_personalities
                WHERE user_id = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()

        return [
            CustomPersonality(
                personality_id=row["personality_id"],
                title=row["title"],
                instructions=row["instructions"],
            )
            for row in rows
        ]

    async def delete_custom_personality(self, user_id: int, personality_id: str) -> bool:
        await self.ensure_user(user_id)
        pid = personality_id.strip()
        async with self._connect() as conn:
            cursor = await conn.execute(
                """
                DELETE FROM custom_personalities
                WHERE user_id = ? AND personality_id = ?
                """,
                (user_id, pid),
            )
            await conn.execute(
                """
                UPDATE users
                SET personality = 'default', updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND personality = ?
                """,
                (user_id, pid),
            )
            await conn.commit()

        return int(cursor.rowcount or 0) > 0

    async def set_custom_base_url(self, user_id: int, base_url: str) -> None:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            await conn.execute(
                """
                UPDATE users
                SET custom_base_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (base_url.strip(), user_id),
            )
            await conn.commit()

    async def _set_user_field(self, user_id: int, field: str, value: str | int) -> None:
        async with self._connect() as conn:
            await conn.execute(
                f"UPDATE users SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (value, user_id),
            )
            await conn.commit()

    async def set_api_key(self, user_id: int, provider: str, api_key: str) -> None:
        await self.ensure_user(user_id)
        encrypted_key = self._fernet.encrypt(api_key.encode("utf-8")).decode("utf-8")
        async with self._connect() as conn:
            await conn.execute(
                """
                INSERT INTO api_keys(user_id, provider, encrypted_key)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, provider)
                DO UPDATE SET encrypted_key = excluded.encrypted_key, updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, provider, encrypted_key),
            )
            await conn.commit()

    async def get_api_key(self, user_id: int, provider: str) -> str | None:
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT encrypted_key FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        encrypted = row["encrypted_key"]
        return self._fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")

    async def delete_api_key(self, user_id: int, provider: str) -> None:
        async with self._connect() as conn:
            await conn.execute(
                "DELETE FROM api_keys WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            )
            await conn.commit()

    async def add_message(self, user_id: int, role: str, content: str, *, chat_id: int) -> None:
        async with self._connect() as conn:
            await conn.execute(
                "INSERT INTO messages(user_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
                (user_id, chat_id, role, content),
            )
            await conn.execute(
                "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (chat_id, user_id),
            )
            await conn.commit()

    async def get_recent_messages(self, user_id: int, limit: int, *, chat_id: int | None = None) -> list[dict[str, str]]:
        target_chat_id = chat_id if chat_id is not None else await self.get_active_chat_id(user_id)
        if target_chat_id is None:
            return []
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT role, content
                FROM messages
                WHERE user_id = ? AND chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, target_chat_id, limit),
            )
            rows = await cursor.fetchall()
        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    async def get_active_chat_id(self, user_id: int) -> int | None:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            cursor = await conn.execute("SELECT active_chat_id FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return row[0]

    async def create_chat(self, user_id: int, *, title: str = "") -> int:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            cursor = await conn.execute(
                "INSERT INTO chats(user_id, title) VALUES (?, ?)",
                (user_id, title.strip()),
            )
            chat_id = cursor.lastrowid
            await conn.execute(
                """
                UPDATE users
                SET active_chat_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (chat_id, user_id),
            )
            await conn.commit()
        return int(chat_id)

    async def set_active_chat(self, user_id: int, chat_id: int | None) -> None:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            await conn.execute(
                """
                UPDATE users
                SET active_chat_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (chat_id, user_id),
            )
            await conn.commit()

    async def set_chat_title(self, user_id: int, chat_id: int, title: str) -> None:
        clean_title = title.strip()
        if not clean_title:
            return
        async with self._connect() as conn:
            await conn.execute(
                """
                UPDATE chats
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (clean_title, chat_id, user_id),
            )
            await conn.commit()

    async def chat_message_count(self, user_id: int, chat_id: int) -> int:
        async with self._connect() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            row = await cursor.fetchone()
        return int(row[0] if row else 0)

    async def get_recent_chats(self, user_id: int, limit: int) -> list[ChatSummary]:
        async with self._connect() as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT
                    c.id AS chat_id,
                    c.title AS title,
                    c.updated_at AS updated_at,
                    COALESCE(COUNT(m.id), 0) AS message_count,
                    COALESCE((
                        SELECT m2.content
                        FROM messages m2
                        WHERE m2.chat_id = c.id
                        ORDER BY m2.id DESC
                        LIMIT 1
                    ), '') AS last_message
                FROM chats c
                LEFT JOIN messages m ON m.chat_id = c.id
                WHERE c.user_id = ?
                GROUP BY c.id, c.title, c.updated_at
                HAVING message_count > 0
                ORDER BY c.updated_at DESC, c.id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()

        return [
            ChatSummary(
                chat_id=row["chat_id"],
                title=row["title"] or "",
                message_count=int(row["message_count"] or 0),
                last_message=row["last_message"] or "",
                updated_at=row["updated_at"] or "",
            )
            for row in rows
        ]

    async def start_new_chat(self, user_id: int) -> bool:
        await self.ensure_user(user_id)
        active_chat_id = await self.get_active_chat_id(user_id)
        if active_chat_id is None:
            return False

        message_count = await self.chat_message_count(user_id, active_chat_id)
        async with self._connect() as conn:
            if message_count == 0:
                await conn.execute(
                    "DELETE FROM chats WHERE id = ? AND user_id = ?",
                    (active_chat_id, user_id),
                )
            await conn.execute(
                """
                UPDATE users
                SET active_chat_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            await conn.commit()
        return message_count > 0

    async def delete_chat(self, user_id: int, chat_id: int) -> None:
        await self.ensure_user(user_id)
        async with self._connect() as conn:
            await conn.execute(
                "DELETE FROM messages WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
            await conn.execute(
                "DELETE FROM chats WHERE id = ? AND user_id = ?",
                (chat_id, user_id),
            )
            await conn.execute(
                """
                UPDATE users
                SET active_chat_id = CASE WHEN active_chat_id = ? THEN NULL ELSE active_chat_id END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (chat_id, user_id),
            )
            await conn.commit()

    async def _column_exists(self, conn: aiosqlite.Connection, table: str, column: str) -> bool:
        cursor = await conn.execute(f"PRAGMA table_info({table})")
        rows = await cursor.fetchall()
        return any(row[1] == column for row in rows)

    async def _migrate_messages_to_chats(self, conn: aiosqlite.Connection) -> None:
        cursor = await conn.execute("SELECT DISTINCT user_id FROM messages WHERE chat_id IS NULL")
        rows = await cursor.fetchall()
        for (user_id,) in rows:
            existing_active = await conn.execute(
                "SELECT active_chat_id FROM users WHERE user_id = ?",
                (user_id,),
            )
            active_row = await existing_active.fetchone()
            active_chat_id = active_row[0] if active_row else None

            if active_chat_id is None:
                title = "Imported chat"
                chat_insert = await conn.execute(
                    "INSERT INTO chats(user_id, title) VALUES (?, ?)",
                    (user_id, title),
                )
                active_chat_id = int(chat_insert.lastrowid)
                await conn.execute(
                    """
                    UPDATE users
                    SET active_chat_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (active_chat_id, user_id),
                )

            await conn.execute(
                "UPDATE messages SET chat_id = ? WHERE user_id = ? AND chat_id IS NULL",
                (active_chat_id, user_id),
            )

    @staticmethod
    def _custom_personality_title(instructions: str) -> str:
        first_line = instructions.splitlines()[0].strip() if instructions else ""
        title = first_line[:42].strip() if first_line else "Custom instructions"
        if len(first_line) > 42:
            title = f"{title.rstrip()}..."
        return title or "Custom instructions"

    @staticmethod
    def _normalize_custom_personality_title(raw_title: str | None) -> str | None:
        if raw_title is None:
            return None
        title = raw_title.strip()
        if not title:
            return None
        if len(title) <= 42:
            return title
        return f"{title[:39].rstrip()}..."
