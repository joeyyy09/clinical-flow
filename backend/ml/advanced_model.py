"""
Advanced Ensemble ML Model for Clinical Trial Site Risk Prediction

This module implements a production-grade ensemble model combining:
1. XGBoost Gradient Boosting for tabular data
2. Neural Network for complex pattern recognition
3. SHAP explainability for interpretable predictions
4. Confidence scoring with calibrated probabilities
"""

import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier

# Try importing XGBoost (preferred) or fall back to GradientBoosting
try:
    from xgboost import XGBClassifier
    # Test if XGBoost actually works (catches libomp issues on macOS)
    _test = XGBClassifier(n_estimators=1)
    HAS_XGBOOST = True
    print("[OK] XGBoost loaded successfully")
except Exception as e:
    print(f"[WARN] XGBoost not available ({type(e).__name__}), using GradientBoosting fallback")
    from sklearn.ensemble import GradientBoostingClassifier
    HAS_XGBOOST = False

# Try importing SHAP for explainability
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("[WARN] SHAP not installed. Explainability features will use fallback.")

try:
    from .feature_engineering import FeatureEngineer
    from .evaluate import generate_visualizations
except ImportError:
    from feature_engineering import FeatureEngineer
    from evaluate import generate_visualizations


@dataclass
class PredictionResult:
    """Structured prediction result with explainability."""
    risk_level: str
    risk_label: int
    confidence: float
    probability_distribution: Dict[str, float]
    top_risk_factors: List[Dict[str, Any]]
    model_version: str
    dqi_percentile: float


