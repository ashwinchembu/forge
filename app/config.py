from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "forge"
    hevy_api_key: str = ""
    oura_access_token: str = ""
    webhook_secret: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    preview_mode: bool = False
    cors_origins: str = "*"
    program_start: str = "2026-05-19"
    sync_interval_minutes: int = 15
    briefing_hours: str = "7,13,19"  # 7am, 1pm, 7pm local time

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # OpenAI (GPT-4o vision for food photos)
    openai_api_key: str = ""


    class Config:
        env_file = ".env"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_settings():
    return Settings()
