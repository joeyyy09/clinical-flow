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
