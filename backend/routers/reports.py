"""
Reports API Router

Provides endpoints for:
- AI-powered report generation (Site, CRA, Executive)
- PDF export with AI narratives
- Report history and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from dataclasses import asdict
import json

from core.deps import get_db, get_agent, get_current_user
from core.agent import ClinicalAgent
from services.report_service import ReportService
from services.report_generator_llm import get_report_generator, GeneratedReport, ReportType
from services.risk_monitor_service import RiskMonitorService

try:
    from services.ml_prediction_service import MLPredictionService
    HAS_ML_SERVICE = True
except ImportError:
    HAS_ML_SERVICE = False

router = APIRouter(prefix="/reports", tags=["Reports"])

# In-memory storage for generated reports (use DB in production)
_generated_reports: dict = {}


@router.get("")
def get_reports():
    """Get list of available reports."""
    # Combine static reports with generated ones
    static_reports = ReportService.get_report_list()
    
    # Add generated reports
    generated = [
        {
            "id": r.report_id,
            "title": r.title,
            "date": r.generated_at[:10],
            "type": r.report_type.replace("_", " ").title(),
            "status": "Ready" if r.status == "complete" else "Processing",
            "generation_source": r.generation_source
        }
        for r in _generated_reports.values()
    ]
    
    return static_reports + generated


@router.post("/generate")
def generate_report(db: Session = Depends(get_db), agent: ClinicalAgent = Depends(get_agent)):
    """Generate legacy PDF report (backward compatibility)."""
    pdf_buffer = ReportService.generate_assessment_report(db, agent)
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": "attachment; filename=risk_assessment_report.pdf"}
    )


@router.post("/generate/site/{site_id}")
def generate_site_report(site_id: str, db: Session = Depends(get_db)):
    """
    Generate AI-powered site risk assessment report.
    
    Args:
        site_id: Site identifier
        
    Returns:
        GeneratedReport: Structured report with AI narrative
    """
    try:
        # Get site data
        all_sites = RiskMonitorService.get_detailed_risk_data(db)
        site_data = next((s for s in all_sites if str(s['site']) == str(site_id)), None)
        
        # Try alternate formats
        if not site_data:
            for s in all_sites:
                if f"Site {s['site']}" == site_id or str(s['site']).lstrip('0') == str(site_id).lstrip('0'):
                    site_data = s
                    break
        
        if not site_data:
            raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
        
        # Get ML prediction
        ml_prediction = None
        if HAS_ML_SERVICE:
            try:
                ml_prediction = MLPredictionService.predict_site_risk(site_id)
            except Exception as e:
                print(f"ML prediction failed: {e}")
        
        # Generate report
        generator = get_report_generator()
        report = generator.generate_site_risk_report(site_id, site_data, ml_prediction)
        
        # Store report
        _generated_reports[report.report_id] = report
        
        return asdict(report)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/cra/{cra_id}")
def generate_cra_report(cra_id: str, db: Session = Depends(get_db)):
    """
    Generate AI-powered CRA performance report.
    
    Args:
        cra_id: CRA identifier (name or ID)
        
    Returns:
        GeneratedReport: CRA performance assessment
    """
    try:
        from core import models
        
        # Get CRA activity logs
        activities = db.query(models.CRAActivityLog)\
            .filter(models.CRAActivityLog.cra_name.ilike(f"%{cra_id}%"))\
            .order_by(models.CRAActivityLog.timestamp.desc())\
            .limit(20)\
            .all()
        
        activity_list = [
            {
                "action": a.action,
                "site_id": a.site_id,
                "details": a.details,
                "timestamp": str(a.timestamp) if a.timestamp else ""
            }
            for a in activities
        ]
        
        # Get sites assigned to this CRA (based on activity)
        site_ids = list(set(a.site_id for a in activities if a.site_id))
        
        # Build CRA data
        cra_data = {
            "name": cra_id,
            "sites": site_ids,
            "total_visits": len([a for a in activities if "visit" in (a.action or "").lower()]),
            "issues_resolved": len([a for a in activities if "resolve" in (a.action or "").lower()]),
            "avg_response_time": 0,  # Metric pending implementation of derived timestamps
            "sites_at_risk": 0  # Would cross-reference with risk data
        }
        
        # Cross-reference with risk data
        all_sites = RiskMonitorService.get_detailed_risk_data(db)
        cra_data["sites_at_risk"] = len([
            s for s in all_sites 
            if str(s['site']) in site_ids and s['risk_level'] == 'High'
        ])
        
        # Generate report
        generator = get_report_generator()
        report = generator.generate_cra_performance_report(cra_id, cra_data, activity_list)
        
        # Store report
        _generated_reports[report.report_id] = report
        
        return asdict(report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/executive")
def generate_executive_report(
    study_id: str = Query(default="CT-2024-001"),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered executive summary report.
    
    Args:
        study_id: Study identifier
        
    Returns:
        GeneratedReport: Executive dashboard summary
    """
    try:
        # Get all site data
        all_sites = RiskMonitorService.get_detailed_risk_data(db)
        
        if not all_sites:
            raise HTTPException(status_code=404, detail="No site data available")
        
        # Calculate study-level metrics
        high_risk = len([s for s in all_sites if s['risk_level'] == 'High'])
        medium_risk = len([s for s in all_sites if s['risk_level'] == 'Medium'])
        low_risk = len([s for s in all_sites if s['risk_level'] == 'Low'])
        
        total_subjects = sum(s.get('subject_count', 0) for s in all_sites)
        total_missing = sum(s.get('missing_pages', 0) for s in all_sites)
        total_saes = sum(s.get('sae_count', 0) for s in all_sites)
        avg_dqi = sum(s.get('dqi', 0) for s in all_sites) / max(1, len(all_sites))
        
        # Get readiness from analytics
        from services.analytics_service import AnalyticsService
        readiness = AnalyticsService.calculate_study_readiness(db)
        
        study_metrics = {
            "study_id": study_id,
            "total_sites": len(all_sites),
            "total_subjects": total_subjects,
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "avg_dqi": round(avg_dqi, 1),
            "readiness_score": readiness.get("readiness_score", 0),
            "pending_saes": sum(s.get('sae_count', 0) for s in all_sites if s['risk_level'] == 'High'),
            "total_missing": total_missing
        }
        
        # Site summaries for context
        site_summaries = [
            {
                "site_id": s['site'],
                "risk_level": s['risk_level'],
                "dqi": s['dqi']
            }
            for s in sorted(all_sites, key=lambda x: x['dqi'])[:5]  # Bottom 5
        ]
        
        # Generate report
        generator = get_report_generator()
        report = generator.generate_executive_summary(study_id, study_metrics, site_summaries)
        
        # Store report
        _generated_reports[report.report_id] = report
        
        return asdict(report)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved")
