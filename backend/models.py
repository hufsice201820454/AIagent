from sqlalchemy import Column, String, DateTime, Text, Numeric, Date, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    birth_date = Column(Date)
    role = Column(String(20), default='viewer')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    favorites = relationship("UserFavorite", back_populates="user")

class OEMCompany(Base):
    __tablename__ = "oem_companies"
    
    oem_id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False)
    ticker = Column(String(20), index=True)
    country = Column(String(100), index=True)
    headquarters = Column(String(200))
    website = Column(String(255))
    industry_segment = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    financial_data = relationship("OEMFinancialData", back_populates="oem_company")
    reports = relationship("AIReport", back_populates="oem_company")
    news = relationship("NewsFeed", back_populates="oem_company")
    factories = relationship("OEMFactory", back_populates="oem_company")
    favorites = relationship("UserFavorite", back_populates="oem_company")

class BatteryCompany(Base):
    __tablename__ = "battery_companies"
    
    battery_id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False)
    ticker = Column(String(20), index=True)
    country = Column(String(100), index=True)
    headquarters = Column(String(200))
    website = Column(String(255))
    industry_segment = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    factories = relationship("BatteryFactory", back_populates="battery_company")

class HVACCompany(Base):
    __tablename__ = "hvac_companies"
    
    hvac_id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False)
    ticker = Column(String(20), index=True)
    country = Column(String(100), index=True)
    headquarters = Column(String(200))
    website = Column(String(255))
    industry_segment = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    factories = relationship("HVACFactory", back_populates="hvac_company")

class OEMFinancialData(Base):
    __tablename__ = "oem_financial_data"
    
    financial_id = Column(String(36), primary_key=True, default=generate_uuid)
    oem_id = Column(String(36), ForeignKey('oem_companies.oem_id'), nullable=False, index=True)
    revenue = Column(Numeric(15, 2))
    revenue_change_pct = Column(Numeric(5, 2))
    profit_margin = Column(Numeric(5, 2))
    period = Column(String(20), index=True)
    created_at = Column(DateTime, default=func.now())
    
    oem_company = relationship("OEMCompany", back_populates="financial_data")

class AIReport(Base):
    __tablename__ = "ai_reports"
    
    report_id = Column(String(36), primary_key=True, default=generate_uuid)
    report_code = Column(String(50), unique=True, nullable=False)
    oem_id = Column(String(36), ForeignKey('oem_companies.oem_id'), index=True)
    title = Column(String(255), nullable=False)
    html_path = Column(String(500), nullable=False)
    # Store full HTML content for DB-served viewing
    html_content = Column(Text)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    oem_company = relationship("OEMCompany", back_populates="reports")

class NewsFeed(Base):
    __tablename__ = "news_feed"
    
    news_id = Column(String(36), primary_key=True, default=generate_uuid)
    oem_id = Column(String(36), ForeignKey('oem_companies.oem_id'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    content = Column(Text)
    source_url = Column(String(1000))
    source_name = Column(String(100))
    thumbnail_url = Column(String(500))
    category = Column(String(50), index=True)
    sentiment = Column(String(20))
    published_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    oem_company = relationship("OEMCompany", back_populates="news")

class OEMFactory(Base):
    __tablename__ = "oem_factories"
    
    factory_id = Column(String(36), primary_key=True, default=generate_uuid)
    oem_id = Column(String(36), ForeignKey('oem_companies.oem_id'), nullable=False, index=True)
    plant_name = Column(String(300), nullable=False)
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False, index=True)
    longitude = Column(Numeric(11, 8), nullable=False, index=True)
    notes = Column(Text)
    
    oem_company = relationship("OEMCompany", back_populates="factories")
    
    __table_args__ = (
        Index('idx_oem_country_city', 'oem_id', 'country', 'city'),
        Index('idx_oem_lat_lng', 'latitude', 'longitude'),
    )

class BatteryFactory(Base):
    __tablename__ = "battery_factories"
    
    factory_id = Column(String(36), primary_key=True, default=generate_uuid)
    battery_id = Column(String(36), ForeignKey('battery_companies.battery_id'), nullable=False, index=True)
    plant_name = Column(String(300), nullable=False)
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False, index=True)
    longitude = Column(Numeric(11, 8), nullable=False, index=True)
    notes = Column(Text)
    
    battery_company = relationship("BatteryCompany", back_populates="factories")
    
    __table_args__ = (
        Index('idx_battery_country_city', 'battery_id', 'country', 'city'),
        Index('idx_battery_lat_lng', 'latitude', 'longitude'),
    )

class HVACFactory(Base):
    __tablename__ = "hvac_factories"
    
    factory_id = Column(String(36), primary_key=True, default=generate_uuid)
    hvac_id = Column(String(36), ForeignKey('hvac_companies.hvac_id'), nullable=False, index=True)
    plant_name = Column(String(300), nullable=False)
    city = Column(String(100))
    state_province = Column(String(100))
    country = Column(String(100), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False, index=True)
    longitude = Column(Numeric(11, 8), nullable=False, index=True)
    notes = Column(Text)
    
    hvac_company = relationship("HVACCompany", back_populates="factories")
    
    __table_args__ = (
        Index('idx_hvac_country_city', 'hvac_id', 'country', 'city'),
        Index('idx_hvac_lat_lng', 'latitude', 'longitude'),
    )

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    favorite_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.user_id'), nullable=False, index=True)
    oem_id = Column(String(36), ForeignKey('oem_companies.oem_id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", back_populates="favorites")
    oem_company = relationship("OEMCompany", back_populates="favorites")
    
    __table_args__ = (
        Index('idx_user_oem', 'user_id', 'oem_id', unique=True),
    )

class OurCompanyFinancials(Base):
    __tablename__ = "our_company_financials"
    
    financial_id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False)
    revenue = Column(Numeric(15, 2))
    revenue_change_pct = Column(Numeric(5, 2))
    profit_margin = Column(Numeric(5, 2))
    period = Column(String(20), index=True)
    created_at = Column(DateTime, default=func.now())
