from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from ingestion import run_ingestion
from agent import ClinicalAgent
from pydantic import BaseModel
import pandas as pd
<<<<<<< HEAD
import models
from datetime import datetime
=======
from dotenv import load_dotenv

load_dotenv()
>>>>>>> 782bab7 (feat: Implement Scientific AI Agent with Gemini, fix ingestion, refine UI)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinical Trial Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://127.0.0.1:5173"], # Allow all origins for hackathon demo
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
    
    # Generate AI Narrative
    # Use the agent to create a natural language summary
    try:
        from main import agent
        summary_prompt = f"Summarize the risk status for {len(risk_data)} clinical sites. There are {high_risk} high risk sites. The average DQI is {sum(r['dqi'] for r in risk_data)/len(risk_data):.1f}."
        ai_summary = agent.query(summary_prompt).get('answer', '')
    except:
        ai_summary = None

    report_context = {
        "study_id": "CT-2024-001", # Mock context
        "sites": risk_data,
        "site_count": len(risk_data),
        "high_risk_count": high_risk,
        "executive_summary": ai_summary
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
    from ingestion import DATA_DIR
    
    # Ensure DATA_DIR exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    file_location = os.path.join(DATA_DIR, file.filename)
    
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        # Trigger ingestion pipeline
        run_ingestion()
        
        return {"message": f"Successfully ingested {file.filename}", "status": "processing"}
    except Exception as e:
        return {"message": f"Error interacting with file: {str(e)}", "status": "error"}

class CommentRequest(BaseModel):
    comment: str
    author: str
    tag: str = "Info"

@app.post("/sites/{site_number}/comment")
def add_site_comment(site_number: str, request: CommentRequest, db: Session = Depends(get_db)):
    db_comment = models.SiteComment(
        site_number=site_number,
        comment=request.comment,
        tag=request.tag,
        author=request.author,
        created_at=datetime.now()
    )
    db.add(db_comment)
    db.commit()
    return {"status": "success", "message": "Comment added"}

@app.get("/sites/{site_number}/comments")
def get_site_comments(site_number: str, db: Session = Depends(get_db)):
    return db.query(models.SiteComment).filter(models.SiteComment.site_number == site_number).all()

@app.get("/sites/{site_number}/patients")
def get_site_patients(site_number: str, db: Session = Depends(get_db)):
    from analytics import get_site_patients_data
    return get_site_patients_data(db, site_number)


