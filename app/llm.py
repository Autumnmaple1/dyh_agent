import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.schemas import Character, ChatMessage, ChatMode


class LLMError(RuntimeError):
    pass


@dataclass
class Completion:
    """一次模型回复：正文 + 基于当前对话动态生成的建议问题。"""

    answer: str
    suggestions: list[str]


# 兜底建议：仅当模型未按约定返回 JSON 或返回空列表时使用。
_DEFAULT_SUGGESTIONS: dict[ChatMode, list[str]] = {
    ChatMode.TOURISM: ["为我安排半日路线", "这里与大运河有什么关系？", "讲讲你当时的心境"],
    ChatMode.STORY: ["检查险情", "询问现场的人", "提出另一种办法"],
}

_COMPLETION_INSTRUCTION = (
    "\n\n请以严格 JSON 对象输出，不要输出任何其它内容、不要使用代码块、不要换行。格式如下：\n"
    '{"answer": "你对用户的最新回复", "suggestions": ["用户可能的下一条消息1", "用户可能的下一条消息2", "用户可能的下一条消息3"]}\n'
    "要求：\n"
    "1. answer 与 suggestions 均基于当前对话内容，紧扣你刚刚的回复。\n"
    "2. suggestions 恰好 3 条，必须站在用户/游客的视角，是可被用户直接选中发送的下一条提问或行动，不要写成你（角色）要说的话。\n"
    "3. 不得重复用户刚问过或已经问过的内容。\n"
    "4. 整个 JSON 必须输出为一行；answer 内部需要分段时，用 \\n 表示，不要使用真实换行符。"
)

_RETRY_INSTRUCTION = (
    "\n\n你刚才的输出不是合法 JSON。请只重新输出一个 JSON 对象：\n"
    "1. 不要任何解释、不要代码块、不要 Markdown。\n"
    "2. 整个 JSON 必须是一行，字符串内不要有真实换行，需要换行时写成 \\n。\n"
    '3. 格式仍为 {"answer": "你的回复", "suggestions": ["建议1", "建议2", "建议3"]}。'
)

_FALLBACK_ANSWER = "抱歉，我这边回复生成出了点小问题，请再问一次。"


def _repair_json_string_newlines(text: str) -> str:
    """把 JSON 字符串内部的真实换行替换为 \\n，修复常见的多行输出。"""
    out: list[str] = []
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
                continue
            if ch == "\\":
                out.append(ch)
                escaped = True
                continue
            if ch == '"':
                in_string = False
                out.append(ch)
                continue
            if ch in "\r\n":
                out.append("\\n")
                continue
            out.append(ch)
            continue
        if ch == '"':
            in_string = True
        out.append(ch)
    return "".join(out)


def _extract_json(text: str) -> dict | None:
    """从模型输出中稳健提取 JSON 对象。"""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    for candidate in (cleaned, _repair_json_string_newlines(cleaned)):
        try:
            data = json.loads(candidate)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        for candidate in (match.group(0), _repair_json_string_newlines(match.group(0))):
            try:
                data = json.loads(candidate)
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                pass
    return None


def _normalize_suggestions(data: dict | None, mode: ChatMode) -> list[str]:
    raw = (data or {}).get("suggestions")
    if not isinstance(raw, list):
        return list(_DEFAULT_SUGGESTIONS[mode])
    cleaned = [str(item).strip() for item in raw if str(item).strip()][:3]
    return cleaned or list(_DEFAULT_SUGGESTIONS[mode])


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        character: Character,
        mode: ChatMode,
        turn: int,
    ) -> Completion:
        raise NotImplementedError

    @abstractmethod
    async def summarize(
        self,
        existing_summary: str,
        messages: list[ChatMessage],
        character: Character,
        mode: ChatMode,
        max_chars: int,
    ) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(
        self,
        messages: list[dict[str, str]],
        character: Character,
        mode: ChatMode,
        turn: int,
    ) -> Completion:
        prompt_messages = [*messages, {"role": "system", "content": _COMPLETION_INSTRUCTION}]
        temperature = 0.72 if mode == ChatMode.STORY else 0.55
        text = await self._request(
            messages=prompt_messages,
            temperature=temperature,
        )
        completion = self._build_completion(text, mode)
        if completion is not None:
            return completion

        # 首次解析失败时，追加一条“只输出 JSON”的纠正指令重试一次。
        retry_messages = [
            *prompt_messages,
            {"role": "system", "content": _RETRY_INSTRUCTION},
        ]
        retry_text = await self._request(
            messages=retry_messages,
            temperature=temperature,
        )
        completion = self._build_completion(retry_text, mode)
        if completion is not None:
            return completion

        # 两次都失败时，不展示原始 JSON，改用礼貌的兜底回复。
        return Completion(
            answer=_FALLBACK_ANSWER,
            suggestions=list(_DEFAULT_SUGGESTIONS[mode]),
        )

    @staticmethod
    def _build_completion(text: str, mode: ChatMode) -> Completion | None:
        data = _extract_json(text)
        if data and str(data.get("answer", "")).strip():
            return Completion(
                answer=str(data["answer"]).strip(),
                suggestions=_normalize_suggestions(data, mode),
            )
        return None

    async def summarize(
        self,
        existing_summary: str,
        messages: list[ChatMessage],
        character: Character,
        mode: ChatMode,
        max_chars: int,
    ) -> str:
        transcript = "\n".join(
            f"{'访客' if item.role == 'user' else character.name}：{item.content}"
            for item in messages
        )
        summary_messages = [
            {
                "role": "system",
                "content": (
                    "你是会话记忆压缩器。只保留已经发生的事实：游客偏好、承诺、地点、"
                    "人物关系、任务、玩家选择、结果与未解决线索。不得补充新事实，不要写抒情文。"
                    f"输出不超过{max_chars}个中文字符。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"模式：{mode.value}\n既有摘要：{existing_summary or '无'}\n"
                    f"新增对话：\n{transcript}\n请合并成新的滚动摘要。"
                ),
            },
        ]
        result = await self._request(summary_messages, temperature=0.1)
        return result[:max_chars]

    async def _request(
        self, messages: list[dict[str, str]], temperature: float
    ) -> str:
        if not self.settings.ai_api_key:
            raise LLMError("AI_API_KEY 未配置，请在 .env 中设置，或使用 AI_PROVIDER=demo。")

        url = f"{self.settings.ai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.ai_model,
            "messages": messages,
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.ai_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"模型服务调用失败：{exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("模型服务返回了无法识别的数据结构。") from exc


