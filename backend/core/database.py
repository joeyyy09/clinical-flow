
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Render and other providers often use postgres:// while SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "clinical_trials.db")
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30  # Add 30 second timeout to prevent database locks
    },
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600    # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
