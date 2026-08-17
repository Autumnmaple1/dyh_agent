import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config import Settings
from app.llm import LLMError, LLMProvider
from app.prompt_builder import build_system_prompt
from app.schemas import Character, ChatMessage, ChatMode, ClientContext

if TYPE_CHECKING:
    from app.sessions import Session


_HAN_PATTERN = re.compile(r"[\u3400-\u9fff]")


def estimate_tokens(text: str) -> int:
    """无需绑定具体 tokenizer 的保守估算：汉字约一字一 token，其余约四字符一 token。"""
    if not text:
        return 0
    han_count = len(_HAN_PATTERN.findall(text))
    other_count = len(text) - han_count
    return han_count + math.ceil(other_count / 4)


def estimate_messages(messages: list[ChatMessage]) -> int:
    return sum(estimate_tokens(item.content) + 4 for item in messages)


@dataclass
class PreparedMemory:
    history: list[ChatMessage]
    estimated_tokens: int
    compacted: bool


class MemoryManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def prepare(
        self,
        session: "Session",
        provider: LLMProvider,
        character: Character,
        mode: ChatMode,
        context: ClientContext,
        user_message: str,
    ) -> PreparedMemory:
        system_tokens = estimate_tokens(build_system_prompt(character, mode, context))
        fixed_tokens = system_tokens + estimate_tokens(user_message) + 256
        active = session.messages[session.context_start_index :]
        summary_tokens = estimate_tokens(session.summary)
        available = max(512, self.settings.context_token_budget - fixed_tokens - summary_tokens)
        compacted = False

        if (
            estimate_messages(active) > available
            and len(active) > self.settings.min_recent_messages
        ):
            compact_count = len(active) - self.settings.min_recent_messages
            older = active[:compact_count]
            try:
                session.summary = await provider.summarize(
                    existing_summary=session.summary,
                    messages=older,
                    character=character,
                    mode=mode,
                    max_chars=self.settings.summary_max_chars,
                )
            except LLMError:
                # 摘要失败不阻断本轮对话：保留原文，后续仍按 token 预算裁剪近期消息。
                compacted = False
            else:
                session.context_start_index += compact_count
                session.compacted_message_count += compact_count
                active = session.messages[session.context_start_index :]
                compacted = True

        # 摘要之后仍可能超预算；从最新消息向前装填，并保证至少保留配置的近期消息。
        available = max(
            512,
            self.settings.context_token_budget
            - fixed_tokens
            - estimate_tokens(session.summary),
        )
        selected_reversed: list[ChatMessage] = []
        used = 0
        for message in reversed(active):
            cost = estimate_tokens(message.content) + 4
            if (
                used + cost > available
                and len(selected_reversed) >= self.settings.min_recent_messages
            ):
                break
            selected_reversed.append(message)
            used += cost

        selected = list(reversed(selected_reversed))
        session.estimated_active_tokens = fixed_tokens + estimate_tokens(session.summary) + used
        return PreparedMemory(
            history=selected,
            estimated_tokens=session.estimated_active_tokens,
            compacted=compacted,
        )
