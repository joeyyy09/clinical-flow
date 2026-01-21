from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from core.database import SessionLocal
from services.risk_monitor_service import RiskMonitorService

router = APIRouter(prefix="/agent", tags=["agent"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/explain-site-risk")
def explain_site_risk(site_id: str, db: Session = Depends(get_db)):
    """
    Deterministic Agent-Analyst that explains WHY a site has a certain risk score.
    Returns structured rationale and actionable steps.
    """
    # 1. Fetch Metrics
    # (In prod, we would optimize to fetch single site, but here we reuse the robust aggregator)
    all_sites = RiskMonitorService.get_detailed_risk_data(db)
    
    # Normalize comparison (site_id in URL might be "1" vs "01")
    # Our aggregation service usually normalizes site IDs to clean strings.
    target = next((s for s in all_sites if str(s['site']) == str(site_id)), None)
    
    if not target:
        # Fallback search if "Site X" format
        target = next((s for s in all_sites if f"Site {s['site']}" == str(site_id) or str(s['site']) in str(site_id)), None)
    
    if not target:
        return {
            "site_id": site_id,
            "explanation": f"The Agent could not locate sufficient metrics for Site '{site_id}' to generate a risk analysis.",
            "metrics": {},
            "action_item": "Verify site ID."
        }
    
    # 2. Generate Deterministic Explanation
    risk_level = target['risk_level']
    factors = []
    
    # Analyze Missing Pages
    if target['missing_pages'] > 50:
        factors.append(f"**Critical Missing Data**: {target['missing_pages']} pages outstanding")
    elif target['missing_pages'] > 10:
        factors.append(f"Missing Data Backlog ({target['missing_pages']} pages)")
        
    # Analyze SAEs
    if target['sae_count'] > 0:
        factors.append(f"**Safety Signal**: {target['sae_count']} SAEs reported")
        
    # Analyze Latency
    latency = target.get('query_latency', 0)
    if latency > 40:
        factors.append(f"**High Latency**: Avg query response time > {latency} days")
    elif latency > 15:
        factors.append(f"Sluggish Response ({latency} days)")
        
    # Analyze DQI
    dqi = target['dqi']
    
    explanation = f"**{result_verdict(risk_level)}** (DQI: {dqi}). "
    
    if factors:
         explanation += "This score is primarily driven by: " + "; ".join(factors) + "."
    else:
         explanation += "All operational metrics are within nominal ranges. No specific bottlenecks detected."

    # 3. Actions
    recommendation = target.get('recommendation', "Continue routine monitoring.")
    
    return {
        "site_id": site_id,
        "risk_level": risk_level,
        "explanation": explanation,
        "action_item": recommendation,
        "metrics": {
            "dqi": dqi,
            "missing": target['missing_pages'],
            "sae": target['sae_count'],
            "latency": latency
        }
    }

def result_verdict(level):
    if level == 'High': return "Critical Attention Required"
    if level == 'Medium': return "Close Monitoring Recommended"
    return "Operations Normal"
