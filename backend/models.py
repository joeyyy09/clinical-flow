
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, unique=True, index=True)
    
class SAEMetrics(Base):
    __tablename__ = "sae_metrics"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    country = Column(String)
    site = Column(String)
    patient_id = Column(String)
    review_status = Column(String)
    action_status = Column(String)
    
class MissingPages(Base):
    __tablename__ = "missing_pages"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    site_number = Column(String)
    subject_name = Column(String)
    form_name = Column(String)
    visit_date = Column(String) # Keeping as string for flexibility with bad data
    missing_days = Column(Integer)

class VisitProjection(Base):
    __tablename__ = "visit_projections"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    subject_id = Column(String)
    visit_name = Column(String)
    projected_date = Column(Date)
    actual_date = Column(Date)

class EDCMetrics(Base):
    __tablename__ = "edc_metrics"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    site_id = Column(String)
    subject_id = Column(String)
    subject_status = Column(String)
    latest_visit = Column(String)

class SiteComment(Base):
    __tablename__ = "site_comments"
    id = Column(Integer, primary_key=True, index=True)
    site_number = Column(String, index=True)
    comment = Column(String)
    tag = Column(String, default="Info")
    author = Column(String)
    created_at = Column(DateTime)
