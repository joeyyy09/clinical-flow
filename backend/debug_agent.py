
from agent import ClinicalAgent
import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

try:
    agent = ClinicalAgent()
    print("Testing get_summary()...")
    summary = agent.get_summary()
    print("Summary result keys:", summary.keys())
    # Try to serialize
    print(json.dumps(summary, cls=NpEncoder))

    print("\nTesting analyze_missing_pages()...")
    missing = agent.analyze_missing_pages()
    print("Missing result keys:", missing.keys())
    # Try to serialize
    try:
        json.dumps(missing)
        print("Serialization success")
    except TypeError as e:
        print("Serialization FAILED:", e)

except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
