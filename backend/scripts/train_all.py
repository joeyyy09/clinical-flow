
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.ingestion_service import IngestionService
from ml.data_processor import extract_features
import joblib
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def main():
    print("🚀 Starting Batch Processing...")
    
    # 1. Run Ingestion for all studies
    IngestionService.run_full_pipeline()
    
    # 2. Extract Features
    print("📊 Extracting Features...")
    # Update DB_PATH in data_processor if needed, but it should find it in backend/
    df = extract_features()
    df.to_csv("backend/ml/processed_features.csv", index=False)
    
    # 3. Retrain Model
    print("🧠 Retraining ML Model on the full dataset...")
    X = df[['sae_count', 'missing_pages', 'subject_count', 'review_rate', 'missing_per_subject']]
    y = df['target']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    joblib.dump(model, "backend/ml/risk_model.pkl")
    print(f"✨ Model retrained on {len(df)} sites. Saved to backend/ml/risk_model.pkl")

if __name__ == "__main__":
    main()
