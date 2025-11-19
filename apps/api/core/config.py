from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Cross-LLM Research Synthesis API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = 4

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/llm_synthesis"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 50

    # Gemini
    GEMINI_API_KEY: str = "your_gemini_key_here"
    GEMINI_MODEL: str = "models/gemini-2.5-flash-preview-09-2025"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT: int = 60

    # Authentication
    CLERK_SECRET_KEY: str = "your_clerk_secret_here"
    CLERK_PUBLISHABLE_KEY: str = "your_clerk_public_here"

    # Storage
    UPLOAD_DIR: str = "/mnt/uploads"
    EXPORT_DIR: str = "/mnt/exports"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB

    # Queue
    QUEUE_NAME: str = "llm_synthesis"
    QUEUE_CONCURRENCY: int = 5

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "https://*.railway.app"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
