from functools import lru_cache
from typing import Annotated, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./signaling.db"
    access_token_expire_minutes: int = 1440
    cors_origins: Annotated[List[str], NoDecode] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    port: int = 8000
    upload_dir: str = "uploads/avatars"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
