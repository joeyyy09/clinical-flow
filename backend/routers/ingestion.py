from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from core.deps import get_db
from services.patient_service import PatientService
from services.ingestion_service import IngestionService
import shutil
import os

router = APIRouter(tags=["Ingestion & Subjects"])

@router.post("/ingest")
def trigger_ingestion():
    IngestionService.run_full_pipeline()
    return {"message": "Ingestion triggered"}

@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    # Standard uploads directory
    upload_dir = os.path.join(os.getcwd(), "uploads")
    if not os.path.exists(upload_dir): os.makedirs(upload_dir)
    file_location = os.path.join(upload_dir, file.filename)
    try:
        with open(file_location, "wb+") as f: shutil.copyfileobj(file.file, f)
        IngestionService.run_full_pipeline()
        return {"message": f"Successfully ingested {file.filename}", "status": "processing"}
    except Exception as e:
        return {"message": f"Error: {str(e)}", "status": "error"}

@router.get("/sites/{site_number}/patients")
def get_site_patients(site_number: str, db: Session = Depends(get_db)):
    return PatientService.get_site_patients_data(db, site_number)
