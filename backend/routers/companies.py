from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import OEMCompany as OEMCompanyModel, UserFavorite, OEMFinancialData, OurCompanyFinancials
from sqlalchemy import desc
from schemas import OEMCompany, OEMCompanyCreate, User
from routers.auth import get_current_user

router = APIRouter()

@router.get("/oem", response_model=List[OEMCompany])
def get_oem_companies(
    skip: int = 0,
    limit: int = 100,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(OEMCompanyModel)
    if country:
        query = query.filter(OEMCompanyModel.country == country)
    companies = query.offset(skip).limit(limit).all()
    return companies

@router.get("/oem/{oem_id}", response_model=OEMCompany)
def get_oem_company(oem_id: str, db: Session = Depends(get_db)):
    company = db.query(OEMCompanyModel).filter(OEMCompanyModel.oem_id == oem_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.post("/oem", response_model=OEMCompany)
def create_oem_company(
    company: OEMCompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_company = OEMCompanyModel(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.post("/oem/{oem_id}/favorite")
def toggle_favorite(
    oem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if company exists
    company = db.query(OEMCompanyModel).filter(OEMCompanyModel.oem_id == oem_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if favorite exists
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.user_id,
        UserFavorite.oem_id == oem_id
    ).first()
    
    if favorite:
        # Remove favorite
        db.delete(favorite)
        db.commit()
        return {"message": "Removed from favorites", "is_favorite": False}
    else:
        # Add favorite
        new_favorite = UserFavorite(user_id=current_user.user_id, oem_id=oem_id)
        db.add(new_favorite)
        db.commit()
        return {"message": "Added to favorites", "is_favorite": True}

@router.get("/favorites", response_model=List[OEMCompany])
def get_user_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    favorites = db.query(OEMCompanyModel).join(UserFavorite).filter(
        UserFavorite.user_id == current_user.user_id
    ).all()
    return favorites


@router.get("/financials/summary")
def get_financial_summary(db: Session = Depends(get_db)):
    """Return compact financial snapshot for dashboard.

    - our_company: latest revenue/profit if available
    - oem_revenue_change: list of {name, pct}
    - profit_margin: list of {name, margin}
    """
    # Our company (pick latest created_at)
    our_company = None
    oc = db.query(OurCompanyFinancials).order_by(desc(OurCompanyFinancials.created_at)).first()
    if oc:
        our_company = {
            "company_name": oc.company_name,
            "revenue": float(oc.revenue) if oc.revenue is not None else None,
            "revenue_change_pct": float(oc.revenue_change_pct) if oc.revenue_change_pct is not None else None,
            "profit_margin": float(oc.profit_margin) if oc.profit_margin is not None else None,
            "period": oc.period,
        }

    # OEM financials: join to names, take latest per OEM by period (string desc)
    rows = (
        db.query(OEMFinancialData, OEMCompanyModel.company_name)
        .join(OEMCompanyModel, OEMCompanyModel.oem_id == OEMFinancialData.oem_id)
        .order_by(OEMCompanyModel.company_name.asc(), desc(OEMFinancialData.period))
        .all()
    )
    latest_by_oem = {}
    for rec, name in rows:
        if rec.oem_id in latest_by_oem:
            continue
        latest_by_oem[rec.oem_id] = {
            "company_name": name,
            "revenue": float(rec.revenue) if rec.revenue is not None else None,
            "revenue_change_pct": float(rec.revenue_change_pct) if rec.revenue_change_pct is not None else None,
            "profit_margin": float(rec.profit_margin) if rec.profit_margin is not None else None,
            "period": rec.period,
        }

    oem_revenue_change = [
        {"company_name": v["company_name"], "revenue_change_pct": v["revenue_change_pct"]}
        for v in latest_by_oem.values()
        if v["revenue_change_pct"] is not None
    ]

    profit_margins = [
        {"company_name": v["company_name"], "profit_margin": v["profit_margin"]}
        for v in latest_by_oem.values()
        if v["profit_margin"] is not None
    ]

    # Optionally top-N sorting
    oem_revenue_change.sort(key=lambda x: x["revenue_change_pct"], reverse=True)
    profit_margins.sort(key=lambda x: x["profit_margin"], reverse=True)

    return {
        "our_company": our_company,
        "oem_revenue_change": oem_revenue_change[:10],
        "profit_margins": profit_margins[:10],
    }
