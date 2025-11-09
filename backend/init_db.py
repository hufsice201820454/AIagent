import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import os
from database import Base
from models import OEMCompany, NewsFeed, OEMFactory, BatteryFactory, HVACFactory
from config import settings

# Database connection - PostgreSQL
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CSV 파일 경로 설정
DB_DIR = settings.DB_DIR

def generate_uuid():
    return str(uuid.uuid4())

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.drop_all(bind=engine)  # 이 줄 추가!
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

def seed_data():
    """Seed initial data"""
    db = SessionLocal()
    
    try:
        print("\nSeeding data...")
        
        # Seed OEM companies
        companies_data = [
            {
                "oem_id": "0456e3bc-0f4d-5da2-974b-322c9d04547e",
                "company_name": "BYD",
                "ticker": "BYDDY",
                "country": "China",
                "headquarters": "Shenzhen",
                "website": "https://www.byd.com"
            },
            {
                "oem_id": "1bf96eea-be32-5a47-9bf1-12ad53af5097",
                "company_name": "XPeng",
                "ticker": "XPEV",
                "country": "China",
                "headquarters": "Guangzhou",
                "website": "https://www.xiaopeng.com"
            },
            {
                "oem_id": "606071ee-23a7-5e9b-b980-61970440c66a",
                "company_name": "Li Auto",
                "ticker": "LI",
                "country": "China",
                "headquarters": "Beijing",
                "website": "https://www.lixiang.com"
            },
            {
                "oem_id": "7fdbbb3d-f616-5759-8780-7f89dfd2faca",
                "company_name": "General Motors",
                "ticker": "GM",
                "country": "USA",
                "headquarters": "Detroit",
                "website": "https://www.gm.com"
            },
            {
                "oem_id": "aee706c2-6955-54ae-a43a-09750d52cad9",
                "company_name": "Ford",
                "ticker": "F",
                "country": "USA",
                "headquarters": "Dearborn",
                "website": "https://www.ford.com"
            },
            {
                "oem_id": "b28dad9d-eb6e-5667-a75e-f2aafb970a87",
                "company_name": "BMW",
                "ticker": "BMW",
                "country": "Germany",
                "headquarters": "Munich",
                "website": "https://www.bmw.com"
            },
            {
                "oem_id": "c2d742c9-adeb-56c3-a327-1f3637ef0961",
                "company_name": "Tesla",
                "ticker": "TSLA",
                "country": "USA",
                "headquarters": "Austin",
                "website": "https://www.tesla.com"
            },
            {
                "oem_id": "f30bb3ea-854e-5dd1-8286-3e99953f5640",
                "company_name": "Rivian",
                "ticker": "RIVN",
                "country": "USA",
                "headquarters": "Irvine",
                "website": "https://www.rivian.com"
            },
            {
                "oem_id": "f4067158-f67c-53bc-b0e4-235748b4640c",
                "company_name": "Volkswagen",
                "ticker": "VWAGY",
                "country": "Germany",
                "headquarters": "Wolfsburg",
                "website": "https://www.volkswagen.com"
            }
        ]
        
        for company_data in companies_data:
            if not db.query(OEMCompany).filter(OEMCompany.oem_id == company_data["oem_id"]).first():
                company = OEMCompany(**company_data)
                db.add(company)
        
        db.commit()
        print("✓ OEM companies seeded")
        
        # Seed news feed from CSV
        try:
            news_csv_path = os.path.join(DB_DIR, 'news_feed_seed.csv')
            news_df = pd.read_csv(news_csv_path)
            
            for _, row in news_df.iterrows():
                if not db.query(NewsFeed).filter(NewsFeed.news_id == row['news_id']).first():
                    news = NewsFeed(
                        news_id=row['news_id'],
                        oem_id=row['oem_id'],
                        title=row['title'],
                        source_url=row['source_url'],
                        source_name=row['source_name'],
                        published_at=pd.to_datetime(row['published_at'])
                    )
                    db.add(news)
            
            db.commit()
            print("✓ News feed seeded")
        except Exception as e:
            print(f"⚠ News feed seeding skipped: {e}")
        
        # Seed factories from CSV files
        try:
            # OEM factories
            oem_factories_path = os.path.join(DB_DIR, 'oem_factories.csv')
            oem_factories_df = pd.read_csv(oem_factories_path)
            for _, row in oem_factories_df.iterrows():
                if not db.query(OEMFactory).filter(OEMFactory.factory_id == row['factory_id']).first():
                    factory = OEMFactory(
                        factory_id=row['factory_id'],
                        oem_id=row['oem_id'],
                        plant_name=row['plant_name'],
                        city=row.get('city'),
                        state_province=row.get('state_province'),
                        country=row['country'],
                        latitude=row['latitude'],
                        longitude=row['longitude']
                    )
                    db.add(factory)
            db.commit()
            print("✓ OEM factories seeded")
        except Exception as e:
            print(f"⚠ OEM factories seeding skipped: {e}")
        
        try:
            # Battery factories
            battery_factories_path = os.path.join(DB_DIR, 'battery_factories.csv')
            battery_factories_df = pd.read_csv(battery_factories_path)
            for _, row in battery_factories_df.iterrows():
                if not db.query(BatteryFactory).filter(BatteryFactory.factory_id == row['factory_id']).first():
                    factory = BatteryFactory(
                        factory_id=row['factory_id'],
                        battery_id=row['battery_id'],
                        plant_name=row['plant_name'],
                        city=row.get('city'),
                        state_province=row.get('state_province'),
                        country=row['country'],
                        latitude=row['latitude'],
                        longitude=row['longitude']
                    )
                    db.add(factory)
            db.commit()
            print("✓ Battery factories seeded")
        except Exception as e:
            print(f"⚠ Battery factories seeding skipped: {e}")
        
        try:
            # HVAC factories
            hvac_factories_path = os.path.join(DB_DIR, 'hvac_factories.csv')
            hvac_factories_df = pd.read_csv(hvac_factories_path)
            for _, row in hvac_factories_df.iterrows():
                if not db.query(HVACFactory).filter(HVACFactory.factory_id == row['factory_id']).first():
                    factory = HVACFactory(
                        factory_id=row['factory_id'],
                        hvac_id=row['hvac_id'],
                        plant_name=row['plant_name'],
                        city=row.get('city'),
                        state_province=row.get('state_province'),
                        country=row['country'],
                        latitude=row['latitude'],
                        longitude=row['longitude']
                    )
                    db.add(factory)
            db.commit()
            print("✓ HVAC factories seeded")
        except Exception as e:
            print(f"⚠ HVAC factories seeding skipped: {e}")
        
        print("\n✅ Database seeding completed!")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Database Initialization ===\n")
    init_database()
    seed_data()
    print("\n=== Done ===")
