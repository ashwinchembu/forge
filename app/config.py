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

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
