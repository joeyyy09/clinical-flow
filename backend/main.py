from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.database import engine, Base
from dotenv import load_dotenv
import os

# Routers
from routers import risk, chat, ingestion, reports, comments, agent, cra, alerts

load_dotenv()

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinical Trial Insights")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
app.mount("/static/ml", StaticFiles(directory="ml"), name="ml")

# Include Routers
app.include_router(chat.router)
app.include_router(risk.router)
app.include_router(ingestion.router)
app.include_router(reports.router)
app.include_router(comments.router)
app.include_router(agent.router)
app.include_router(cra.router)
app.include_router(alerts.router)

@app.get("/")
def read_root():
    return {"message": "ClinicalFlow Modular API is running"}
