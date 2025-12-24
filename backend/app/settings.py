from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]  # cover-builder/
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # App
    app_env: str = "development"

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # OpenAI
    openai_api_key: str
    openai_text_model: str = "gpt-5.2"  # default, can override in .env

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
