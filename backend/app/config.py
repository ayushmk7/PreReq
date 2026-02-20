"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Load settings from .env file or environment variables."""

    DATABASE_URL: str
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TIMEOUT_SECONDS: int = 30
    OPENAI_MAX_RETRIES: int = 2

    # Instructor auth credentials (MVP: basic auth)
    INSTRUCTOR_USERNAME: str = "admin"
    INSTRUCTOR_PASSWORD: str = "admin"

    # Student token expiry in days
    STUDENT_TOKEN_EXPIRY_DAYS: int = 30

    # Export settings
    EXPORT_DIR: str = "/tmp/conceptlens_exports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
