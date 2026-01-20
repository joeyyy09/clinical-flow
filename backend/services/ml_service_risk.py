
import joblib
import os
import random
from typing import Dict

# Model path
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'risk_model.pkl')

class MLRiskService:
    @staticmethod
    def predict_site_risk(missing: int, sae: int, subjects: int) -> str:
        """Uses the trained Random Forest model to predict site risk level."""
        if not os.path.exists(MODEL_PATH):
            return "N/A"
        
        try:
            model = joblib.load(MODEL_PATH)
            review_rate = 0.5 # Default mock
            missing_per_sub = missing / max(1, subjects)
            
            features = [[sae, missing, subjects, review_rate, missing_per_sub]]
            pred = model.predict(features)[0]
            
            return ["Low", "Medium", "High"][int(pred)]
        except Exception as e:
            print(f"ML Inference Error: {e}")
            return "Error"

    @staticmethod
    def get_ml_status() -> Dict:
        """Returns metadata about the ML model."""
        return {
            "confusion_matrix": "/static/ml/confusion_matrix.png",
            "feature_importance": "/static/ml/feature_importance.png",
            "model_type": "Random Forest Classifier",
            "last_trained": "2026-01-20" 
        }
