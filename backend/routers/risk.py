from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.deps import get_db, get_current_user
from services.risk_monitor_service import RiskMonitorService
from services.analytics_service import AnalyticsService
from services.ml_service_risk import MLRiskService

# Try importing advanced ML service
try:
    from services.ml_prediction_service import MLPredictionService
    HAS_ADVANCED_ML = True
except ImportError:
    HAS_ADVANCED_ML = False

router = APIRouter(prefix="/analytics", tags=["Risk & Analytics"])

@router.get("/risk")
def get_risk_heatmap(db: Session = Depends(get_db)):
    return RiskMonitorService.get_risk_heatmap_data(db)

@router.get("/score")
def get_study_score(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Protected Endpoint: Requires authenticated clinical user."""
    return {"score": AnalyticsService.calculate_study_health_score(db)}

@router.get("/trend")
def get_trends(db: Session = Depends(get_db)):
    return AnalyticsService.get_sae_trend(db)

@router.get("/risk-monitor")
def get_risk_monitor(db: Session = Depends(get_db)):
    return RiskMonitorService.get_detailed_risk_data(db)

@router.get("/ml-status")
def get_ml_status():
    """Get status of ML model (flat structure for frontend compatibility)."""
    
    # Default/Legacy status
    status = MLRiskService.get_ml_status()
    
    if HAS_ADVANCED_ML:
        advanced_status = MLPredictionService.get_model_status()
        
        if advanced_status.get("status") == "operational":
            # Merge advanced metadata but keep the static image paths
            # The Advanced Model generates these same images in the same location
            status.update({
                "model_type": f"Advanced {advanced_status.get('architecture', 'Ensemble')}",
                "last_trained": advanced_status.get("version", "2.0.0"),
                "accuracy": advanced_status.get("accuracy"),
                "n_features": advanced_status.get("n_features")
            })

    # EMERGENCY PATCH: Directly inject metrics from file to ensure frontend gets them
    try:
        import os
        import json
        # Go up one level from routers to backend, then to ml/model_metrics.json
        # backend/routers/risk.py -> backend/routers -> backend
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        metrics_path = os.path.join(base_dir, 'ml', 'model_metrics.json')
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics_data = json.load(f)
                status['metrics'] = metrics_data
                # print("Force injected metrics into status")
    except Exception as e:
        print(f"Error injecting metrics: {str(e)}")
        status['_debug_error'] = f"Injection failed: {str(e)} Path: {metrics_path}"
            
    return status

@router.get("/ml-predict/{site_id}")
def predict_site_risk_advanced(site_id: str):
    """
    Get advanced ML prediction with explainability for a specific site.
    
    Returns:
        - risk_level: Predicted risk level (Low/Medium/High)
        - confidence: Model confidence (0-1)
        - probability_distribution: Probability for each risk level
        - top_risk_factors: Explained risk factors with SHAP values
        - dqi_percentile: Site's DQI percentile ranking
    """
    if not HAS_ADVANCED_ML:
        return {
            "error": "Advanced ML service not available",
            "fallback": MLRiskService.predict_site_risk(0, 0, 1)
        }
    
    return MLPredictionService.predict_site_risk(site_id)

@router.get("/ml-predict-batch")
def predict_batch_risk(site_ids: Optional[str] = Query(default=None)):
    """
    Get batch predictions for multiple sites.
    
    Args:
        site_ids: Comma-separated list of site IDs, or None for all sites
    """
    if not HAS_ADVANCED_ML:
        return {"error": "Advanced ML service not available"}
    
    ids = site_ids.split(",") if site_ids else None
    return MLPredictionService.predict_batch(ids)

@router.get("/ml-feature-importance")
def get_feature_importance():
    """Get global feature importance rankings from the ML model."""
    if not HAS_ADVANCED_ML:
        return {"error": "Advanced ML service not available"}
    
    return MLPredictionService.get_feature_importance()

@router.post("/ml-retrain")
def retrain_ml_model():
    """Force retrain the ML model with latest data."""
    if not HAS_ADVANCED_ML:
        return {"error": "Advanced ML service not available"}
    
    return MLPredictionService.retrain_model()

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
    from sqlalchemy import func
    try:
        issues = db.query(
            models.EDRRIssue.subject,
            func.max(models.EDRRIssue.open_issue_count).label('count')
        )\
        .group_by(models.EDRRIssue.subject)\
        .having(func.max(models.EDRRIssue.open_issue_count) > 0)\
        .order_by(func.max(models.EDRRIssue.open_issue_count).desc())\
        .limit(10)\
        .all()
        return [{"subject": i.subject, "count": i.count} for i in issues]
    except Exception as e:
        print(f"Error in edrr-status: {e}")
        return []

@router.get("/readiness")
def get_study_readiness(db: Session = Depends(get_db)):
    """Returns detailed study readiness for statistical deliverables"""
    return AnalyticsService.calculate_study_readiness(db)

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
