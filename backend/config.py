from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# .env 파일 강제 로드
load_dotenv()

class Settings(BaseSettings):
    # PostgreSQL Database Configuration
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "secret")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    
    # CSV 파일 경로
    BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))
    DB_DIR: str = os.getenv("DB_DIR", os.path.join(os.path.dirname(BASE_DIR), "db"))
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL 연결 URL"""
        # 수정 전: postgresql+psycopg2
        # 수정 후: postgresql+psycopg
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Anthropic API
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Feature flags
    SEED_FINANCIALS: bool = os.getenv("SEED_FINANCIALS", "true").lower() in ("1","true","yes")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
