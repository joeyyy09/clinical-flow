from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_db
from services.cra_service import CRAService

router = APIRouter(prefix="/analytics/cra", tags=["CRA Performance"])

@router.get("/performance")
def get_performance(db: Session = Depends(get_db)):
    return CRAService.get_cra_performance_metrics(db)

@router.get("/logs")
def get_logs(db: Session = Depends(get_db)):
    return CRAService.get_cra_activity_logs(db)

@router.get("/underperforming")
def get_underperforming(db: Session = Depends(get_db)):
    return CRAService.get_underperforming_sites(db)
