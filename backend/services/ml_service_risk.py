
import joblib
import os
import random
import pandas as pd
from typing import Dict, List, Any

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
    def predict_batch(data: List[Dict[str, Any]]) -> List[str]:
        """
        Batch prediction for multiple sites.
        Expects list of dicts with keys: 'missing_pages', 'sae_count', 'subject_count'
        """
        model = MLRiskService.load_model()
        if model is None:
            return ["N/A"] * len(data)

        try:
            # Convert to DataFrame to match training features and suppress warnings
            df = pd.DataFrame(data)
            
            # Ensure required columns exist
            required = ['missing_pages', 'sae_count', 'subject_count']
            for col in required:
                if col not in df.columns:
                    df[col] = 0
            
            # Feature Engineering (must match training exactly)
            df['review_rate'] = 0.8
            # Avoid division by zero
            df['missing_per_subject'] = df['missing_pages'] / df['subject_count'].replace(0, 1)
            
            # Select features in correct order
            features_list = [
                'sae_count', 
                'missing_pages', 
                'subject_count', 
                'review_rate', 
                'missing_per_subject'
            ]
            
            X = df[features_list]
            preds = model.predict(X)
            
            labels = ["Low", "Medium", "High"]
            return [labels[int(p)] for p in preds]
            
        except Exception as e:
            print(f"Batch ML Error: {e}")
            return ["Error"] * len(data)

    @staticmethod
    def predict_site_risk(missing: int, sae: int, subjects: int) -> str:
        """Wrapper for single prediction using batch logic."""
        result = MLRiskService.predict_batch([{
            'missing_pages': missing, 
            'sae_count': sae, 
            'subject_count': subjects
        }])
        return result[0]

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