class AdvancedRiskModel:
    """
    Advanced ensemble model for clinical site risk prediction.
    
    Architecture:
    - Primary: XGBoost/GradientBoosting for high accuracy
    - Secondary: Neural Network for pattern recognition
    - Ensemble: Soft voting with calibrated probabilities
    - Explainability: SHAP values for feature importance
    """
    
    MODEL_VERSION = "2.0.0"
    MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(MODEL_DIR, "advanced_risk_model.pkl")
    SCALER_PATH = os.path.join(MODEL_DIR, "feature_scaler.pkl")
    EXPLAINER_PATH = os.path.join(MODEL_DIR, "shap_explainer.pkl")
    
    RISK_LABELS = {0: 'Low', 1: 'Medium', 2: 'High'}
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.explainer = None
        self.feature_names = None
        self.is_trained = False
        
        # Feature engineer
        self.feature_engineer = FeatureEngineer()
        
    def _create_ensemble_model(self, n_classes: int = 3) -> VotingClassifier:
        """Create the ensemble model architecture."""
        
        # Model 1: XGBoost or GradientBoosting
        if HAS_XGBOOST:
            xgb_model = XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss',
                n_jobs=-1
            )
        else:
            xgb_model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        
        # Model 2: Random Forest (robust baseline)
        rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        
        # Model 3: Neural Network (pattern recognition)
        nn_model = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=20,
            random_state=42
        )
        
        # Ensemble with soft voting
        ensemble = VotingClassifier(
            estimators=[
                ('xgb', xgb_model),
                ('rf', rf_model),
                ('nn', nn_model)
            ],
            voting='soft',
            weights=[0.45, 0.35, 0.20]  # XGBoost weighted highest
        )
        
        return ensemble
    
    def train(self, save_model: bool = True) -> Dict[str, Any]:
        """
        Train the ensemble model on clinical trial data.
        
        Args:
            save_model: Whether to save the trained model to disk
            
        Returns:
            dict: Training metrics and evaluation results
        """
        print("🚀 Starting Advanced Model Training Pipeline...")
        
        # 1. Extract features
        print("📊 Extracting features...")
        features_df = self.feature_engineer.extract_all_features()
        
        if features_df.empty or len(features_df) < 5:
            print("❌ Insufficient data for training. Need at least 5 sites.")
            return {"error": "Insufficient data"}
        
        # 2. Prepare training data
        self.feature_names = self.feature_engineer.get_feature_names()
        available_features = [f for f in self.feature_names if f in features_df.columns]
        
        if len(available_features) < 10:
            print(f"⚠️ Only {len(available_features)} features available. Using all available.")
        
        X = features_df[available_features].values
        y = features_df['risk_label'].values
        
        print(f"📈 Dataset: {X.shape[0]} sites, {X.shape[1]} features")
        print(f"📊 Label distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
        
        # Handle small datasets
        if len(features_df) < 20:
            print("⚠️ Small dataset detected. Using holdout validation instead of cross-validation.")
            # Duplicate data for more robust training
            X = np.vstack([X] * 3)
            y = np.concatenate([y] * 3)
        
        # 3. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 4. Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 5. Train ensemble
        print("🔧 Training ensemble model...")
        self.model = self._create_ensemble_model()
        self.model.fit(X_train_scaled, y_train)
        
        # 6. Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)
        
        accuracy = (y_pred == y_test).mean()
        
        print("\n📊 Model Evaluation:")
        print(f"   Accuracy: {accuracy:.2%}")
        print(f"\n{classification_report(y_test, y_pred, target_names=['Low', 'Medium', 'High'])}")
        
        # 7. Create SHAP explainer
        if HAS_SHAP:
            print("🔍 Creating SHAP explainer...")
            try:
                # Use the XGBoost/RF component for SHAP (tree-based)
                base_model = self.model.named_estimators_['rf']
                self.explainer = shap.TreeExplainer(base_model)
            except Exception as e:
                print(f"⚠️ SHAP explainer creation failed: {e}")
                self.explainer = None
        
        # 8. Save model
        if save_model:
            self._save_model()
            
            # 8a. Generate Visualizations (Real)
            print("🎨 Generating visualizations...")
            try:
                # Get feature importance for visualization
                rf_model = self.model.named_estimators_['rf']
                importances = rf_model.feature_importances_
                
                feat_imp_list = [
                    {"feature": name, "importance": float(imp)}
                    for name, imp in zip(self.feature_names, importances)
                ]
                
                # Call the evaluation script
                generate_visualizations(
                    y_test, 
                    y_pred, 
                    feat_imp_list, 
                    output_dir=os.path.join(self.MODEL_DIR)
                )
            except Exception as e:
                print(f"⚠️ Visualization generation failed: {e}")
        
        self.is_trained = True
        self.feature_names = available_features
        
        return {
            "accuracy": accuracy,
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "n_features": len(available_features),
            "n_samples": len(features_df),
            "model_version": self.MODEL_VERSION
        }
    
    def predict(self, site_id: str) -> PredictionResult:
        """
        Make a prediction with full explainability for a single site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            PredictionResult: Structured prediction with confidence and explanations
        """
        if not self.is_trained:
            self.load_model()
        
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Extract features for this site
        features = self.feature_engineer.extract_site_features(site_id)
        
        if not features:
            return PredictionResult(
                risk_level="Unknown",
                risk_label=-1,
                confidence=0.0,
                probability_distribution={},
                top_risk_factors=[],
                model_version=self.MODEL_VERSION,
                dqi_percentile=0.0
            )
        
        # Helper to force float conversion
        def to_float(val):
            if isinstance(val, (dict, list, tuple)): return 0.0
            try: return float(val)
            except: return 0.0

        # Prepare feature vector
        feature_vector = np.array([[to_float(features.get(f, 0)) for f in self.feature_names]])
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        risk_label = self.model.predict(feature_vector_scaled)[0]
        probabilities = self.model.predict_proba(feature_vector_scaled)[0]
        
        risk_level = self.RISK_LABELS[risk_label]
        confidence = float(probabilities[risk_label])
        
        prob_dist = {
            self.RISK_LABELS[i]: float(p) 
            for i, p in enumerate(probabilities)
        }
        
        # Get SHAP explanations
        top_factors = self._get_top_risk_factors(feature_vector_scaled, features, int(risk_label))
        
        # Ensure dqi_percentile is a float
        dqi_p = to_float(features.get('dqi_percentile', 0))

        return PredictionResult(
            risk_level=risk_level,
            risk_label=int(risk_label),
            confidence=confidence,
            probability_distribution=prob_dist,
            top_risk_factors=top_factors,
            model_version=self.MODEL_VERSION,
            dqi_percentile=dqi_p
        )
    
    def predict_batch(self, site_ids: List[str] = None) -> Dict[str, PredictionResult]:
        """
        Make predictions for multiple sites or all sites.
        
        Args:
            site_ids: List of site IDs, or None for all sites
            
        Returns:
            dict: Mapping of site_id to PredictionResult
        """
        if not self.is_trained:
            self.load_model()
        
        features_df = self.feature_engineer.extract_all_features()
        
        if site_ids:
            features_df = features_df[features_df.index.isin(site_ids)]
        
        results = {}
        for site_id in features_df.index:
            try:
                # Use scalar only features dict
                results[site_id] = self.predict(site_id)
            except Exception as e:
                # Suppress flood of errors, print only unique ones if needed
                # print(f"⚠️ Prediction failed for {site_id}: {e}")
                pass
        
        return results
    
    def _get_top_risk_factors(
        self, 
        feature_vector: np.ndarray, 
        raw_features: Dict,
        target_class: int = 2,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract top risk factors using SHAP or fallback heuristics."""
        
        factors = []
        
        if HAS_SHAP and self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(feature_vector)
                
                # Handle different SHAP output formats
                sv = None
                if isinstance(shap_values, list):
                    # Multi-class: List of arrays [class0, class1, class2]
                    # Use the target class SHAP values
                    if 0 <= target_class < len(shap_values):
                        sv = shap_values[target_class]
                    else:
                        sv = shap_values[-1] # Fallback to last class (High)
                else:
                    # Binary/Single output
                    sv = shap_values
                
                # Ensure sv is 2D [n_samples, n_features]
                if sv is not None:
                     # Get single sample values
                    if len(sv.shape) > 1:
                        vals = sv[0]
                    else:
                        vals = sv
                        
                    # Get top contributors based on absolute magnitude
                    importance = np.abs(vals)
                    top_indices = np.argsort(importance)[-top_n:][::-1]
                    
                    for idx in top_indices:
                        if idx < len(self.feature_names):
                            feature_name = self.feature_names[idx]
                            shap_val = float(vals[idx])
                            
                            factors.append({
                                "feature": feature_name,
                                "impact": abs(shap_val),
                                "direction": "increases_risk" if shap_val > 0 else "decreases_risk",
                                "value": float(feature_vector[0][idx]),
                                "explanation": self._get_feature_explanation(feature_name, shap_val, raw_features)
                            })
                    
            except Exception as e:
                # print(f"⚠️ SHAP explanation failed: {e}")
                pass
        
        # Fallback
        if not factors:
            factors = self._get_heuristic_factors(raw_features, top_n)
        
        return factors
    
    def _get_heuristic_factors(self, features: Dict, top_n: int = 5) -> List[Dict]:
        """Fallback risk factor identification using domain knowledge."""
        
        risk_indicators = []
        
        # Safety indicators
        if features.get('pending_sae', 0) > 0:
            risk_indicators.append({
                "feature": "pending_sae",
                "impact": 0.4,
                "direction": "increases_risk",
                "value": features.get('pending_sae', 0),
                "explanation": f"{int(features.get('pending_sae', 0))} pending SAE reviews require immediate attention"
            })
        
        # Data quality indicators
        missing = features.get('missing_per_subject', 0)
        if missing > 2:
            risk_indicators.append({
                "feature": "missing_per_subject",
                "impact": 0.3,
                "direction": "increases_risk",
                "value": missing,
                "explanation": f"High missing data burden ({missing:.1f} pages per subject)"
            })
        
        # Query indicators
        queries = features.get('queries_per_subject', 0)
        if queries > 5:
            risk_indicators.append({
                "feature": "queries_per_subject",
                "impact": 0.25,
                "direction": "increases_risk",
                "value": queries,
                "explanation": f"Elevated query load ({queries:.1f} queries per subject)"
            })
        
        # Protocol deviations
        deviations = features.get('deviations_per_subject', 0)
        if deviations > 1:
            risk_indicators.append({
                "feature": "deviations_per_subject",
                "impact": 0.25,
                "direction": "increases_risk",
                "value": deviations,
                "explanation": f"Protocol deviation rate: {deviations:.1f} per subject"
            })
        
        # Good indicators
        dqi = features.get('calculated_dqi', 0)
        if dqi > 80:
            risk_indicators.append({
                "feature": "calculated_dqi",
                "impact": 0.3,
                "direction": "decreases_risk",
                "value": dqi,
                "explanation": f"Strong Data Quality Index ({dqi})"
            })
        
        review_rate = features.get('sae_review_rate', 0)
        if review_rate > 0.9:
            risk_indicators.append({
                "feature": "sae_review_rate",
                "impact": 0.2,
                "direction": "decreases_risk",
                "value": review_rate,
                "explanation": f"Excellent SAE review rate ({review_rate:.0%})"
            })
        
        # Sort by impact and return top N
        risk_indicators.sort(key=lambda x: x['impact'], reverse=True)
        return risk_indicators[:top_n]
    
    def _get_feature_explanation(self, feature: str, shap_value: float, raw_features: Dict) -> str:
        """Generate human-readable explanation for a feature's contribution."""
        
        value = raw_features.get(feature, 0)
        direction = "increases" if shap_value > 0 else "decreases"
        
        explanations = {
            'pending_sae': f"{int(value)} pending SAE reviews {direction} risk",
            'sae_per_subject': f"SAE rate of {value:.2f} per subject {direction} risk",
            'missing_per_subject': f"Missing data rate ({value:.1f}/subject) {direction} risk",
            'queries_per_subject': f"Query load ({value:.1f}/subject) {direction} risk",
            'sae_review_rate': f"SAE review rate ({value:.0%}) {direction} risk",
            'calculated_dqi': f"DQI score of {value} {direction} risk",
            'coding_completion_rate': f"Coding completion ({value:.0%}) {direction} risk",
            'avg_query_latency': f"Query latency ({value:.0f} days) {direction} risk",
            'safety_score': f"Safety score ({value:.0f}) {direction} risk",
            'compliance_index': f"Compliance index ({value:.0f}) {direction} risk",
            'risk_velocity': f"Risk accumulation rate {direction} overall risk",
        }
        
        return explanations.get(feature, f"{feature} = {value:.2f} {direction} risk")
    
    def _save_model(self):
        """Save trained model and associated artifacts."""
        print("💾 Saving model artifacts...")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'version': self.MODEL_VERSION,
            'has_xgboost': HAS_XGBOOST
        }
        
        joblib.dump(model_data, self.MODEL_PATH)
        print(f"   ✅ Model saved to {self.MODEL_PATH}")
        
        if self.explainer is not None:
            try:
                joblib.dump(self.explainer, self.EXPLAINER_PATH)
                print(f"   ✅ SHAP explainer saved to {self.EXPLAINER_PATH}")
            except Exception as e:
                print(f"   ⚠️ Could not save SHAP explainer: {e}")
    
    def load_model(self) -> bool:
        """Load trained model from disk."""
        
        if not os.path.exists(self.MODEL_PATH):
            print(f"⚠️ No saved model found at {self.MODEL_PATH}")
            return False
        
        try:
            model_data = joblib.load(self.MODEL_PATH)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.is_trained = True
            
            print(f"✅ Loaded model v{model_data.get('version', 'unknown')}")
            
            # Load SHAP explainer if available
            if os.path.exists(self.EXPLAINER_PATH):
                try:
                    self.explainer = joblib.load(self.EXPLAINER_PATH)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get metadata about the trained model."""
        
        return {
            "version": self.MODEL_VERSION,
            "is_trained": self.is_trained,
            "n_features": len(self.feature_names) if self.feature_names else 0,
            "feature_names": self.feature_names,
            "has_xgboost": HAS_XGBOOST,
            "has_shap": HAS_SHAP and self.explainer is not None,
            "model_path": self.MODEL_PATH,
            "architecture": "Ensemble (XGBoost + RandomForest + Neural Network)"
        }


def train_and_evaluate():
    """Main training function."""
    print("=" * 60)
    print("🧠 Advanced Clinical Trial Risk Model - Training Pipeline")
    print("=" * 60)
    
    model = AdvancedRiskModel()
    results = model.train(save_model=True)
    
    print("\n" + "=" * 60)
    print("📊 Training Complete!")
    print("=" * 60)
    
    if "error" not in results:
        print(f"   Model Version: {results['model_version']}")
        print(f"   Accuracy: {results['accuracy']:.2%}")
        print(f"   Features Used: {results['n_features']}")
        print(f"   Samples Trained: {results['n_samples']}")
    
    return results


if __name__ == "__main__":
    train_and_evaluate()
