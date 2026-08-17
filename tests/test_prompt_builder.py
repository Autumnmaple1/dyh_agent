from app.characters import get_character
from app.prompt_builder import build_system_prompt
from app.schemas import ChatMode, ClientContext


def test_prompt_contains_only_selected_character() -> None:
    character = get_character("su-shi-xuzhou")
    assert character is not None

    prompt = build_system_prompt(character, ChatMode.TOURISM, ClientContext())

    assert "苏轼" in prompt
    assert "黄楼" in prompt
    assert "陈瑄" not in prompt
    assert "张伯行" not in prompt


def test_story_prompt_contains_scene_and_boundaries() -> None:
    character = get_character("chen-xuan-huaian")
    assert character is not None

    prompt = build_system_prompt(character, ChatMode.STORY, ClientContext())

    assert "沉浸式故事模式" in prompt
    assert "软土与渗水" in prompt
    assert "历史边界" in prompt

