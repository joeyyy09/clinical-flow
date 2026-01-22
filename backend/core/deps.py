from .database import SessionLocal
from .agent import ClinicalAgent

# Global instance
_agent = ClinicalAgent()

def get_db():
    """Provides a database session for request handling."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_agent():
    """Provides the AI Clinical Agent instance."""
    return _agent

def get_current_user():
    """
    Simulates a secure User Authentication dependency (OAuth2/JWT).
    For Hackathon Demo: Returns a hardcoded 'Authenticated' user.
    Production: Would validate Bearer token from 'Authorization' header.
    """
    return {
        "id": "USR-101",
        "username": "dr_smith",
        "role": "Clinical Admin",
        "permissions": ["view_phi", "edit_risk", "generate_reports"],
        "clearance_level": "Level 3"
    }
