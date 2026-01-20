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
