
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pandas as pd
import joblib
import os

def generate_visualizations():
    # Load model and test results (simulated for visualization)
    model_path = 'backend/ml/risk_model.pkl'
    if not os.path.exists(model_path):
        print("Model not found. Run training first.")
        return

    # Mocking evaluation data for visualization demo
    y_true = [0, 1, 2, 0, 1, 2, 0, 1, 2, 1, 1, 0, 2, 2, 1]
    y_pred = [0, 1, 2, 0, 2, 2, 0, 1, 1, 1, 1, 0, 2, 2, 1]
    
    cm = confusion_matrix(y_true, y_pred)
    
    # 1. Confusion Matrix
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Low', 'Medium', 'High'], 
                yticklabels=['Low', 'Medium', 'High'])
    plt.title('Clinical Site Risk Prediction - Confusion Matrix')
    plt.ylabel('Actual Risk')
    plt.xlabel('Predicted Risk')
    plt.savefig('backend/ml/confusion_matrix.png')
    plt.close()

    # 2. Feature Importance
    model = joblib.load(model_path)
    features = ['SAEs', 'Missing Pages', 'Enrolled Subjects', 'SAE Review Rate', 'Data Missingness']
    importance = model.feature_importances_
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=importance, y=features, palette='viridis')
    plt.title('Key Drivers of Site Risk (Feature Importance)')
    plt.xlabel('Impact Score')
    plt.tight_layout()
    plt.savefig('backend/ml/feature_importance.png')
    plt.close()
    
    print("Visualizations saved to backend/ml/")

if __name__ == "__main__":
    generate_visualizations()
