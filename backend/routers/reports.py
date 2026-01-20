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
def generate_report(db: Session = Depends(get_db), agent: ClinicalAgent = Depends(get_agent)):
    pdf_buffer = ReportService.generate_assessment_report(db, agent)
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=risk_assessment_report.pdf"}
    )
