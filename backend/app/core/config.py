from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sellora"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "sellora-development-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    AUTH_PROVIDER: str = "dev_mock"  # "dev_mock", "supabase", or "clerk"
    
    # Supabase (optional if configured)
    SUPABASE_URL: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./sellora_dev.db"

    # AI Configuration (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Amazon Selling Partner API (SP-API) - India (A21TJRUUN4KGV / EU endpoint)
    SP_API_CLIENT_ID: str = ""
    SP_API_CLIENT_SECRET: str = ""
    SP_API_REFRESH_TOKEN: str = ""
    SP_API_SELLER_ID: str = ""
    SP_API_MARKETPLACE_ID: str = "A21TJRUUN4KGV"
    SP_API_ENDPOINT: str = "https://sellingpartnerapi-eu.amazon.com"
    SP_API_ENV: str = "production"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            import json
            if isinstance(v, str):
                return json.loads(v)
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
