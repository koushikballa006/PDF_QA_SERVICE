from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDF QA Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL Database Settings
    POSTGRES_USER: str = "koushik"
    POSTGRES_PASSWORD: str = "8008"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "pdf_qa_db"

    # SQLAlchemy Database URL
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    # Storage
    UPLOAD_DIR: str = "storage/pdfs"
    EXTRACTED_TEXT_DIR: str = "storage/extracted_text"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    WS_RATE_LIMIT_PER_MINUTE: int = 30
    
    # Token Settings
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()    