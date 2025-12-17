"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Interview Readiness Coach"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Database
    DATABASE_URL: str = "sqlite:///./irc_coach.db"
    # For PostgreSQL: "postgresql://user:password@localhost/dbname"
    
    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # openai, anthropic, ollama
    LLM_MODEL: str = "gpt-4-turbo-preview"
    
    # Ollama (if using local LLM)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # LangSmith
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "irc-coach"
    LANGSMITH_TRACING: bool = False
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"  # faiss or chroma
    VECTOR_STORE_PATH: str = "./data/vector_store"
    
    # File Storage
    UPLOAD_DIR: Path = Path("./data/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Calendar
    CALENDAR_TIMEZONE: str = "UTC"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)




