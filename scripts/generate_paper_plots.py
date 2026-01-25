
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix
import joblib

# Add backend to path to import model
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from ml.advanced_model import AdvancedRiskModel
except ImportError:
    print("Could not import AdvancedRiskModel. Ensure you are running from project root.")
    sys.exit(1)

OUTPUT_DIR = "data/images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_plots():
    print("Loading model...")
    model = AdvancedRiskModel()
    if not model.load_model():
        print("Model not trained! Training now...")
        model.train()

    # Set style
    sns.set_theme(style="whitegrid")
    
    # 1. Feature Importance Plot
    print("Generating Feature Importance Plot...")
    if hasattr(model.model, 'named_estimators_'):
        # For VotingClassifier, get feature importance from Random Forest
        rf = model.model.named_estimators_['rf']
        importances = rf.feature_importances_
        feature_names = model.feature_names
        
        # Create DataFrame
        fi_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
        fi_df = fi_df.sort_values(by='Importance', ascending=False).head(10) # Top 10 for cleaner plot
        
        plt.figure(figsize=(8, 5)) # Landscape aspect ratio
        sns.barplot(x='Importance', y='Feature', data=fi_df, palette='viridis')
        plt.title('Top 10 High-Impact Risk Factors', fontsize=12)
        plt.xlabel('Relative Importance')
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'feature_importance.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    # 2. Confusion Matrix (Using internal Feature Engineer)
    print("Generating Confusion Matrix...")
    features_df = model.feature_engineer.extract_all_features()
    
    # Check if we have data
    if features_df.empty:
        print("No data found for confusion matrix. Skipping.")
    else:
        # Prepare data similar to train() method
        available_features = [f for f in model.feature_names if f in features_df.columns]
        X = features_df[available_features].values
        y = features_df['risk_label'].values
        
        # Scale
        X_scaled = model.scaler.transform(X)
        y_pred = model.model.predict(X_scaled)
    
        cm = confusion_matrix(y, y_pred)
        
        plt.figure(figsize=(6, 5)) 
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                    xticklabels=['Low', 'Medium', 'High'],
                    yticklabels=['Low', 'Medium', 'High'])
        plt.xlabel('Predicted Risk Level')
        plt.ylabel('Actual Risk Level')
        plt.title('Classification Accuracy (Confusion Matrix)', fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'confusion_matrix.png'), dpi=300, bbox_inches='tight')
        plt.close()

        # 3. Risk Distribution Histogram
        print("Generating Risk Distribution Histogram...")
        plt.figure(figsize=(8, 5))
        sns.histplot(y, bins=np.arange(4)-0.5, discrete=True, shrink=0.8, color='#3498db')
        plt.xticks([0, 1, 2], ['Low', 'Medium', 'High'])
        plt.title('Distribution of Site Risk Classifications', fontsize=12)
        plt.xlabel('Risk Level')
        plt.ylabel('Number of Sites')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, 'risk_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()

    print(f"All plots saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_plots()
