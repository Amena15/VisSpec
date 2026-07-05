"""
Environment configuration management.
Loads settings from .env file with sensible defaults using Pydantic Settings.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Application
    APP_NAME: str = "VisSpec"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Override via .env for real credentials.
    # NOTE: keep defaults only for local dev; real values should come from backend/.env
    DATABASE_URL: str = "postgresql+asyncpg://vispec:vispec123@localhost:5432/vispec"

    # Security
    SECRET_KEY: str = "vispec_secret_key_for_development_purpose_only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq / LLaMA 3
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"
    GROQ_TEMPERATURE: float = 0.1
    GROQ_MAX_RETRIES: int = 3

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    # Document Limits
    MAX_FILE_SIZE_BYTES: int = 10485760  # 10MB
    MAX_PAGES: int = 50
    MAX_PROCESSING_TIME_MS: int = 180000  # 180 sec

    # Validation
    MIN_CONFIDENCE_THRESHOLD: float = 0.70

    # Report
    REPORT_WATERMARK: str = "VisSpec"

    class Config:
        # Load the backend-local .env reliably (so DATABASE_URL overrides defaults)
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance shared across the application
settings = Settings()
