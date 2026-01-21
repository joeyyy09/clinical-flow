from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_db
from services.risk_monitor_service import RiskMonitorService
from services.analytics_service import AnalyticsService
from services.ml_service_risk import MLRiskService

router = APIRouter(prefix="/analytics", tags=["Risk & Analytics"])

@router.get("/risk")
def get_risk_heatmap(db: Session = Depends(get_db)):
    return RiskMonitorService.get_risk_heatmap_data(db)

@router.get("/score")
def get_study_score(db: Session = Depends(get_db)):
    return {"score": AnalyticsService.calculate_study_health_score(db)}

@router.get("/trend")
def get_trends():
    return AnalyticsService.get_sae_trend()

@router.get("/risk-monitor")
def get_risk_monitor(db: Session = Depends(get_db)):
    return RiskMonitorService.get_detailed_risk_data(db)

@router.get("/ml-status")
def get_ml_status():
    return MLRiskService.get_ml_status()

@router.get("/missing-visits")
def get_missing_visits(db: Session = Depends(get_db)):
    """Returns visits that are overdue, ordered by days outstanding"""
    try:
        from core import models
        visits = db.query(models.VisitProjection)\
                   .filter(models.VisitProjection.days_outstanding > 0)\
                   .order_by(models.VisitProjection.days_outstanding.desc())\
                   .limit(100)\
                   .all()
        return [
            {
                "study_id": v.study_id or "",
                "country": v.country or "",
                "site": v.site or "",
                "subject": v.subject or "",
                "visit": v.visit or "",
                "projected_date": v.projected_date or "",
                "days_outstanding": v.days_outstanding or 0
            } for v in visits
        ]
    except Exception as e:
        print(f"Error in missing-visits: {e}")
        return []

@router.get("/lab-gaps")
def get_lab_data_gaps(db: Session = Depends(get_db)):
    """Returns lab data quality issues (missing names/ranges)"""
    try:
        from core import models
        labs = db.query(models.MissingLabData)\
                 .order_by(models.MissingLabData.site_number)\
                 .limit(100)\
                 .all()
        return [
            {
                "study_id": l.study_id or "",
                "country": l.country or "",
                "site_number": l.site_number or "",
                "subject": l.subject or "",
                "visit": l.visit or "",
                "form_name": l.form_name or "",
                "lab_category": l.lab_category or "",
                "test_name": l.test_name or "",
                "issue": l.issue or "",
                "comments": l.comments or ""
            } for l in labs
        ]
    except Exception as e:
        print(f"Error in lab-gaps: {e}")
        return []

@router.get("/sae-reviews")
def get_sae_reviews(db: Session = Depends(get_db)):
    """Returns SAE review status including DM and Safety reviews"""
    try:
        from core import models
        saes = db.query(models.SAEMetrics)\
                 .filter(models.SAEMetrics.discrepancy_id != None)\
                 .filter(models.SAEMetrics.discrepancy_id != "")\
                 .order_by(models.SAEMetrics.created_timestamp.desc())\
                 .limit(100)\
                 .all()
        return [
            {
                "discrepancy_id": s.discrepancy_id or "",
                "study_id": s.study_id or "",
                "country": s.country or "",
                "site": s.site or "",
                "patient_id": s.patient_id or "",
                "form_name": s.form_name or "",
                "review_status": s.review_status or "",
                "action_status": s.action_status or "",
                "case_status": s.case_status or "",
                "created_timestamp": s.created_timestamp or ""
            } for s in saes
        ]
    except Exception as e:
        print(f"Error in sae-reviews: {e}")
        return []

@router.get("/coding-status")
def get_coding_status(db: Session = Depends(get_db)):
    """Summary of MedDRA and WHODrug coding status"""
    from core import models
    from sqlalchemy import func
    
    try:
        # MedDRA Stats
        meddra_total = db.query(models.MedDRACoding).count()
        meddra_uncoded = db.query(models.MedDRACoding).filter(models.MedDRACoding.coding_status.ilike('%uncoded%')).count()
        
        # WHODrug Stats
        who_total = db.query(models.WHODrugCoding).count()
        who_uncoded = db.query(models.WHODrugCoding).filter(models.WHODrugCoding.coding_status.ilike('%uncoded%')).count()
        
        return {
            "meddra": {"total": meddra_total, "uncoded": meddra_uncoded, "coded": meddra_total - meddra_uncoded},
            "whodrug": {"total": who_total, "uncoded": who_uncoded, "coded": who_total - who_uncoded}
        }
    except Exception as e:
        print(f"Error in coding-status: {e}")
        return {"meddra": {"total":0,"uncoded":0}, "whodrug": {"total":0,"uncoded":0}}

@router.get("/edrr-status")
def get_edrr_status(db: Session = Depends(get_db)):
    """Top subjects with open issues from EDRR"""
    from core import models
    try:
        issues = db.query(models.EDRRIssue)\
                   .filter(models.EDRRIssue.open_issue_count > 0)\
                   .order_by(models.EDRRIssue.open_issue_count.desc())\
                   .limit(10)\
                   .all()
        return [{"subject": i.subject, "count": i.open_issue_count} for i in issues]
    except Exception as e:
        print(f"Error in edrr-status: {e}")
        return []

@router.get("/inactivated-audit")
def get_inactivated_audit(db: Session = Depends(get_db)):
    """Recent inactivated records"""
    from core import models
    try:
        records = db.query(models.InactivatedForm).limit(50).all()
        return [
            {
                "site": r.site,
                "subject": r.subject,
                "form": r.form,
                "action": r.audit_action,
                "folder": r.folder
            } for r in records
        ]
    except Exception as e:
        print(f"Error in inactivated-audit: {e}")
        return []
