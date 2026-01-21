
from services.analytics_service import AnalyticsService
from core.database import SessionLocal
from core.agent import ClinicalAgent
import json

db = SessionLocal()
agent = ClinicalAgent()

print("--- Stats (Agent) ---")
try:
    stats = agent.get_summary()
    print(json.dumps(stats['data'], indent=2))
except Exception as e:
    print(f"Stats Error: {e}")

print("\n--- Score (Analytics) ---")
try:
    score = AnalyticsService.calculate_study_health_score(db)
    print(f"Score: {score}")
except Exception as e:
    print(f"Score Error: {e}")

print("\n--- Trend (Analytics) ---")
try:
    trend = AnalyticsService.get_sae_trend()
    print(json.dumps(trend, indent=2))
except Exception as e:
    print(f"Trend Error: {e}")

from services.risk_monitor_service import RiskMonitorService
print("\n--- Heatmap (Risk) ---")
try:
    heatmap = RiskMonitorService.get_risk_heatmap_data(db)
    print(json.dumps(heatmap[:3], indent=2))
except Exception as e:
    print(f"Heatmap Error: {e}")
