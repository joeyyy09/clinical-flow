from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, func
from sqlalchemy.orm import relationship
from .database import Base

class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, unique=True, index=True)
    
class SAEMetrics(Base):
    __tablename__ = "sae_metrics"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    country = Column(String)
    site = Column(String, index=True)
    patient_id = Column(String, index=True)
    review_status = Column(String)
    action_status = Column(String)
    # SAE Dashboard tracking fields
    discrepancy_id = Column(String)
    form_name = Column(String)
    created_timestamp = Column(String)
    case_status = Column(String)
    
class MissingPages(Base):
    __tablename__ = "missing_pages"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    site_number = Column(String, index=True)
    subject_name = Column(String, index=True)
    form_name = Column(String)
    visit_date = Column(String) 
    missing_days = Column(Integer)
    # New fields for Global Missing Pages
    overall_status = Column(String)
    visit_status = Column(String)
    folder_name = Column(String)
    form_type = Column(String)

class VisitProjection(Base):
    __tablename__ = "visit_projections"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    country = Column(String)
    site = Column(String, index=True)
    subject = Column(String, index=True)
    visit = Column(String)
    projected_date = Column(String)
    days_outstanding = Column(Integer, default=0)

class MissingLabData(Base):
    __tablename__ = "missing_lab_data"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    country = Column(String)
    site_number = Column(String, index=True)
    subject = Column(String, index=True)
    visit = Column(String)
    form_name = Column(String)
    lab_category = Column(String)
    lab_name = Column(String)
    lab_date = Column(String)
    test_name = Column(String)
    test_description = Column(String)
    issue = Column(String)
    comments = Column(String)

class EDCMetrics(Base):
    __tablename__ = "edc_metrics"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    project_name = Column(String)
    region = Column(String)
    country = Column(String)
    site_id = Column(String, index=True)
    subject_id = Column(String, index=True)
    latest_visit = Column(String)
    subject_status = Column(String)
    
    # New Metrics from CPID
    input_files = Column(Integer, default=0)
    cpmd = Column(String)
    ssm = Column(String)
    missing_visits = Column(Integer, default=0)
    missing_pages = Column(Integer, default=0)
    coded_terms = Column(Integer, default=0)
    uncoded_terms = Column(Integer, default=0)
    open_issues_lnr = Column(Integer, default=0)
    open_issues_edrr = Column(Integer, default=0)
    inactivated_forms = Column(Integer, default=0)
    esae_review_dm = Column(Integer, default=0)
    esae_review_safety = Column(Integer, default=0)
    
    # Statuses
    visit_status = Column(String)
    page_status = Column(String)
    queries_status = Column(String)
    page_action_status = Column(String)
    
    # Compliance
    protocol_deviations = Column(Integer, default=0)
    pi_signatures = Column(String)
    expected_visits = Column(Integer, default=0)
    pages_entered = Column(Integer, default=0)
    pages_non_conformant = Column(Integer, default=0)
    total_crfs_query_non_conformant = Column(Integer, default=0)
    total_crfs_clean = Column(Integer, default=0)
    clean_entered_crf_pct = Column(Float, default=0.0)
    
    # Query Breakdowns
    dm_queries = Column(Integer, default=0)
    clinical_queries = Column(Integer, default=0)
    medical_queries = Column(Integer, default=0)
    site_queries = Column(Integer, default=0)
    field_monitor_queries = Column(Integer, default=0)
    coding_queries = Column(Integer, default=0)
    safety_queries = Column(Integer, default=0)
    total_queries = Column(Integer, default=0)
    query_latency = Column(Integer, default=0) # Derived from Visit/Page Overdue (Proxy for Query Age)
    
    # Verification & Lock
    crfs_verified = Column(Integer, default=0)
    forms_verified = Column(Integer, default=0)
    crfs_frozen = Column(Integer, default=0)
    crfs_locked = Column(Integer, default=0)
    crfs_unlocked = Column(Integer, default=0)
    
    # Signatures
    crfs_signed = Column(Integer, default=0)
    crfs_overdue_45 = Column(Integer, default=0)
    crfs_overdue_45_90 = Column(Integer, default=0)
    crfs_overdue_90 = Column(Integer, default=0)
    broken_signatures = Column(Integer, default=0)
    never_signed = Column(Integer, default=0)
    
    responsible_lf = Column(String)
    queries_resolved = Column(Integer, default=0)

class SiteComment(Base):
    __tablename__ = "site_comments"
    id = Column(Integer, primary_key=True, index=True)
    site_number = Column(String, index=True)
    comment = Column(String)
    tag = Column(String, default="Info")
    author = Column(String)
    created_at = Column(DateTime)

class CRAActivityLog(Base):
    __tablename__ = "cra_activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    cra_name = Column(String, index=True)
    site_id = Column(String, index=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=func.now() if 'func' in globals() else None) # Need to ensure func is imported or handled

class InactivatedForm(Base):
    __tablename__ = "inactivated_forms"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    country = Column(String)
    site = Column(String, index=True)
    subject = Column(String, index=True)
    folder = Column(String)
    form = Column(String)
    record_position = Column(String)
    audit_action = Column(String)

class EDRRIssue(Base):
    __tablename__ = "edrr_issues"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    subject = Column(String, index=True)
    open_issue_count = Column(Integer, default=0)

class MedDRACoding(Base):
    __tablename__ = "meddra_coding"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    dictionary = Column(String)
    version = Column(String)
    subject = Column(String, index=True)
    form = Column(String)
    logline = Column(String)
    field_oid = Column(String)
    supplement_term = Column(String)
    coding_status = Column(String)
    require_coding = Column(String)

class WHODrugCoding(Base):
    __tablename__ = "whodrug_coding"
    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    dictionary = Column(String)
    version = Column(String)
    subject = Column(String, index=True)
    form = Column(String)
    logline = Column(String)
    field_oid = Column(String)
    trade_name = Column(String)
    coding_status = Column(String)
    require_coding = Column(String)
