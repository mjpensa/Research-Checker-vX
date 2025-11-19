from pydantic_settings import BaseSettings
from typing import Optional
import os

class WorkerConfig(BaseSettings):
    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Database
    DATABASE_URL: str = "postgresql://localhost/llm_synthesis"

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "models/gemini-2.5-flash-preview-09-2025"

    # Worker settings
    WORKER_CONCURRENCY: int = 3
    WORKER_NAME: str = "default-worker"
    QUEUE_NAME: str = "llm_synthesis"

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    # Storage
    UPLOAD_DIR: str = "/mnt/uploads"
    EXPORT_DIR: str = "/mnt/exports"

    class Config:
        env_file = ".env"
        case_sensitive = True

config = WorkerConfig()
