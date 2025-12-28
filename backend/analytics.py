
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import pandas as pd
import random
from typing import List, Dict

def calculate_study_health_score(db: Session, study_id: str = None):
    # Heuristic scoring model (0-100)
    # 1. SAE Pending Review Ratio (Lower is better)
    # 2. Missing Pages per active subject (Lower is better)
    
    query_sae = db.query(models.SAEMetrics)
    query_missing = db.query(models.MissingPages)
    
    if study_id:
        query_sae = query_sae.filter(models.SAEMetrics.study_id == study_id)
        query_missing = query_missing.filter(models.MissingPages.study_id == study_id)

    df_sae = pd.read_sql(query_sae.statement, db.bind)
    df_missing = pd.read_sql(query_missing.statement, db.bind)
    
    # Calculate SAE Component
    if not df_sae.empty:
        total_saes = len(df_sae)
        pending = len(df_sae[df_sae['review_status'] != 'Reviewed'])
        sae_score = max(0, 100 - (pending / total_saes * 50)) # Penalty up to 50 points
    else:
        sae_score = 100

    # Calculate Missing Pages Component
    if not df_missing.empty:
        total_missing = len(df_missing)
        # Normalize by assuming 100 subjects for demo purposes if not known
        missing_density = total_missing / 100 
        missing_score = max(0, 100 - (missing_density * 2)) # 2 points penalty per missing page/subject ratio unit
    else:
        missing_score = 100
        
    final_score = (sae_score * 0.4) + (missing_score * 0.6)
    return int(final_score)

def calculate_data_quality_index(db: Session, site_number: str):
    # DQI = Weighted average of core quality metrics (0-100)
    # Weights: Missing Pages (40%), Query Latency (30%), SAE Conformity (30%)
    
    # 1. Missing Pages Score
    missing_count = db.query(models.MissingPages).filter(models.MissingPages.site_number == site_number).count()
    # Benchmark: > 10 missing pages is 0 score. 0 missing is 100.
    missing_score = max(0, 100 - (missing_count * 10))
    
    # 2. Query Latency (Mocked for now as we don't have query table yet, using rand for demo robustness)
    # Ideally link to Query table.
    latency = random.randint(1, 10) 
    latency_score = max(0, 100 - (latency * 5)) # > 20 days is 0.
    
    # 3. SAE Conformity
    # Ratio of Reviewed SAEs vs Total
    sae_total = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site_number)).count()
    if sae_total == 0:
        sae_score = 100
    else:
        pending = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site_number), models.SAEMetrics.review_status != 'Reviewed').count()
        sae_score = int(((sae_total - pending) / sae_total) * 100)
    
    dqi = (missing_score * 0.4) + (latency_score * 0.3) + (sae_score * 0.3)
    return int(dqi)

def get_risk_heatmap_data(db: Session):
    # Aggregate missing pages by Site and Country
    # Used for Dashboard Heatmap
    results = db.query(
        models.MissingPages.site_number, 
        func.count(models.MissingPages.id).label('missing_count')
    ).group_by(models.MissingPages.site_number).order_by(func.count(models.MissingPages.id).desc()).limit(10).all()
    
    return [{"site": r[0], "risk_score": r[1]} for r in results]

def get_detailed_risk_data(db: Session):
    # For Risk Monitor Table
    # Returns: Site, Country, SAE Count, Missing Pages, Avg Query Latency (Mocked), Risk Level
    
    # 1. Get Top Sites by missing pages
    top_sites_query = db.query(
        models.MissingPages.site_number, 
        func.count(models.MissingPages.id).label('missing_cnt')
    ).group_by(models.MissingPages.site_number).order_by(func.count(models.MissingPages.id).desc()).limit(20)
    
    df_sites = pd.read_sql(top_sites_query.statement, db.bind)
    
    results = []
    for _, row in df_sites.iterrows():
        site = row['site_number']
        missing = row['missing_cnt']
        
        # Get SAEs for this site (approximate match since SAE file might have slightly different site naming format, but we try)
        # In this demo dataset, SAE file has 'Site' column. 
        sae_count = db.query(models.SAEMetrics).filter(models.SAEMetrics.site.contains(site)).count()
        
        # Mocking Latency data
        latency = random.randint(2, 15)
        
        # Determine Risk
        risk_score = (missing * 0.5) + (sae_count * 2) + (latency * 10)
        risk_level = "High" if risk_score > 100 else "Medium" if risk_score > 50 else "Low"
        
        # Deterministic Mock Study ID based on site number hash or similar
        # Studies: Study 101 (Oncology), Study 202 (Cardio), Study 303 (Neuro)
        study_map = ["Study 101 (Oncology)", "Study 202 (Cardio)", "Study 303 (Neuro)"]
        study_id = study_map[hash(site) % 3]

        results.append({
            "site": site,
            "country": "USA", # Placeholder/Mock or lookup if available
            "study_id": study_id,
            "sae_count": sae_count,
            "missing_pages": missing,
            "query_latency": latency,
            "risk_level": risk_level,
            "dqi": calculate_data_quality_index(db, site),
            "recommendation": generate_recommendation(risk_level, missing, sae_count)
        })
        
    return results

    return results

