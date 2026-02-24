"""Application settings loaded from environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost:5432/aecai"

    # Auth
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # VLM
    DEFAULT_MODEL: str = "claude-haiku-4-5-20251001"
    DEFAULT_GRID_SIZE: int = 8
    DEFAULT_ZOOM: int = 8
    MAX_CONCURRENT_VLM: int = 3

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # File storage
    UPLOAD_DIR: Path = Path("./uploads")
    WORK_DIR: Path = Path("./work")
    OUTPUT_DIR: Path = Path("./outputs")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def setup_dirs(self):
        for d in [self.UPLOAD_DIR, self.WORK_DIR, self.OUTPUT_DIR]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_dirs()
