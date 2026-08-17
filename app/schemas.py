from enum import StrEnum

from pydantic import BaseModel, Field


class ChatMode(StrEnum):
    TOURISM = "tourism"
    STORY = "story"


class SpeechProfile(BaseModel):
    voice_register: str
    rhythm: str
    preferred_expressions: list[str] = []
    rhetorical_devices: list[str] = []
    avoid_patterns: list[str] = []


class HistoricalEvent(BaseModel):
    year: int | None = None
    title: str
    description: str


class Character(BaseModel):
    id: str
    name: str
    alias: str
    city: str
    dynasty: str
    active_time: str
    role: str
    portrait_mark: str
    short_intro: str
    personality: list[str]
    speech_profile: SpeechProfile
    biography: list[HistoricalEvent]
    canal_knowledge: list[str]
    tourism_focus: list[str]
    opening_lines: dict[str, str] = Field(default_factory=dict)
    story_scene: str
    historical_boundaries: list[str]


class ClientContext(BaseModel):
    visitor_interests: list[str] = []
    duration_minutes: int | None = Field(default=None, ge=15, le=1440)
    current_location: str | None = None
    scene: str | None = None


class ChatRequest(BaseModel):
    character_id: str
    mode: ChatMode = ChatMode.TOURISM
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    context: ClientContext = Field(default_factory=ClientContext)


class ChatMessage(BaseModel):
    role: str
    content: str


class StoryMemory(BaseModel):
    scene: str
    current_beat: str = "开场"
    key_player_actions: list[str] = []
    last_outcome: str = ""


class ChatResponse(BaseModel):
    session_id: str
    character_id: str
    character_name: str
    mode: ChatMode
    answer: str
    suggestions: list[str]
    turn: int


class SessionView(BaseModel):
    session_id: str
    character_id: str
    mode: ChatMode
    turn: int
    summary: str
    compacted_message_count: int
    estimated_active_tokens: int
    story_memory: StoryMemory | None
    messages: list[ChatMessage]
    suggestions: list[str] = []