def get_site_patients_data(db: Session, site_number: str):
    # Aggregates data to form a Patient-Level view for a specific site
    # Determines "Clean Patient" status: No Missing Pages AND No Pending SAEs
    
    # 1. Get all subjects for this site from EDC Metrics (Single Source of Truth for Subjects)
    # If EDC metrics is empty for this site, we might fallback to other tables, but let's assume EDC is populated
    subjects = db.query(models.EDCMetrics).filter(models.EDCMetrics.site_id == site_number).all()
    
    # If no EDC entries, try to infer from MissingPages or SAEs for robustness in this demo
    if not subjects:
        # distinct subjects from missing pages
        distinct_missing = db.query(models.MissingPages.subject_name).filter(models.MissingPages.site_number == site_number).distinct().all()
        # Create mock objects
        subjects = [models.EDCMetrics(subject_id=r[0], subject_status="Active") for r in distinct_missing]

    patient_data = []
    clean_count = 0
    total_count = len(subjects)

    for sub in subjects:
        sub_id = sub.subject_id
        
        # Check Missing Pages
        missing_count = db.query(models.MissingPages).filter(
            models.MissingPages.site_number == site_number, 
            models.MissingPages.subject_name == sub_id
        ).count()
        
        # Check SAEs
        sae_pending = db.query(models.SAEMetrics).filter(
            models.SAEMetrics.site.contains(site_number),
            models.SAEMetrics.patient_id == sub_id,
            models.SAEMetrics.review_status != 'Reviewed'
        ).count()
        
        is_clean = (missing_count == 0) and (sae_pending == 0)
        if is_clean:
            clean_count += 1
            
        patient_data.append({
            "subject_id": sub_id,
            "status": sub.subject_status,
            "is_clean": is_clean,
            "missing_pages": missing_count,
            "sae_pending": sae_pending,
            "last_visit": sub.latest_visit or "N/A"
        })
        
    return {
        "site_id": site_number,
        "total_patients": total_count,
        "clean_patient_count": clean_count,
        "clean_patient_rate": int((clean_count/total_count * 100) if total_count > 0 else 100),
        "topics": patient_data
    }

def generate_recommendation(risk, missing, sae):
    if risk == "High":
        if missing > sae * 5:
            return "Audit Site: High Missing Data volume."
        elif sae > 5:
            return "Safety Review Required: High SAE frequency."
        else:
             return "Intensive Monitoring recommended."
    elif risk == "Medium":
        return "Schedule remote monitoring visit."
    else:
        return "Maintain routine surveillance."

def get_sae_trend(db: Session):
    # Mocking time-series because current SAE data doesn't have clear dates in the columns I mapped
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    values = [12, 19, 3, 5, 2, 30] # Mock data for the visual boost
    return [{"month": m, "sae_count": v} for m, v in zip(months, values)]

def get_generated_reports():
    # Mock list of available reports
    return [
        {"id": 1, "title": "Protocol Deviation Summary - Q3", "date": "2025-10-15", "type": "Compliance", "status": "Ready"},
        {"id": 2, "title": "Safety Signal Detection - Site 404", "date": "2025-11-01", "type": "Safety", "status": "Ready"},
        {"id": 3, "title": "Missing Data Trends - Global", "date": "2025-11-10", "type": "Data Quality", "status": "Processing"}
    ]
