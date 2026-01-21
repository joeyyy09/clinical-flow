"""
ML Prediction Service for Clinical Trial Site Risk

This service provides the API layer for the advanced ML model,
offering predictions with explainability for the Risk Monitor and Reports.
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import sys

# Add ML directory to path
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml')
sys.path.insert(0, ML_DIR)

try:
    from advanced_model import AdvancedRiskModel, PredictionResult
    HAS_ADVANCED_MODEL = True
except ImportError as e:
    print(f"[WARN] Advanced model not available: {e}")
    HAS_ADVANCED_MODEL = False


class MLPredictionService:
    """
    Service layer for ML predictions with caching and fallback handling.
    
    Provides:
    - Single site predictions with explainability
    - Batch predictions for all sites
    - Model status and health checks
    - Fallback to heuristic predictions when model unavailable
    """
    
    _model_instance: Optional['AdvancedRiskModel'] = None
    _is_initialized: bool = False
    
    @classmethod
    def _get_model(cls) -> Optional['AdvancedRiskModel']:
        """Lazy load the model instance."""
        if not HAS_ADVANCED_MODEL:
            return None
            
        if cls._model_instance is None:
            try:
                cls._model_instance = AdvancedRiskModel()
                if not cls._model_instance.load_model():
                    # Model not trained yet, train it
                    print("[INFO] Training ML model for first time...")
                    cls._model_instance.train(save_model=True)
                cls._is_initialized = True
            except Exception as e:
                print(f"[ERROR] Failed to initialize ML model: {e}")
                return None
        
        return cls._model_instance
    
    @classmethod
    def predict_site_risk(cls, site_id: str) -> Dict[str, Any]:
        """
        Predict risk for a single site with full explainability.
        
        Args:
            site_id: Site identifier
            
        Returns:
            dict: Prediction result including risk level, confidence, 
                  probability distribution, and top risk factors
        """
        model = cls._get_model()
        
        if model is None:
            return cls._fallback_prediction(site_id)
        
        try:
            result = model.predict(site_id)
            return {
                "site_id": site_id,
                "risk_level": result.risk_level,
                "risk_label": result.risk_label,
                "confidence": round(result.confidence, 3),
                "probability_distribution": {
                    k: round(v, 3) for k, v in result.probability_distribution.items()
                },
                "top_risk_factors": result.top_risk_factors,
                "dqi_percentile": round(result.dqi_percentile, 1),
                "model_version": result.model_version,
                "prediction_source": "advanced_ml"
            }
        except Exception as e:
            print(f"[ERROR] Prediction failed for {site_id}: {e}")
            return cls._fallback_prediction(site_id)
    
    @classmethod
    def predict_batch(cls, site_ids: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Predict risk for multiple sites.
        
        Args:
            site_ids: List of site IDs, or None for all sites
            
        Returns:
            dict: Mapping of site_id to prediction results
        """
        model = cls._get_model()
        
        if model is None:
            return {}
        
        try:
            results = model.predict_batch(site_ids)
            return {
                site_id: {
                    "site_id": site_id,
                    "risk_level": result.risk_level,
                    "confidence": round(result.confidence, 3),
                    "probability_distribution": {
                        k: round(v, 3) for k, v in result.probability_distribution.items()
                    },
                    "top_risk_factors": result.top_risk_factors[:3],  # Top 3 for batch
                    "model_version": result.model_version
                }
                for site_id, result in results.items()
            }
        except Exception as e:
            print(f"[ERROR] Batch prediction failed: {e}")
            return {}
    
    @classmethod
    def get_model_status(cls) -> Dict[str, Any]:
        """
        Get current model status and metadata.
        
        Returns:
            dict: Model status including version, features, and health
        """
        model = cls._get_model()
        
        if model is None:
            return {
                "status": "unavailable",
                "message": "Advanced model not loaded",
                "fallback_active": True,
                "model_type": "Heuristic Fallback"
            }
        
        info = model.get_model_info()
        return {
            "status": "operational" if info["is_trained"] else "not_trained",
            "version": info["version"],
            "architecture": info["architecture"],
            "n_features": info["n_features"],
            "has_explainability": info["has_shap"],
            "fallback_active": False,
            "model_path": info["model_path"]
        }
    
    @classmethod
    def retrain_model(cls) -> Dict[str, Any]:
        """
        Force retrain the model with latest data.
        
        Returns:
            dict: Training results
        """
        if not HAS_ADVANCED_MODEL:
            return {"error": "Advanced model not available"}
        
        try:
            model = AdvancedRiskModel()
            results = model.train(save_model=True)
            
            # Reset cached instance to use new model
            cls._model_instance = model
            cls._is_initialized = True
            
            return {
                "status": "success",
                "accuracy": results.get("accuracy", 0),
                "n_features": results.get("n_features", 0),
                "n_samples": results.get("n_samples", 0),
                "model_version": results.get("model_version", "unknown")
            }
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    def _fallback_prediction(cls, site_id: str) -> Dict[str, Any]:
        """Heuristic fallback when ML model is unavailable."""
        
        # Import the legacy service for fallback
        try:
            from services.ml_service_risk import MLRiskService
            risk_level = MLRiskService.predict_site_risk(0, 0, 1)  # Default values
        except:
            risk_level = "Medium"
        
        return {
            "site_id": site_id,
            "risk_level": risk_level,
            "risk_label": {"Low": 0, "Medium": 1, "High": 2}.get(risk_level, 1),
            "confidence": 0.5,
            "probability_distribution": {"Low": 0.33, "Medium": 0.34, "High": 0.33},
            "top_risk_factors": [
                {
                    "feature": "model_unavailable",
                    "impact": 0,
                    "direction": "neutral",
                    "explanation": "Using heuristic fallback - ML model not available"
                }
            ],
            "dqi_percentile": 50.0,
            "model_version": "fallback",
            "prediction_source": "heuristic_fallback"
        }
    
    @classmethod
    def get_feature_importance(cls) -> List[Dict[str, Any]]:
        """
        Get global feature importance rankings.
        
        Returns:
            list: Features ranked by importance
        """
        model = cls._get_model()
        
        if model is None or not model.is_trained:
            return []
        
        try:
            # Get feature importance from Random Forest component
            rf_model = model.model.named_estimators_['rf']
            importances = rf_model.feature_importances_
            
            feature_importance = [
                {
                    "feature": name,
                    "importance": float(imp),
                    "rank": i + 1
                }
                for i, (name, imp) in enumerate(
                    sorted(
                        zip(model.feature_names, importances),
                        key=lambda x: x[1],
                        reverse=True
                    )
                )
            ]
            
            return feature_importance[:15]  # Top 15
            
        except Exception as e:
            print(f"[ERROR] Failed to get feature importance: {e}")
            return []


# Convenience functions for backward compatibility
def predict_site_risk(missing: int, sae: int, subjects: int) -> str:
    """Legacy compatibility wrapper."""
    # This is called by the old service - return basic prediction
    try:
        from services.ml_service_risk import MLRiskService
        return MLRiskService.predict_site_risk(missing, sae, subjects)
    except:
        return "Medium"
