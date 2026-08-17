import pytest

from app.characters import get_character
from app.config import Settings
from app.llm import DemoProvider
from app.memory import MemoryManager, estimate_tokens
from app.schemas import ChatMessage, ChatMode, ClientContext
from app.sessions import Session


def test_chinese_token_estimation_is_conservative() -> None:
    assert estimate_tokens("大运河人物智能体") >= 8
    assert estimate_tokens("hello world") >= 3


@pytest.mark.asyncio
async def test_old_messages_are_compacted_but_full_history_is_retained() -> None:
    character = get_character("su-shi-xuzhou")
    assert character is not None
    session = Session(
        id="memory-test",
        character_id=character.id,
        mode=ChatMode.TOURISM,
        messages=[
            ChatMessage(
                role="user" if index % 2 == 0 else "assistant",
                content=f"第{index}条关于徐州运河、诗词和游览偏好的较长对话内容。" * 8,
            )
            for index in range(16)
        ],
    )
    original_history = list(session.messages)
    settings = Settings(
        ai_provider="demo",
        context_token_budget=2200,
        min_recent_messages=4,
        summary_max_chars=500,
    )

    prepared = await MemoryManager(settings).prepare(
        session=session,
        provider=DemoProvider(),
        character=character,
        mode=ChatMode.TOURISM,
        context=ClientContext(),
        user_message="请继续安排路线。",
    )

    assert prepared.compacted is True
    assert session.summary
    assert session.compacted_message_count > 0
    assert session.context_start_index > 0
    assert session.messages == original_history
    assert len(prepared.history) >= settings.min_recent_messages