class DemoProvider(LLMProvider):
    """无密钥时用于验证全链路的角色化演示，不代替正式模型。"""

    async def complete(
        self,
        messages: list[dict[str, str]],
        character: Character,
        mode: ChatMode,
        turn: int,
    ) -> Completion:
        user_message = messages[-1]["content"]
        if mode == ChatMode.TOURISM:
            places = character.tourism_focus[:3]
            answer = self._tourism_reply(character, places, user_message)
            suggestions = self._tourism_suggestions(character, places, user_message)
        else:
            answer = self._story_reply(character, user_message, turn)
            suggestions = self._story_suggestions(turn)
        return Completion(answer=answer, suggestions=suggestions)

    @staticmethod
    def _tourism_suggestions(character: Character, places: list[str], user_message: str) -> list[str]:
        return [
            f"半天时间怎么逛 {places[0]} 和 {places[1]}？",
            f"我在意{user_message[:20]}，路线还能怎么优化？",
            "这里和大运河有什么关系？",
        ]

    @staticmethod
    def _story_suggestions(turn: int) -> list[str]:
        return [
            "检查当前最危险的堤段",
            "询问附近河工的所见",
            "提出你自己的应对办法",
        ]

    async def summarize(
        self,
        existing_summary: str,
        messages: list[ChatMessage],
        character: Character,
        mode: ChatMode,
        max_chars: int,
    ) -> str:
        lines = [existing_summary] if existing_summary else []
        lines.extend(
            f"{'访客' if item.role == 'user' else character.name}：{item.content}"
            for item in messages
        )
        merged = "\n".join(line for line in lines if line).strip()
        if len(merged) <= max_chars:
            return merged
        return "…" + merged[-(max_chars - 1) :]

    @staticmethod
    def _tourism_reply(character: Character, places: list[str], user_message: str) -> str:
        openings = {
            "苏轼": "诸位既问到徐州，我便不只领你们看楼阁，也要看水与城如何彼此成全。",
            "陈瑄": "依水势而论，游淮安不可只看一处古迹，须沿着河、闸与城的关系来看。",
            "张伯行": "游苏州，当看繁华，也当看繁华如何由一河清水、一段安堤护持。",
        }
        reason = character.canal_knowledge[0]
        route = " → ".join(places)
        return (
            f"{openings[character.name]}\n\n"
            f"我建议从 **{places[0]}** 起步，再往 **{places[1]}**，若时间从容，最后到 **{places[2]}**。"
            f"这条线不在景点多少，而在能看出一条脉络：{reason}\n\n"
            f"**建议顺序**：{route}\n\n"
            f"你方才说“{user_message[:60]}”。若告诉我可游览多久、偏爱诗文还是水利，我还能把路线再收紧些。"
        )

    @staticmethod
    def _story_reply(character: Character, user_message: str, turn: int) -> str:
        scenes = {
            "苏轼": "雨声压住城头的呼喊，东南角的草袋堤忽然向外鼓起。苏轼将衣袖束紧，回身看你。",
            "陈瑄": "浑水从试掘的土层间慢慢渗出，木桩旁的细砂开始下陷。陈瑄蹲下捻了捻湿土。",
            "张伯行": "河堤外雨水连成一片，案上的物料簿却少了三十担石料。张伯行合上账册，目光转向你。",
        }
        directives = {
            "苏轼": "此刻人心不可乱。你去看渗水是清是浑，再报我草袋还余多少。",
            "陈瑄": "先辨渗水来自何层，不可急着填埋。你愿查木桩，还是随我复核闸址？",
            "张伯行": "水情与账目须同时查。护堤是急务，亏空也不可借雨遮掩。",
        }
        return (
            f"*第 {turn} 幕*\n\n{scenes[character.name]}\n\n"
            f"“{directives[character.name]}”\n\n"
            f"你刚才的行动是：**{user_message[:100]}**\n\n现场因此有了新的变化，但结果还未完全显露。\n\n"
            "你可以：\n1. 立刻检查最危险的位置\n2. 向附近河工询问异常\n3. 提出你自己的办法"
        )


def create_provider(settings: Settings) -> LLMProvider:
    if settings.ai_provider.lower() == "demo":
        return DemoProvider()
    if settings.ai_provider.lower() in {
        "openai",
        "openai_compatible",
        "deepseek",
        "qwen",
        "moonshot",
    }:
        return OpenAICompatibleProvider(settings)
    raise LLMError(f"不支持的 AI_PROVIDER：{settings.ai_provider}")
