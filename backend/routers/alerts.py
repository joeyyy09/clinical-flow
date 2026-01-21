from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_db
from core import models

router = APIRouter(prefix="/alerts", tags=["Collaboration"])

@router.get("/{user_handle}")
def get_user_alerts(user_handle: str, db: Session = Depends(get_db)):
    # Note: user_handle should include the @
    return db.query(models.UserAlert).filter(models.UserAlert.user_handle == user_handle).order_by(models.UserAlert.created_at.desc()).all()

@router.post("/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.UserAlert).filter(models.UserAlert.id == alert_id).first()
    if alert:
        alert.is_read = 1
        db.commit()
        return {"status": "success"}
    return {"status": "error", "message": "Alert not found"}
