
import os
import sys

# Simulate the path calculation in backend/routers/risk.py
# backend/routers/risk.py -> backend/routers -> backend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This is running from backend/scripts/ so up 2 levels = clinical-flow/backend ? No.
# backend/scripts/debug.py -> backend/scripts -> backend. 
# wait, the routers calculation was: os.path.dirname(os.path.dirname(os.path.abspath(__file__))) from risk.py
# risk.py is in backend/routers/
# .../backend/routers/risk.py
# dirname -> .../backend/routers
# dirname -> .../backend

print("--- DEBUGGING PATHS ---")
current_file = os.path.abspath(__file__)
print(f"Script location: {current_file}")

# Let's verify what risk.py would see
import backend.routers.risk
risk_file = os.path.abspath(backend.routers.risk.__file__)
print(f"Risk Router File: {risk_file}")

risk_base_dir = os.path.dirname(os.path.dirname(risk_file))
print(f"Calculated Base Dir (from risk.py): {risk_base_dir}")

metrics_path = os.path.join(risk_base_dir, 'ml', 'model_metrics.json')
print(f"Calculated Metrics Path: {metrics_path}")

exists = os.path.exists(metrics_path)
print(f"File Exists? {exists}")

if exists:
    import json
    try:
        with open(metrics_path, 'r') as f:
            data = json.load(f)
            print("JSON Content Loaded: YES")
            print(f"Keys: {list(data.keys())}")
    except Exception as e:
        print(f"JSON Read Error: {e}")
else:
    print("Listing backend/ml directory:")
    ml_dir = os.path.join(risk_base_dir, 'ml')
    if os.path.exists(ml_dir):
        print(os.listdir(ml_dir))
    else:
        print(f"ML Dir '{ml_dir}' does not exist")
