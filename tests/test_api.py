import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app
from app.sessions import session_store

_TEST_DB = Path(tempfile.gettempdir()) / "canal_test.db"

app.dependency_overrides[get_settings] = lambda: Settings(ai_provider="demo", db_path=str(_TEST_DB))
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db() -> None:
    for path in (*_TEST_DB.parent.glob(f"{_TEST_DB.name}*"),):
        path.unlink(missing_ok=True)
    session_store.reset()
    yield
    session_store.reset()


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_three_characters() -> None:
    response = client.get("/api/v1/characters")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_demo_tourism_chat_and_session() -> None:
    response = client.post(
        "/api/v1/chat",
        json={
            "character_id": "su-shi-xuzhou",
            "mode": "tourism",
            "message": "我有半天时间，喜欢诗词。",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["character_name"] == "苏轼"
    assert "黄楼" in payload["answer"]

    session = client.get(f"/api/v1/sessions/{payload['session_id']}")
    assert session.status_code == 200
    assert session.json()["turn"] == 1
    assert len(session.json()["messages"]) == 2


def test_suggestions_are_dynamic_and_persisted() -> None:
    first = client.post(
        "/api/v1/chat",
        json={
            "character_id": "su-shi-xuzhou",
            "mode": "tourism",
            "message": "我想去看黄楼，顺便走半天。",
        },
    ).json()
    assert len(first["suggestions"]) == 3
    assert all(isinstance(item, str) and item for item in first["suggestions"])
    assert "黄楼" in first["answer"]

    # 会话视图中应能取回动态建议，供前端恢复历史时展示。
    session = client.get(f"/api/v1/sessions/{first['session_id']}").json()
    assert session["suggestions"] == first["suggestions"]

    # 不同内容应生成不同的动态建议（demo 模式会引用用户消息）。
    second = client.post(
        "/api/v1/chat",
        json={
            "character_id": "su-shi-xuzhou",
            "mode": "tourism",
            "message": "对治水比较感兴趣。",
        },
    ).json()
    assert second["suggestions"] != first["suggestions"]


def test_session_rejects_character_switch() -> None:
    first = client.post(
        "/api/v1/chat",
        json={"character_id": "chen-xuan-huaian", "mode": "story", "message": "检查渗水。"},
    ).json()
    response = client.post(
        "/api/v1/chat",
        json={
            "character_id": "zhang-boxing-suzhou",
            "mode": "story",
            "message": "继续。",
            "session_id": first["session_id"],
        },
    )
    assert response.status_code == 409

    session = client.get(f"/api/v1/sessions/{first['session_id']}").json()
    assert session["story_memory"]["current_beat"] == "第 1 幕"
    assert session["story_memory"]["key_player_actions"] == ["检查渗水。"]
    assert session["estimated_active_tokens"] > 0


def test_sessions_are_isolated_between_visitors() -> None:
    first_visitor = TestClient(app)
    second_visitor = TestClient(app)
    first = first_visitor.post(
        "/api/v1/chat",
        json={"character_id": "su-shi-xuzhou", "mode": "tourism", "message": "只属于第一位访客的记忆。"},
    )
    session_id = first.json()["session_id"]

    assert second_visitor.get(f"/api/v1/sessions/{session_id}").status_code == 404
    assert second_visitor.post(
        "/api/v1/chat",
        json={"character_id": "su-shi-xuzhou", "mode": "tourism", "message": "尝试读取别人的会话。", "session_id": session_id},
    ).status_code == 404
    assert first_visitor.get(f"/api/v1/sessions/{session_id}").status_code == 200
