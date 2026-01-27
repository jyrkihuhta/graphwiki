"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    data_dir: Path = Path("data/pages")
    debug: bool = False
    app_title: str = "GraphWiki"

    model_config = SettingsConfigDict(
        env_prefix="GRAPHWIKI_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
