
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import pandas as pd
import joblib
import os

def generate_visualizations(y_true, y_pred, feature_importances, output_dir='backend/ml'):
    """
    Generate and save Confusion Matrix and Feature Importance plots.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        feature_importances: List of dicts with 'feature' and 'importance' keys
        output_dir: Directory to save images
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 1. Confusion Matrix
    # Force labels 0, 1, 2 to ensure 3x3 matrix even if some classes are missing
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Low', 'Medium', 'High'], 
                yticklabels=['Low', 'Medium', 'High'])
    plt.title('Clinical Site Risk Prediction - Confusion Matrix')
    plt.ylabel('Actual Risk')
    plt.xlabel('Predicted Risk')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'confusion_matrix.png'))
    plt.close()

    # 2. Feature Importance
    if feature_importances:
        # Convert to DataFrame for easier plotting
        df_imp = pd.DataFrame(feature_importances)
        
        # Sort by importance
        df_imp = df_imp.sort_values('importance', ascending=False).head(10)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='importance', y='feature', data=df_imp, palette='viridis')
        plt.title('Key Drivers of Site Risk (Feature Importance)')
        plt.xlabel('Importance Score')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'feature_importance.png'))
        plt.close()
    
    print(f"✅ Visualizations saved to {output_dir}")
