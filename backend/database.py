from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

# PostgreSQL 연결
DATABASE_URL = settings.DATABASE_URL

# CSV 파일 디렉토리 생성
os.makedirs(settings.DB_DIR, exist_ok=True)

# PostgreSQL 엔진 생성
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
