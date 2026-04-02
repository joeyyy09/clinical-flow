import time
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.ml_service_risk import MLRiskService

def benchmark_batch():
    print("Starting Batch benchmark...")
    start_load = time.time()
    model = MLRiskService.load_model()
    end_load = time.time()
    print(f"Model load time: {end_load - start_load:.4f}s")
    
    if model is None:
        print("Model failed to load.")
        return

    # Simulate 300 sites
    N = 300
    batch_data = [{'missing_pages': 10, 'sae_count': 2, 'subject_count': 50} for _ in range(N)]
    
    start_pred = time.time()
    MLRiskService.predict_batch(batch_data)
    end_pred = time.time()
    
    total_time = end_pred - start_pred
    print(f"Total prediction time for {N} calls (Batch): {total_time:.4f}s")

if __name__ == "__main__":
    benchmark_batch()
