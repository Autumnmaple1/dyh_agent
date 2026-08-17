from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "大运河人物智能体"
    ai_provider: str = "demo"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4.1-mini"
    ai_timeout_seconds: float = 60
    context_token_budget: int = 8000
    min_recent_messages: int = 6
    summary_max_chars: int = 1800
    db_path: str = "data/canal.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
