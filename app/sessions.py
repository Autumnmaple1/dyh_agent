import asyncio
import json
from dataclasses import dataclass, field
from uuid import uuid4

from app import db
from app.config import get_settings
from app.schemas import ChatMessage, ChatMode, SessionView, StoryMemory


@dataclass
class Session:
    id: str
    character_id: str
    mode: ChatMode
    owner_id: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    turn: int = 0
    summary: str = ""
    context_start_index: int = 0
    compacted_message_count: int = 0
    estimated_active_tokens: int = 0
    suggestions: list[str] = field(default_factory=list)
    story_memory: StoryMemory | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._write_lock = asyncio.Lock()
        self._loaded = False

    # ---- 持久化 ----

    def _ensure_loaded(self) -> None:
        """首次访问时从 SQLite 全量加载会话到内存，之后以内存为准。"""
        if self._loaded:
            return
        settings = get_settings()
        db.init_db(settings.db_path)
        for row in db.load_sessions(settings.db_path):
            story = db.build_story_memory(row)
            session = Session(
                id=row["id"],
                owner_id=row["owner_id"],
                character_id=row["character_id"],
                mode=db.parse_mode(row["mode"]),
                turn=row["turn"],
                summary=row["summary"],
                context_start_index=row["context_start_index"],
                compacted_message_count=row["compacted_message_count"],
                estimated_active_tokens=row["estimated_active_tokens"],
                suggestions=_parse_suggestions(row.get("suggestions")),
                story_memory=story,
                messages=[db.build_chat_message(role, content) for role, content in row["messages"]],
            )
            self._sessions[session.id] = session
        self._loaded = True

    async def persist(self, session: Session) -> None:
        """将单个会话写穿到 SQLite（串行化写，避免并发写冲突）。"""
        async with self._write_lock:
            await asyncio.to_thread(db.save_session, get_settings().db_path, session)

    def reset(self) -> None:
        """清空内存缓存并强制下次重新从磁盘加载（主要供测试使用）。"""
        self._sessions.clear()
        self._loaded = False

    # ---- 会话操作 ----

    def get_or_create(
        self,
        owner_id: str,
        session_id: str | None,
        character_id: str,
        mode: ChatMode,
    ) -> Session:
        self._ensure_loaded()
        if session_id:
            session = self._sessions.get(session_id)
            if session is None or session.owner_id != owner_id:
                raise LookupError("会话不存在或无访问权限，请新建会话。")
            if session.character_id != character_id or session.mode != mode:
                raise ValueError("一个会话中不能切换角色或模式，请创建新会话。")
            return session

        new_id = str(uuid4())
        session = Session(
            id=new_id,
            owner_id=owner_id,
            character_id=character_id,
            mode=mode,
        )
        self._sessions[new_id] = session
        return session

    def get(self, owner_id: str, session_id: str) -> Session | None:
        self._ensure_loaded()
        session = self._sessions.get(session_id)
        return session if session and session.owner_id == owner_id else None

    async def clear(self, owner_id: str, session_id: str) -> bool:
        session = self.get(owner_id, session_id)
        if session is None:
            return False
        self._sessions.pop(session_id, None)
        await asyncio.to_thread(db.delete_session, get_settings().db_path, session_id)
        return True

    @staticmethod
    def view(session: Session) -> SessionView:
        return SessionView(
            session_id=session.id,
            character_id=session.character_id,
            mode=session.mode,
            turn=session.turn,
            summary=session.summary,
            compacted_message_count=session.compacted_message_count,
            estimated_active_tokens=session.estimated_active_tokens,
            story_memory=session.story_memory,
            messages=session.messages,
            suggestions=session.suggestions,
        )


def _parse_suggestions(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


session_store = SessionStore()
