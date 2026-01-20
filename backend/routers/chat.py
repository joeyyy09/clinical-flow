from fastapi import APIRouter, Depends
from pydantic import BaseModel
from core.agent import ClinicalAgent
from core.deps import get_agent

router = APIRouter(prefix="/chat", tags=["AI Copilot"])

class ChatRequest(BaseModel):
    query: str

@router.post("")
def chat_with_agent(request: ChatRequest, agent: ClinicalAgent = Depends(get_agent)):
    return agent.query(request.query)

@router.get("/stats")
def get_stats(agent: ClinicalAgent = Depends(get_agent)):
    return agent.get_summary()
