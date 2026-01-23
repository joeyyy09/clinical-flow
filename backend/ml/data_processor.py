
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os

# Database path
# Assuming the DB is in the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = f"sqlite:///{os.path.join(BASE_DIR, 'clinical_trials.db')}"

def extract_features():
    """
    Extracts features for clinical site risk prediction from the database.
    
    Features:
    - sae_count: Total Serious Adverse Events at the site.
    - missing_pages: Total missing data pages.
    - subject_count: Total patients enrolled.
    - query_latency: Mocked/Real resolution time (days).
    - review_rate: Ratio of reviewed vs total SAEs.
    """
    engine = create_engine(DB_PATH)
    
    # Helper for cleaning
    def clean_site_col(df, col_name):
        initial_count = len(df)
        # Standardize to string
        df[col_name] = df[col_name].astype(str).str.strip()
        # Filter invalid
        invalid_values = ['', '0', 'nan', 'None', 'Unassigned', 'None']
        df = df[~df[col_name].isin(invalid_values)]
        dropped = initial_count - len(df)
        if dropped > 0:
            print(f"  ⚠️ Dropped {dropped} rows with invalid site IDs in col '{col_name}'")
        return df

    # 1. Get SAE Counts and Review Rates
    sae_df = pd.read_sql("SELECT site, review_status FROM sae_metrics", engine)
    sae_df = clean_site_col(sae_df, 'site')
    sae_counts = sae_df.groupby('site').size().reset_index(name='sae_count')
    # Use site number extraction for matching if needed, but for MVP we match directly
    sae_reviewed = sae_df[sae_df['review_status'] == 'Reviewed'].groupby('site').size().reset_index(name='reviewed_count')
    
    # 2. Get Missing Pages
    missing_df = pd.read_sql("SELECT site_number, missing_days FROM missing_pages", engine)
    missing_df = clean_site_col(missing_df, 'site_number')
    missing_counts = missing_df.groupby('site_number').size().reset_index(name='missing_pages')
    avg_missing_days = missing_df.groupby('site_number')['missing_days'].mean().reset_index(name='avg_missing_days')
    
    # 3. Get Subject Counts (EDC Metrics)
    edc_df = pd.read_sql("SELECT site_id, subject_id FROM edc_metrics", engine)
    edc_df = clean_site_col(edc_df, 'site_id')
    subject_counts = edc_df.groupby('site_id').size().reset_index(name='subject_count')
    
    # Merge all into a master feature set
    # Using 'site_id' / 'site' as key. Note: In real data, cleaning/mapping keys is critical.
    # Here we assume site names are consistent enough for the demo.
    
    # Inner join to ensure we only train on sites with overlapping data
    features = sae_counts.rename(columns={'site': 'site_id'})
    features = pd.merge(features, missing_counts.rename(columns={'site_number': 'site_id'}), on='site_id', how='outer')
    features = pd.merge(features, subject_counts, on='site_id', how='outer')
    features = pd.merge(features, sae_reviewed.rename(columns={'site': 'site_id'}), on='site_id', how='left')
    
    # Fill NaNs
    features = features.fillna(0)
    
    # Feature Engineering
    features['review_rate'] = features['reviewed_count'] / features['sae_count'].replace(0, 1)
    features['missing_per_subject'] = features['missing_pages'] / features['subject_count'].replace(0, 1)
    
    # Mocking a target for the hackathon showcase
    # In reality, this would be historical "Audit Failure" or "Delayed Submission" flags.
    # We define High Risk as sites with high missingness OR low review rates.
    # Updated Thresholds (Dynamic based on data distribution)
    # High Risk: Extreme missing data (> 30 pages/subject)
    # Medium Risk: Moderate missing data (> 10 pages/subject)
    # Low Risk: Everything else
    features['target'] = np.where(
        features['missing_per_subject'] > 30, 
        2, # High
        np.where(features['missing_per_subject'] > 10, 1, 0) # Medium, Low
    )
    
    return features

if __name__ == "__main__":
    if not os.path.exists('clinical_trials.db'):
        print("Database not found. Please run ingestion first.")
    else:
        df = extract_features()
        df.to_csv("backend/ml/processed_features.csv", index=False)
        print(f"Features extracted: {df.shape[0]} sites processed.")
        print(df.head())
