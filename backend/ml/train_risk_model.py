
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

def train_model():
    # Load processed data
    DATA_PATH = "backend/ml/processed_features.csv"
    if not os.path.exists(DATA_PATH):
        print("Processed data not found. Running extractor...")
        from data_processor import extract_features
        df = extract_features()
    else:
        df = pd.read_csv(DATA_PATH)

    # Features and Target
    # Expanded feature set for better accuracy (approx 80-90% target) avoiding leakage (e.g. calculated_dqi)
    features = [
        'total_missing_pages', 
        'subject_count', 
        'sae_review_rate', 
        'missing_per_subject',
        'deviations_per_subject',
        'queries_per_subject',
        'avg_query_latency',
        'signature_integrity',
        'coding_completion_rate',
        'missing_burden_per_subject'
    ]
    X = df[features]
    y = df['risk_label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Model definition
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    print("--- Model Evaluation ---")
    print(classification_report(y_test, y_pred))
    
    # Save model
    joblib.dump(model, 'backend/ml/risk_model.pkl')
    print("Model saved to backend/ml/risk_model.pkl")

    # Generate Visualizations (Legacy) & Save Metrics (New)
    try:
        from evaluate import generate_visualizations
        
        # Format feature importances
        feature_imp = [
            {'feature': col, 'importance': imp} 
            for col, imp in zip(X.columns, model.feature_importances_)
        ]
        
        # 1. Generate Legacy Images
        generate_visualizations(y_test, y_pred, feature_imp)

        # 2. Save Metrics JSON for Interactive Widgets
        import json
        from datetime import datetime
        
        # Calculate strict confusion matrix
        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
        
        metrics = {
            "confusion_matrix": cm.tolist(),
            "feature_importance": feature_imp,
            "accuracy": float(model.score(X_test, y_test)),
            "last_trained": datetime.now().isoformat(),
            "n_samples": len(df)
        }
        
        metrics_path = "backend/ml/model_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Metrics saved to {metrics_path}")

    except Exception as e:
        print(f"⚠️ Visualization/Metrics generation failed: {e}")
    
    return model, X_test, y_test

if __name__ == "__main__":
    train_model()
