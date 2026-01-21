from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from core.deps import get_db, get_agent
from services.report_service import ReportService
from core.agent import ClinicalAgent

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("")
def get_reports():
    return ReportService.get_report_list()

@router.post("/generate")
def generate_report(
    report_type: str = "risk",
    db: Session = Depends(get_db), 
    agent: ClinicalAgent = Depends(get_agent)
):
    if report_type == "performance":
        pdf_buffer = ReportService.generate_performance_report(db, agent)
        filename = "performance_summary_report.pdf"
    else:
        pdf_buffer = ReportService.generate_assessment_report(db, agent)
        filename = "risk_assessment_report.pdf"
        
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
