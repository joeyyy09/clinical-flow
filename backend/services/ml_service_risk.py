
import joblib
import os
import random
from typing import Dict

# Model path
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'risk_model.pkl')

class MLRiskService:
    _model = None

    @classmethod
    def load_model(cls):
        if cls._model is None and os.path.exists(MODEL_PATH):
            try:
                cls._model = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
        return cls._model

    @staticmethod
    def predict_site_risk(missing: int, sae: int, subjects: int) -> str:
        """Uses the trained Random Forest model to predict site risk level."""
        model = MLRiskService.load_model()
        
        if model is None:
            return "N/A"
        
        try:
            review_rate = 0.8 # Assumed standard rate if data unavailable
            missing_per_sub = missing / max(1, subjects)
            
            features = [[sae, missing, subjects, review_rate, missing_per_sub]]
            pred = model.predict(features)[0]
            
            return ["Low", "Medium", "High"][int(pred)]
        except Exception as e:
            # print(f"ML Inference Error: {e}") # Reduce logging spam
            return "Error"

    @staticmethod
    def get_ml_status() -> Dict:
        """Returns metadata about the ML model."""
        import time
        from datetime import datetime
        
        # Get last modified time of the model to use as versioning
        timestamp = int(time.time())
        last_trained = "Unknown"
        
        if os.path.exists(MODEL_PATH):
            mtime = os.path.getmtime(MODEL_PATH)
            timestamp = int(mtime)
            last_trained = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")

        # Try to load new JSON metrics
        metrics = {}
        metrics_path = os.path.join(os.path.dirname(MODEL_PATH), 'model_metrics.json')
        if os.path.exists(metrics_path):
            try:
                import json
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
            except Exception as e:
                print(f"Error loading metrics json: {e}")

        return {
            "confusion_matrix": f"/static/ml/confusion_matrix.png?v={timestamp}",
            "feature_importance": f"/static/ml/feature_importance.png?v={timestamp}",
            "metrics": metrics, # Raw data for interactive widgets
            "model_type": "Random Forest Classifier",
            "last_trained": last_trained 
        }
