
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
    X = df[['sae_count', 'missing_pages', 'subject_count', 'review_rate', 'missing_per_subject']]
    y = df['target']

    # For hackathon demo, if we have very small data, we'll duplicate it to show training logic
    if len(df) < 10:
        df = pd.concat([df]*5, ignore_index=True)
        X = df[['sae_count', 'missing_pages', 'subject_count', 'review_rate', 'missing_per_subject']]
        y = df['target']

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
    
    return model, X_test, y_test

if __name__ == "__main__":
    train_model()
