import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "AI Worker Marketplace"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False") == "True"

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/worker_marketplace"
    )

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_v1_prefix: str = "/api/v1"

    # AI/ML Settings
    matching_min_score: float = 0.65  # Minimum match score threshold
    approval_auto_threshold: float = 80.0  # Auto-approve if score >= 80
    approval_review_threshold: float = 50.0  # Manual review if score 50-80
    embedding_model: str = "all-MiniLM-L6-v2"  # Lightweight but effective

    # Geographic
    default_search_radius: float = 25.0  # miles

    # Pagination
    page_size_default: int = 50
    page_size_max: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
