from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None
    role: Optional[str] = "viewer"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    birth_date: Optional[date] = None

class User(UserBase):
    user_id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Company schemas
class OEMCompanyBase(BaseModel):
    company_name: str
    ticker: Optional[str] = None
    country: Optional[str] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    industry_segment: Optional[str] = None

class OEMCompanyCreate(OEMCompanyBase):
    pass

class OEMCompany(OEMCompanyBase):
    oem_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# News schemas
class NewsFeedBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    published_at: Optional[datetime] = None

class NewsFeedCreate(NewsFeedBase):
    oem_id: str

class NewsFeed(NewsFeedBase):
    news_id: str
    oem_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Report schemas
class AIReportBase(BaseModel):
    report_code: str
    title: str
    html_path: str

class AIReportCreate(AIReportBase):
    oem_id: Optional[str] = None

class AIReport(AIReportBase):
    report_id: str
    oem_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Factory schemas
class FactoryBase(BaseModel):
    plant_name: str
    city: Optional[str] = None
    state_province: Optional[str] = None
    country: str
    latitude: float
    longitude: float
    notes: Optional[str] = None

class OEMFactoryCreate(FactoryBase):
    oem_id: str

class OEMFactory(FactoryBase):
    factory_id: str
    oem_id: str
    
    class Config:
        from_attributes = True

# Financial schemas
class FinancialDataBase(BaseModel):
    revenue: Optional[Decimal] = None
    revenue_change_pct: Optional[Decimal] = None
    profit_margin: Optional[Decimal] = None
    period: str

class OEMFinancialCreate(FinancialDataBase):
    oem_id: str

class OEMFinancialData(FinancialDataBase):
    financial_id: str
    oem_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Agent request schemas
class AnalysisRequest(BaseModel):
    company_name: Optional[str] = None
    oem_id: Optional[str] = None
    analysis_type: str  # stock, value_chain, esg, tech_search

class ReportGenerateRequest(BaseModel):
    company_name: str
    oem_id: Optional[str] = None
    include_sections: Optional[List[str]] = None
