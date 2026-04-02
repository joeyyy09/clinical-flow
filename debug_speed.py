import time
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.ml_service_risk import MLRiskService

def benchmark():
    print("Starting benchmark...")
    start_load = time.time()
    model = MLRiskService.load_model()
    end_load = time.time()
    print(f"Model load time: {end_load - start_load:.4f}s")

    if model is None:
        print("Model failed to load.")
        return

    # Simulate 300 sites
    N = 300
    start_pred = time.time()
    for _ in range(N):
        MLRiskService.predict_site_risk(10, 2, 50)
    end_pred = time.time()
    
    total_time = end_pred - start_pred
    avg_time = total_time / N
    print(f"Total prediction time for {N} calls: {total_time:.4f}s")
    print(f"Average time per call: {avg_time:.4f}s")

if __name__ == "__main__":
    benchmark()
