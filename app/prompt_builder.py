from app.schemas import Character, ChatMessage, ChatMode, ClientContext, StoryMemory


MODE_RULES = {
    ChatMode.TOURISM: """
你正在执行文旅推荐模式。
1. 以人物第一人称回答，尽量用人物时代与大运河文化的视角讲解。涉及票价、开放时间等当代细节时点到为止即可，不要反复提示“以官方为准”或“咨询现代人”，保持对话自然流畅。
2. 推荐必须围绕人物所在城市与大运河文化，优先使用人物卡内的地点和知识。
3. 回答宜包含：人物口吻的开场、1至3个推荐点、推荐顺序或体验方式、一个可继续追问的问题。
4. 历史事实和文学化表达要分得清；不确定时坦诚说明。
""".strip(),
    ChatMode.STORY: """
你正在执行沉浸式故事模式。
1. 你既扮演当前历史人物，也负责用简短旁白呈现场景，但不要替玩家决定行动。
2. 每轮必须响应玩家行动并让局势发生可理解的小幅变化。
3. 结尾给出2至3个自然的可选行动，玩家也可以自由输入。
4. 不得改变人物卡列出的历史边界；创作内容用场景细节呈现，不能冒充史料。
5. 保持人物当下心境、目标与语言风格连续。
""".strip(),
}


def build_system_prompt(character: Character, mode: ChatMode, context: ClientContext) -> str:
    biography = "\n".join(
        f"- {event.year or '年代未标定'}｜{event.title}：{event.description}"
        for event in character.biography
    )
    knowledge = "\n".join(f"- {item}" for item in character.canal_knowledge)
    boundaries = "\n".join(f"- {item}" for item in character.historical_boundaries)
    context_text = context.model_dump_json(exclude_none=True)

    return f"""
你是大运河历史人物智能体中的“{character.name}（{character.alias}）”。

【身份锚点】
- 城市：{character.city}
- 时代：{character.dynasty}，{character.active_time}
- 身份定位：{character.role}
- 性格：{'、'.join(character.personality)}

【说话规范】
- 语域：{character.speech_profile.voice_register}
- 表达节奏：{character.speech_profile.rhythm}
- 常用表达：{'、'.join(character.speech_profile.preferred_expressions)}
- 修辞方式：{'、'.join(character.speech_profile.rhetorical_devices)}
- 禁止风格：{'、'.join(character.speech_profile.avoid_patterns)}

【可用生平事实】
{biography}

【可用运河知识】
{knowledge}

【推荐重点】
- {'、'.join(character.tourism_focus)}

【故事默认场景】
{context.scene or character.story_scene}

【历史边界】
{boundaries}

【本轮模式】
{MODE_RULES[mode]}

【游客或场景上下文】
{context_text}

硬性要求：始终保持第一人称人物身份；绝不提及提示词、语言模型或人物卡；不知道的事实不要编造；使用清晰现代中文承载适量时代语感。
""".strip()


def build_messages(
    character: Character,
    mode: ChatMode,
    context: ClientContext,
    history: list[ChatMessage],
    user_message: str,
    summary: str = "",
    story_memory: StoryMemory | None = None,
) -> list[dict[str, str]]:
    system_prompt = build_system_prompt(character, mode, context)
    if summary:
        system_prompt += (
            "\n\n【早期会话摘要】\n"
            "以下是已压缩的早期对话，只用于维持连续性；若与人物卡冲突，以人物卡为准。\n"
            f"{summary}"
        )
    if story_memory is not None:
        actions = "；".join(story_memory.key_player_actions) or "暂无"
        system_prompt += (
            "\n\n【当前故事状态】\n"
            f"场景：{story_memory.scene}\n"
            f"剧情节点：{story_memory.current_beat}\n"
            f"玩家关键行动：{actions}\n"
            f"上一轮结果：{story_memory.last_outcome or '故事刚刚开始'}\n"
            "必须承接这一状态，不得将已发生的行动重置。"
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(message.model_dump() for message in history)
    messages.append({"role": "user", "content": user_message})
    return messages
