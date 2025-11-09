from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
from pathlib import Path
import uuid
import os
from dotenv import load_dotenv

from routers import auth, companies, news, reports, users
from database import Base, get_db
from models import (
    AIReport as AIReportModel,
    OEMCompany as OEMCompanyModel,
    OEMFinancialData as OEMFinancialDataModel,
    OurCompanyFinancials as OurCompanyFinancialsModel,
)
from sqlalchemy import inspect, text
from config import settings

load_dotenv()

# Database setup - PostgreSQL
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Ensure ai_reports.html_content column exists (PostgreSQL-safe)
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE ai_reports ADD COLUMN IF NOT EXISTS html_content TEXT"))
except Exception as e:
    print(f"⚠ Could not ensure html_content column: {e}")

# Detect if ai_reports.html_content column exists
inspector = inspect(engine)
_ai_reports_has_html_content = False
try:
    cols = [c['name'] for c in inspector.get_columns('ai_reports')]
    _ai_reports_has_html_content = 'html_content' in cols
except Exception:
    pass

def _sync_outputs_to_ai_reports():
    """Scan evagent/outputs for html reports and upsert to ai_reports."""
    outputs_dir = (Path(__file__).resolve().parent.parent / 'outputs').resolve()
    if not outputs_dir.exists():
        return

    session = SessionLocal()
    try:
        for html_file in outputs_dir.glob('*.html'):
            html_path = f"/reports/{html_file.name}"
            # Skip if already registered
            exists = (
                session.query(AIReportModel)
                .filter(AIReportModel.html_path == html_path)
                .first()
            )
            try:
                html_text = html_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                html_text = None

            if exists:
                # Update missing content (only if column exists)
                if _ai_reports_has_html_content and not getattr(exists, 'html_content', None) and html_text:
                    exists.html_content = html_text
                continue

            # Deterministic report_code from filename for idempotency
            code = 'RPT-' + uuid.uuid5(uuid.NAMESPACE_URL, html_file.name).hex[:8].upper()
            title = html_file.stem.replace('_', ' ').replace('-', ' ')

            if _ai_reports_has_html_content:
                report = AIReportModel(
                    report_code=code,
                    title=title if title else html_file.name,
                    html_path=html_path,
                    html_content=html_text,
                )
            else:
                report = AIReportModel(
                    report_code=code,
                    title=title if title else html_file.name,
                    html_path=html_path,
                )
            session.add(report)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up EVAgent API...")
    # Ensure static reports mount is available before syncing
    try:
        _sync_outputs_to_ai_reports()
        print("✓ Synced HTML reports to ai_reports")
    except Exception as e:
        print(f"⚠ Failed syncing ai_reports: {e}")
    
    # Optional: seed minimal financials (toggle via SEED_FINANCIALS)
    if settings.SEED_FINANCIALS:
        try:
            with engine.begin() as conn:
                has_our = conn.execute(text("SELECT 1 FROM our_company_financials LIMIT 1")).first()
                if not has_our:
                    conn.execute(text(
                        """
                        INSERT INTO our_company_financials
                        (financial_id, company_name, revenue, revenue_change_pct, profit_margin, period, created_at)
                        VALUES (:id, :name, :rev, :chg, :pm, :period, NOW())
                        """
                    ), {
                        "id": str(uuid.uuid4()),
                        "name": "EVAgent",
                        "rev": 1_300_000_000.0,
                        "chg": 4.5,
                        "pm": 7.2,
                        "period": "2025-Q3",
                    })

                has_oem_fin = conn.execute(text("SELECT 1 FROM oem_financial_data LIMIT 1")).first()
                if not has_oem_fin:
                    oems = conn.execute(text("SELECT oem_id, company_name FROM oem_companies"))
                    name_to_id = {row.company_name: row.oem_id for row in oems}
                    rows = []
                    def add(name, rev, chg, pm):
                        oid = name_to_id.get(name)
                        if oid:
                            rows.append({
                                "financial_id": str(uuid.uuid4()),
                                "oem_id": oid,
                                "revenue": rev,
                                "chg": chg,
                                "pm": pm,
                                "period": "2025-Q3",
                            })
                    add("Hyundai Motor Group", 120_000_000_000.0, 12.3, 5.2)
                    add("Tesla", 25_100_000_000.0, 9.5, 11.8)
                    add("Rivian", 1_300_000_000.0, -2.5, -12.0)
                    add("BYD", 13_800_000_000.0, 7.4, 7.4)
                    add("Volkswagen", 18_200_000_000.0, 3.1, 6.1)
                    add("General Motors", 16_900_000_000.0, 2.2, 5.9)
                    add("Ford", 15_400_000_000.0, 1.8, 4.7)
                    add("Li Auto", 3_400_000_000.0, 8.2, 6.5)
                    add("XPeng", 1_900_000_000.0, 6.1, 3.9)
                    if rows:
                        conn.execute(text(
                            """
                            INSERT INTO oem_financial_data
                            (financial_id, oem_id, revenue, revenue_change_pct, profit_margin, period, created_at)
                            VALUES (:financial_id, :oem_id, :revenue, :chg, :pm, :period, NOW())
                            """
                        ), rows)
                    print("✓ Seeded financial snapshot (minimal)")
        except Exception as e:
            print(f"⚠ Financial seed skipped: {e}")
    yield
    # Shutdown
    print("👋 Shutting down EVAgent API...")

app = FastAPI(
    title="EVAgent API",
    description="자동차 시장 트렌드 분석 웹 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

# Serve generated HTML reports from outputs directory
reports_dir = (Path(__file__).resolve().parent.parent / 'outputs').resolve()
if reports_dir.exists():
    app.mount("/reports", StaticFiles(directory=str(reports_dir)), name="reports")

@app.get("/")
async def root():
    return {
        "message": "EVAgent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