def get_saved_reports():
    """Get list of all saved/generated reports."""
    return [
        {
            "report_id": r.report_id,
            "report_type": r.report_type,
            "title": r.title,
            "generated_at": r.generated_at,
            "status": r.status,
            "generation_source": r.generation_source
        }
        for r in _generated_reports.values()
    ]


@router.get("/{report_id}")
def get_report(report_id: str):
    """
    Retrieve a specific generated report.
    
    Args:
        report_id: Report identifier
        
    Returns:
        GeneratedReport: Full report content
    """
    if report_id not in _generated_reports:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    return asdict(_generated_reports[report_id])


@router.delete("/{report_id}")
def delete_report(report_id: str):
    """Delete a generated report."""
    if report_id not in _generated_reports:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    del _generated_reports[report_id]
    return {"status": "deleted", "report_id": report_id}


@router.get("/types/available")
def get_report_types():
    """Get available report types."""
    return [
        {
            "type": "site_risk",
            "name": "Site Risk Assessment",
            "description": "Comprehensive risk analysis for a specific site",
            "requires": ["site_id"]
        },
        {
            "type": "cra_performance",
            "name": "CRA Performance Summary",
            "description": "Performance analysis for a Clinical Research Associate",
            "requires": ["cra_id"]
        },
        {
            "type": "executive_summary",
            "name": "Executive Summary",
            "description": "High-level study overview for leadership",
            "requires": ["study_id"]
        }
    ]
