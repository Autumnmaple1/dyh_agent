from pathlib import Path
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.characters import get_character, list_characters
from app.config import Settings, get_settings
from app.llm import LLMError, create_provider
from app.memory import MemoryManager
from app.prompt_builder import build_messages
from app.schemas import (
    Character,
    ChatMessage,
    ChatMode,
    ChatRequest,
    ChatResponse,
    SessionView,
    StoryMemory,
)
from app.sessions import session_store


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
VISITOR_COOKIE = "canal_visitor_id"

app = FastAPI(
    title="大运河人物智能体 API",
    version="0.1.0",
    description="首版支持苏轼、陈瑄、张伯行三个角色，以及文旅推荐和故事模式。",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/health")
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "provider": settings.ai_provider}


@app.get("/api/v1/characters", response_model=list[Character])
async def characters() -> list[Character]:
    return list_characters()


@app.get("/api/v1/characters/{character_id}", response_model=Character)
async def character_detail(character_id: str) -> Character:
    character = get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return character


def get_visitor_id(request: Request, response: Response) -> str:
    """Return a browser-scoped anonymous owner id without trusting client input."""
    cookie_value = request.cookies.get(VISITOR_COOKIE)
    try:
        visitor_id = str(UUID(cookie_value)) if cookie_value else None
    except (TypeError, ValueError):
        visitor_id = None

    if visitor_id is None:
        visitor_id = str(uuid4())
        response.set_cookie(
            key=VISITOR_COOKIE,
            value=visitor_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 8,
            path="/",
        )
    return visitor_id


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    response: Response,
    visitor_id: str = Depends(get_visitor_id),
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    character = get_character(request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")

    try:
        session = session_store.get_or_create(
            visitor_id, request.session_id, request.character_id, request.mode
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    async with session.lock:
        if request.mode == ChatMode.STORY and session.story_memory is None:
            session.story_memory = StoryMemory(
                scene=request.context.scene or character.story_scene
            )

        session.turn += 1

        try:
            provider = create_provider(settings)
            prepared = await MemoryManager(settings).prepare(
                session=session,
                provider=provider,
                character=character,
                mode=request.mode,
                context=request.context,
                user_message=request.message,
            )
            messages = build_messages(
                character=character,
                mode=request.mode,
                context=request.context,
                history=prepared.history,
                user_message=request.message,
                summary=session.summary,
                story_memory=session.story_memory,
            )
            completion = await provider.complete(
                messages=messages,
                character=character,
                mode=request.mode,
                turn=session.turn,
            )
            answer = completion.answer
        except LLMError as exc:
            session.turn -= 1
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        session.messages.extend(
            [
                ChatMessage(role="user", content=request.message),
                ChatMessage(role="assistant", content=answer),
            ]
        )
        session.suggestions = completion.suggestions
        if session.story_memory is not None:
            session.story_memory.current_beat = f"第 {session.turn} 幕"
            session.story_memory.key_player_actions.append(request.message)
            session.story_memory.key_player_actions = session.story_memory.key_player_actions[-8:]
            session.story_memory.last_outcome = answer[:500]

        # 会话变更完成后写穿到 SQLite，保证服务重启后对话记录不丢失。
        await session_store.persist(session)

    return ChatResponse(
        session_id=session.id,
        character_id=character.id,
        character_name=character.name,
        mode=request.mode,
        answer=answer,
        suggestions=completion.suggestions,
        turn=session.turn,
    )


@app.get("/api/v1/sessions/{session_id}", response_model=SessionView)
async def session_detail(
    session_id: str,
    response: Response,
    visitor_id: str = Depends(get_visitor_id),
) -> SessionView:
    session = session_store.get(visitor_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session_store.view(session)


@app.delete("/api/v1/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    response: Response,
    visitor_id: str = Depends(get_visitor_id),
) -> None:
    if not await session_store.clear(visitor_id, session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
