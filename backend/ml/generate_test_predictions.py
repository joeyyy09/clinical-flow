import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import os
import sys

# Ensure backend modules can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.advanced_model import AdvancedRiskModel

def generate_test_predictions():
    print("--- Starting Prediction Process (Advanced Model) ---")
    
    # 1. Initialize Model
    model = AdvancedRiskModel()
    if not model.load_model():
        print("❌ Error: Could not load advanced model. Please train it first.")
        return

    # 2. Load Evaluation Data
    # We need to reconstruct the test set used during training for valid comparison
    # Ideally, we would have saved the test indices, but for now we reproduce the split
    print("reconstructing test set...")
    
    # Extract features using the same engineer
    features_df = model.feature_engineer.extract_all_features()
    
    if features_df.empty:
        print("❌ no features found")
        return

    # Filter features to match trained model (Cleaned of Leakage)
    training_features = model.feature_names
    X = features_df[training_features].values
    y = features_df['risk_label'].values
    
    # Stratified Split (same random state as training)
    from sklearn.model_selection import train_test_split
    _, X_test, _, y_test_true = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Generate Predictions on Scaled Data
    print("Generating predictions on Test set...")
    # Note: AdvancedRiskModel usually handles scaling internally in .predict(), 
    # but since we are bypassing .predict() to do batch evaluation on X_test numpy array,
    # we need to use the scaler manually.
    X_test_scaled = model.scaler.transform(X_test)
    y_pred = model.model.predict(X_test_scaled)
    y_proba = model.model.predict_proba(X_test_scaled)
    
    # 4. Calculate Metrics
    accuracy = accuracy_score(y_test_true, y_pred)
    print(f"\n--- Evaluation Metrics ---")
    print(f"Accuracy: {accuracy:.4f}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test_true, y_pred)
    print(cm)
    
    print("\nClassification Report:")
    print(classification_report(y_test_true, y_pred))
    
    # 5. Save Detailed Results
    results = []
    # We need to map back to site_ids, which is tricky with just numpy arrays.
    # For this report, we will just save the aggregate metrics and raw predictions.
    
    # For a proper site-level CSV, we'd need the indices. 
    # Let's simple create a dataframe of predictions
    pred_df = pd.DataFrame(y_proba, columns=['Prob_Low', 'Prob_Medium', 'Prob_High'])
    pred_df['Predicted_Label'] = y_pred
    pred_df['True_Label'] = y_test_true
    pred_df['Is_Correct'] = pred_df['Predicted_Label'] == pred_df['True_Label']
    
    output_path = "backend/ml/test_set_predictions.csv"
    pred_df.to_csv(output_path, index=False)
    print(f"\n✅ Predictions saved to {output_path}")

if __name__ == "__main__":
    generate_test_predictions()
