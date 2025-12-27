from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from ingestion import run_ingestion
from agent import ClinicalAgent
from pydantic import BaseModel
import pandas as pd

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinical Trial Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ClinicalAgent()

class ChatRequest(BaseModel):
    query: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Clinical Trial Insights API is running"}

@app.post("/ingest")
def trigger_ingestion():
    run_ingestion()
    return {"message": "Ingestion triggered"}

@app.post("/chat")
def chat_with_agent(request: ChatRequest):
    response = agent.query(request.query)
    return response

@app.get("/stats")
def get_stats():
    return agent.get_summary()

@app.get("/analytics/risk")
def get_risk_heatmap(db: Session = Depends(get_db)):
    from analytics import get_risk_heatmap_data
    return get_risk_heatmap_data(db)

@app.get("/analytics/score")
def get_study_score(db: Session = Depends(get_db)):
    from analytics import calculate_study_health_score
    score = calculate_study_health_score(db)
    return {"score": score}

@app.get("/analytics/trend")
def get_trends(db: Session = Depends(get_db)):
    from analytics import get_sae_trend
    return get_sae_trend(db)

@app.get("/analytics/risk-monitor")
def get_risk_monitor(db: Session = Depends(get_db)):
    from analytics import get_detailed_risk_data
    return get_detailed_risk_data(db)

@app.get("/reports")
def get_reports():
    from analytics import get_generated_reports
    return get_generated_reports()

@app.post("/reports/generate")
def generate_report(db: Session = Depends(get_db)):
    from analytics import get_detailed_risk_data
    from reports import generate_pdf_report
    from fastapi.responses import StreamingResponse
    
    # Fetch real data for the report
    risk_data = get_detailed_risk_data(db)
    
    # Calculate summary stats for the report
    high_risk = len([r for r in risk_data if r['risk_level'] == 'High'])
    
    report_context = {
        "study_id": "CT-2024-001", # Mock context
        "sites": risk_data,
        "site_count": len(risk_data),
        "high_risk_count": high_risk
    }
    
    pdf_buffer = generate_pdf_report(report_context)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=risk_assessment_report.pdf"}
    )

@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    import shutil
    import os
    
    file_location = f"backend/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    # Trigger ingestion pipeline on this file
    run_ingestion()
    
    return {"message": f"Successfully ingested {file.filename}", "status": "processing"}


