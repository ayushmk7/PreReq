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

    # Environment and web security
    APP_ENV: str = "development"
    CORS_ALLOWED_ORIGINS: str = "*"

    # Async compute settings
    COMPUTE_ASYNC_ENABLED: bool = False
    COMPUTE_QUEUE_BACKEND: str = "file"
    COMPUTE_QUEUE_FILE: str = "/tmp/prereq_compute_queue.json"
    COMPUTE_WORKER_POLL_SECONDS: int = 3

    # OCI object storage hooks
    OCI_OBJECT_STORAGE_ENABLED: bool = False
    OCI_OBJECT_STORAGE_NAMESPACE: str = ""
    OCI_BUCKET_UPLOADS: str = ""
    OCI_BUCKET_EXPORTS: str = ""
    OCI_CONFIG_FILE: str = "~/.oci/config"
    OCI_CONFIG_PROFILE: str = "DEFAULT"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
