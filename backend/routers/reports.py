from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import uuid
from pathlib import Path

from database import get_db
from models import AIReport as AIReportModel
from schemas import AIReport, AIReportCreate, AnalysisRequest, ReportGenerateRequest, User
from routers.auth import get_current_user

router = APIRouter()

# Base directory for generated HTML reports
OUTPUTS_DIR = (Path(__file__).resolve().parents[2] / 'outputs').resolve()

# Inject a <base> tag so relative asset URLs in HTML resolve to /reports/
def _inject_base(html_text: str, base_href: str) -> str:
    try:
        if not html_text:
            return html_text
        lower = html_text.lower()
        if '<base ' in lower:
            return html_text
        href = (base_href.rstrip('/') + '/').replace('\\\\', '/')
        base_tag = f"<base href=\"{href}\">"
        head_idx = lower.find('<head>')
        if head_idx != -1:
            insert_at = head_idx + len('<head>')
            return html_text[:insert_at] + base_tag + html_text[insert_at:]
        return base_tag + html_text
    except Exception:
        return html_text

# Rewrite absolute local file paths in HTML to the served /reports path
def _rewrite_local_paths(html_text: str) -> str:
    try:
        if not html_text:
            return html_text
        text = html_text
        # Common Windows path prefix from generation
        win_prefix = 'file:///C:/workspace/evagent/outputs/'
        if win_prefix in text:
            text = text.replace(win_prefix, '/reports/')
        # Generic "file:///.../outputs/" variant
        text = text.replace('file:///workspace/evagent/outputs/', '/reports/')
        text = text.replace('file:///evagent/outputs/', '/reports/')
        # Backslash absolute paths that slipped in
        text = text.replace('C:/workspace/evagent/outputs/', '/reports/')
        text = text.replace('C:\\workspace\\evagent\\outputs\\', '/reports/')
        return text
    except Exception:
        return html_text

@router.get("/", response_model=List[AIReport])
def get_reports(
    skip: int = 0,
    limit: int = 50,
    oem_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AIReportModel)
    if oem_id:
        query = query.filter(AIReportModel.oem_id == oem_id)
    
    reports = query.order_by(desc(AIReportModel.created_at)).offset(skip).limit(limit).all()
    return reports

@router.get("/{report_id}", response_model=AIReport)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(AIReportModel).filter(AIReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/code/{report_code}", response_model=AIReport)
def get_report_by_code(report_code: str, db: Session = Depends(get_db)):
    report = db.query(AIReportModel).filter(AIReportModel.report_code == report_code).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a comprehensive AI report"""
    report_code = f"RPT-{uuid.uuid4().hex[:8].upper()}"
    
    # Create report entry
    report = AIReportModel(
        report_code=report_code,
        oem_id=request.oem_id,
        title=f"Analysis Report: {request.company_name}",
        html_path=f"/reports/{report_code}.html"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Add background task to generate report
    # background_tasks.add_task(generate_report_task, report.report_id, request)
    
    return {
        "report_id": report.report_id,
        "report_code": report_code,
        "status": "generating",
        "message": "Report generation started"
    }

@router.post("/analysis")
async def run_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run specific analysis using agents"""
    # This would call the appropriate agent based on analysis_type
    return {
        "status": "completed",
        "analysis_type": request.analysis_type,
        "result": "Analysis results would be here"
    }


@router.get("/{report_id}/open", include_in_schema=False)
def open_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(AIReportModel).filter(AIReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # Redirect to static served path (mounted at /reports)
    filename = Path(report.html_path).name
    return RedirectResponse(url=f"/reports/{filename}")


@router.get("/code/{report_code}/open", include_in_schema=False)
def open_report_by_code(report_code: str, db: Session = Depends(get_db)):
    report = db.query(AIReportModel).filter(AIReportModel.report_code == report_code).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    filename = Path(report.html_path).name
    return RedirectResponse(url=f"/reports/{filename}")


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(AIReportModel).filter(AIReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    filename = Path(report.html_path).name
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        # Fallback to DB content download
        if getattr(report, 'html_content', None):
            base_href = str(Path(report.html_path).parent) or '/reports'
            html_text = _rewrite_local_paths(report.html_content)
            return HTMLResponse(content=_inject_base(html_text, base_href))
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(path=str(file_path), filename=filename, media_type="text/html")


@router.get("/{report_id}/content", response_class=HTMLResponse)
def stream_report_html(report_id: str, db: Session = Depends(get_db)):
    """Return raw HTML content from DB; fallback to file if needed."""
    report = db.query(AIReportModel).filter(AIReportModel.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if getattr(report, 'html_content', None):
        base_href = str(Path(report.html_path).parent) or '/reports'
        html_text = _rewrite_local_paths(report.html_content)
        return HTMLResponse(content=_inject_base(html_text, base_href))
    # Fallback: read from file path
    filename = Path(report.html_path).name
    file_path = OUTPUTS_DIR / filename
    if file_path.exists():
        try:
            base_href = str(Path(report.html_path).parent) or '/reports'
            html_text = file_path.read_text(encoding='utf-8', errors='ignore')
            html_text = _rewrite_local_paths(html_text)
            return HTMLResponse(content=_inject_base(html_text, base_href))
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="Report content unavailable")
