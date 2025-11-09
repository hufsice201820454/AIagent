from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from database import get_db
from models import NewsFeed as NewsFeedModel
from schemas import NewsFeed, NewsFeedCreate

router = APIRouter()

@router.get("/", response_model=List[NewsFeed])
def get_news(
    skip: int = 0,
    limit: int = 50,
    oem_id: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(NewsFeedModel)
    
    if oem_id:
        query = query.filter(NewsFeedModel.oem_id == oem_id)
    if category:
        query = query.filter(NewsFeedModel.category == category)
    
    news = query.order_by(desc(NewsFeedModel.published_at)).offset(skip).limit(limit).all()
    return news

@router.get("/{news_id}", response_model=NewsFeed)
def get_news_item(news_id: str, db: Session = Depends(get_db)):
    news = db.query(NewsFeedModel).filter(NewsFeedModel.news_id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.post("/", response_model=NewsFeed)
def create_news(news: NewsFeedCreate, db: Session = Depends(get_db)):
    db_news = NewsFeedModel(**news.dict())
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

@router.get("/company/{oem_id}/latest", response_model=List[NewsFeed])
def get_latest_company_news(
    oem_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    news = db.query(NewsFeedModel).filter(
        NewsFeedModel.oem_id == oem_id
    ).order_by(desc(NewsFeedModel.published_at)).limit(limit).all()
    return news
