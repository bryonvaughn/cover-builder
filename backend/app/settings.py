from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parents[2]  # cover-builder/
ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    # App
    app_env: str = "development"

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Database (REQUIRED)
    database_url: str

    # OpenAI
    openai_api_key: str
    openai_text_model: str = "gpt-5.2"  # default, can override in .env

    app_env: str = "dev"
    use_real_openai: bool = False

    storage_dir: str = Field(default="storage")
    image_model: str = Field(default="gpt-image-1.5")
    image_size: str = Field(default="1024x1536")  # portrait cover-ish

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
