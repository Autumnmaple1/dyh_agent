"""SQLite 持久化层。

负责将 Session 及其消息落盘到 SQLite，并支持启动时全量加载恢复。
所有函数均为同步阻塞实现，调用方需通过 asyncio.to_thread 包装以避免阻塞事件循环。
"""
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from app.schemas import ChatMessage, ChatMode, StoryMemory

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_db_path(db_path: str) -> Path:
    path = Path(db_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(_resolve_db_path(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str) -> None:
    path = _resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(str(path)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                turn INTEGER NOT NULL DEFAULT 0,
                summary TEXT NOT NULL DEFAULT '',
                context_start_index INTEGER NOT NULL DEFAULT 0,
                compacted_message_count INTEGER NOT NULL DEFAULT 0,
                estimated_active_tokens INTEGER NOT NULL DEFAULT 0,
                suggestions TEXT NOT NULL DEFAULT '[]',
                story_scene TEXT,
                story_current_beat TEXT,
                story_actions TEXT,
                story_outcome TEXT,
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                seq INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                UNIQUE(session_id, seq)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            """
        )
        # 旧库迁移：为已存在的 sessions 表补充 suggestions 列。
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        if "suggestions" not in columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN suggestions TEXT NOT NULL DEFAULT '[]'")


def save_session(db_path: str, session: Any) -> None:
    """写穿保存整个会话：upsert 会话行并全量重写其消息。"""
    story = session.story_memory
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sessions (
                id, owner_id, character_id, mode, turn, summary,
                context_start_index, compacted_message_count, estimated_active_tokens,
                suggestions, story_scene, story_current_beat, story_actions, story_outcome, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                turn = excluded.turn,
                summary = excluded.summary,
                context_start_index = excluded.context_start_index,
                compacted_message_count = excluded.compacted_message_count,
                estimated_active_tokens = excluded.estimated_active_tokens,
                suggestions = excluded.suggestions,
                story_scene = excluded.story_scene,
                story_current_beat = excluded.story_current_beat,
                story_actions = excluded.story_actions,
                story_outcome = excluded.story_outcome,
                updated_at = excluded.updated_at
            """,
            (
                session.id,
                session.owner_id,
                session.character_id,
                session.mode.value,
                session.turn,
                session.summary,
                session.context_start_index,
                session.compacted_message_count,
                session.estimated_active_tokens,
                json.dumps(session.suggestions, ensure_ascii=False) if session.suggestions else "[]",
                story.scene if story else None,
                story.current_beat if story else None,
                json.dumps(story.key_player_actions, ensure_ascii=False) if story else None,
                story.last_outcome if story else None,
                time.time(),
            ),
        )
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))
        conn.executemany(
            "INSERT INTO messages (session_id, seq, role, content) VALUES (?, ?, ?, ?)",
            [(session.id, index, message.role, message.content) for index, message in enumerate(session.messages)],
        )


def delete_session(db_path: str, session_id: str) -> None:
    """删除会话，级联删除其消息。"""
    with connect(db_path) as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def load_sessions(db_path: str) -> list[dict[str, Any]]:
    """加载全部会话（含消息），返回可直接用于重建 Session 的字典列表。"""
    with connect(db_path) as conn:
        session_rows = conn.execute("SELECT * FROM sessions").fetchall()
        message_rows = conn.execute(
            "SELECT session_id, role, content FROM messages ORDER BY session_id, seq"
        ).fetchall()

    messages_by_session: dict[str, list[tuple[str, str]]] = {}
    for row in message_rows:
        messages_by_session.setdefault(row["session_id"], []).append((row["role"], row["content"]))

    result: list[dict[str, Any]] = []
    for row in session_rows:
        item = dict(row)
        item["messages"] = messages_by_session.get(row["id"], [])
        result.append(item)
    return result


def build_story_memory(row: dict[str, Any]) -> StoryMemory | None:
    if row.get("story_scene") is None:
        return None
    try:
        actions = json.loads(row.get("story_actions") or "[]")
    except json.JSONDecodeError:
        actions = []
    return StoryMemory(
        scene=row["story_scene"],
        current_beat=row.get("story_current_beat") or "开场",
        key_player_actions=actions if isinstance(actions, list) else [],
        last_outcome=row.get("story_outcome") or "",
    )


def build_chat_message(role: str, content: str) -> ChatMessage:
    return ChatMessage(role=role, content=content)


def parse_mode(value: str) -> ChatMode:
    return ChatMode(value)
