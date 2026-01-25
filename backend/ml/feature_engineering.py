"""
Advanced Feature Engineering Pipeline for Clinical Trial Risk Prediction

This module provides comprehensive feature engineering for site risk prediction,
including temporal features, composite indicators, and cross-metric interactions.
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import os

# Database path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = f"sqlite:///{os.path.join(BASE_DIR, 'clinical_trials.db')}"


class FeatureEngineer:
    """
    Advanced feature engineering for clinical trial site risk prediction.
    
    Generates 35+ features across multiple categories:
    - Base Metrics (15): Normalized counts and rates
    - Ratio Features (8): Cross-metric relationships
    - Temporal Features (6): Trends and velocity
    - Composite Features (4): Weighted risk indicators
    - Categorical Features (3): Encoded categories
    """
    
    # Feature importance weights based on clinical domain knowledge
    FEATURE_WEIGHTS = {
        'safety': 0.40,
        'data_quality': 0.25,
        'queries': 0.25,
        'coding': 0.10
    }
    
    def __init__(self, db_path: str = DB_PATH):
        self.engine = create_engine(db_path)
        
    def extract_all_features(self) -> pd.DataFrame:
        """
        Extracts comprehensive feature set for all sites.
        
        Returns:
            pd.DataFrame: Feature matrix with site_id index and 35+ columns
        """
        # Base aggregations
        base_df = self._extract_base_metrics()
        
        if base_df.empty:
            return pd.DataFrame()
        
        # Add derived features
        base_df = self._add_ratio_features(base_df)
        base_df = self._add_composite_features(base_df)
        base_df = self._add_categorical_features(base_df)
        base_df = self._add_risk_trajectory_features(base_df)
        
        # Generate target labels
        base_df = self._generate_risk_labels(base_df)
        
        # Fill any remaining NaNs
        base_df = base_df.fillna(0)
        
        return base_df
    
    def extract_site_features(self, site_id: str) -> Dict:
        """
        Extract features for a single site for real-time prediction.
        
        Args:
            site_id: Site identifier (supports formats: "Site 123", "123", "Site123")
            
        Returns:
            dict: Feature dictionary for the site
        """
        all_features = self.extract_all_features()
        
        if all_features.empty:
            return {}
        
        # Direct match
        if site_id in all_features.index:
            return all_features.loc[site_id].to_dict()
        
        # Extract numeric part from site_id (e.g., "Site 1042" -> "1042")
        import re
        numeric_match = re.search(r'\d+', str(site_id))
        numeric_id = numeric_match.group() if numeric_match else site_id
        
        # Try various key formats
        keys_to_try = [
            site_id,
            numeric_id,
            str(int(numeric_id)) if numeric_id.isdigit() else numeric_id,  # Remove leading zeros
            f"Site {numeric_id}",
            numeric_id.lstrip('0'),  # "01" -> "1"
        ]
        
        for key in keys_to_try:
            if key in all_features.index:
                return all_features.loc[key].to_dict()
        
        # Partial match - check if any index contains the numeric ID
        for idx in all_features.index:
            idx_numeric = re.search(r'\d+', str(idx))
            if idx_numeric and idx_numeric.group() == numeric_id:
                return all_features.loc[idx].to_dict()
        
        return {}
    
    def _extract_base_metrics(self) -> pd.DataFrame:
        """Extract base metrics from all data sources."""
        
        with self.engine.connect() as conn:
            # 1. EDC Metrics - Primary source
            edc_query = """
            SELECT 
                site_id,
                study_id,
                country,
                COUNT(DISTINCT subject_id) as subject_count,
                SUM(missing_pages) as total_missing_pages,
                SUM(missing_visits) as total_missing_visits,
                SUM(total_queries) as total_queries,
                SUM(dm_queries) as dm_queries,
                SUM(clinical_queries) as clinical_queries,
                SUM(medical_queries) as medical_queries,
                SUM(safety_queries) as safety_queries,
                SUM(coding_queries) as coding_queries,
                SUM(protocol_deviations) as total_deviations,
                SUM(esae_review_dm + esae_review_safety) as total_sae_reviews,
                SUM(open_issues_edrr) as total_edrr_issues,
                SUM(uncoded_terms) as total_uncoded,
                SUM(coded_terms) as total_coded,
                SUM(query_latency) as sum_query_latency,
                SUM(inactivated_forms) as total_inactivated,
                SUM(crfs_verified) as total_verified,
                SUM(crfs_locked) as total_locked,
                SUM(crfs_signed) as total_signed,
                SUM(broken_signatures) as total_broken_sigs,
                AVG(clean_entered_crf_pct) as avg_clean_crf_pct
            FROM edc_metrics
            GROUP BY site_id, study_id, country
            """
            edc_df = pd.read_sql(edc_query, conn)
            
            if edc_df.empty:
                return pd.DataFrame()
            
            # 2. SAE Metrics
            sae_query = """
            SELECT 
                site,
                COUNT(*) as sae_count,
                SUM(CASE WHEN review_status != 'Completed' THEN 1 ELSE 0 END) as pending_sae,
                SUM(CASE WHEN review_status = 'Completed' THEN 1 ELSE 0 END) as reviewed_sae
            FROM sae_metrics
            GROUP BY site
            """
            sae_df = pd.read_sql(sae_query, conn)
            sae_map = {row['site']: row for _, row in sae_df.iterrows()}
            
            # 3. Missing Pages (Global)
            missing_query = """
            SELECT 
                site_number,
                COUNT(*) as global_missing_pages,
                AVG(missing_days) as avg_missing_days,
                MAX(missing_days) as max_missing_days
            FROM missing_pages
            GROUP BY site_number
            """
            missing_df = pd.read_sql(missing_query, conn)
            missing_map = {row['site_number']: row for _, row in missing_df.iterrows()}
            
            # 4. MedDRA Coding Status
            meddra_query = """
            SELECT 
                e.site_id,
                COUNT(CASE WHEN m.coding_status LIKE '%uncoded%' THEN 1 END) as meddra_uncoded,
                COUNT(*) as meddra_total
            FROM edc_metrics e
            LEFT JOIN meddra_coding m ON e.subject_id = m.subject
            GROUP BY e.site_id
            """
            meddra_df = pd.read_sql(meddra_query, conn)
            meddra_map = {row['site_id']: row for _, row in meddra_df.iterrows()}
            
            # 5. WHO Drug Coding Status
            who_query = """
            SELECT 
                e.site_id,
                COUNT(CASE WHEN w.coding_status LIKE '%uncoded%' THEN 1 END) as who_uncoded,
                COUNT(*) as who_total
            FROM edc_metrics e
            LEFT JOIN whodrug_coding w ON e.subject_id = w.subject
            GROUP BY e.site_id
            """
            who_df = pd.read_sql(who_query, conn)
            who_map = {row['site_id']: row for _, row in who_df.iterrows()}
        
        # Merge all data sources
        results = []
        for _, row in edc_df.iterrows():
            site_id = row['site_id']
            subject_count = max(1, row['subject_count'] or 1)
            
            # Lookup keys
            keys = [site_id, f"Site {site_id}", str(site_id).lstrip('0')]
            if str(site_id).isdigit():
                keys.append(str(int(site_id)))
            
            # Find SAE data
            sae_data = {'sae_count': 0, 'pending_sae': 0, 'reviewed_sae': 0}
            for k in keys:
                if k in sae_map:
                    sae_data = sae_map[k]
                    break
            
            # Find Missing Pages data
            missing_data = {'global_missing_pages': 0, 'avg_missing_days': 0, 'max_missing_days': 0}
            for k in keys:
                if k in missing_map:
                    missing_data = missing_map[k]
                    break
            
            # Get coding data
            meddra_data = meddra_map.get(site_id, {'meddra_uncoded': 0, 'meddra_total': 0})
            who_data = who_map.get(site_id, {'who_uncoded': 0, 'who_total': 0})
            
            # Helper to safely extract scalar
            def get_val(source, key):
                val = source.get(key, 0)
                if isinstance(val, (dict, list, tuple)):
                    return 0
                try:
                    return float(val)
                except:
                    return 0

            feature_row = {
                'site_id': site_id,
                'study_id': row['study_id'],
                'country': row['country'],
                
                # Base counts
                'subject_count': subject_count,
                'total_missing_pages': get_val(row, 'total_missing_pages'),
                'total_missing_visits': get_val(row, 'total_missing_visits'),
                'total_queries': get_val(row, 'total_queries'),
                'total_deviations': get_val(row, 'total_deviations'),
                'total_sae_reviews': get_val(row, 'total_sae_reviews'),
                'total_edrr_issues': get_val(row, 'total_edrr_issues'),
                'total_inactivated': get_val(row, 'total_inactivated'),
                
                # Query breakdown
                'dm_queries': get_val(row, 'dm_queries'),
                'clinical_queries': get_val(row, 'clinical_queries'),
                'medical_queries': get_val(row, 'medical_queries'),
                'safety_queries': get_val(row, 'safety_queries'),
                'coding_queries': get_val(row, 'coding_queries'),
                
                # Verification metrics
                'total_verified': get_val(row, 'total_verified'),
                'total_locked': get_val(row, 'total_locked'),
                'total_signed': get_val(row, 'total_signed'),
                'total_broken_sigs': get_val(row, 'total_broken_sigs'),
                'avg_clean_crf_pct': get_val(row, 'avg_clean_crf_pct'),
                
                # Coding metrics
                'total_coded': get_val(row, 'total_coded'),
                'total_uncoded': get_val(row, 'total_uncoded'),
                'meddra_uncoded': get_val(meddra_data, 'meddra_uncoded'),
                'who_uncoded': get_val(who_data, 'who_uncoded'),
                
                # SAE metrics
                'sae_count': get_val(sae_data, 'sae_count'),
                'pending_sae': get_val(sae_data, 'pending_sae'),
                'reviewed_sae': get_val(sae_data, 'reviewed_sae'),
                
                # Global missing pages
                'global_missing_pages': get_val(missing_data, 'global_missing_pages'),
                'avg_missing_days': get_val(missing_data, 'avg_missing_days'),
                'max_missing_days': get_val(missing_data, 'max_missing_days'),
                
                # Query latency
                'sum_query_latency': get_val(row, 'sum_query_latency'),
            }
            
            results.append(feature_row)
        
        df = pd.DataFrame(results)
        df = df.set_index('site_id')
        return df
    
    def _add_ratio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ratio-based features for cross-metric relationships."""
        
        subject_count = df['subject_count'].replace(0, 1)
        
        # Per-subject normalized metrics
        df['missing_per_subject'] = df['total_missing_pages'] / subject_count
        df['queries_per_subject'] = df['total_queries'] / subject_count
        df['sae_per_subject'] = df['sae_count'] / subject_count
        df['deviations_per_subject'] = df['total_deviations'] / subject_count
        df['edrr_per_subject'] = df['total_edrr_issues'] / subject_count
        
        # Resolution/completion rates
        total_sae = df['sae_count'].replace(0, 1)
        df['sae_review_rate'] = df['reviewed_sae'] / total_sae
        
        total_coded_terms = (df['total_coded'] + df['total_uncoded']).replace(0, 1)
        df['coding_completion_rate'] = df['total_coded'] / total_coded_terms
        
        # Query latency average
        df['avg_query_latency'] = df['sum_query_latency'] / subject_count
        
        # Safety query ratio (safety queries / total queries)
        total_queries = df['total_queries'].replace(0, 1)
        df['safety_query_ratio'] = df['safety_queries'] / total_queries
        df['dm_query_ratio'] = df['dm_queries'] / total_queries
        
        # Data completeness indicators
        df['missing_data_burden'] = df['total_missing_pages'] + df['total_missing_visits']
        df['missing_burden_per_subject'] = df['missing_data_burden'] / subject_count
        
        # Signature integrity
        total_signed = df['total_signed'].replace(0, 1)
        df['signature_integrity'] = 1 - (df['total_broken_sigs'] / total_signed)
        df['signature_integrity'] = df['signature_integrity'].clip(0, 1)
        
        return df
    
    def _add_composite_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add weighted composite risk indicators."""
        
        subject_count = df['subject_count'].replace(0, 1)
        
        # Safety Score Component (0-100, higher is better)
        sae_rate = df['pending_sae'] / subject_count
        df['safety_score'] = (100 - (sae_rate * 100)).clip(0, 100)
        
        # Data Quality Score Component
        missing_rate = df['missing_burden_per_subject']
        df['data_quality_score'] = (100 - (missing_rate * 20)).clip(0, 100)
        
        # Query Management Score
        query_rate = df['queries_per_subject']
        df['query_score'] = (100 - (query_rate * 10)).clip(0, 100)
        
        # Coding Score
        coding_rate = (df['meddra_uncoded'] + df['who_uncoded']) / subject_count
        df['coding_score'] = (100 - (coding_rate * 20)).clip(0, 100)
        
        # Composite DQI (Data Quality Index)
        df['calculated_dqi'] = (
            df['safety_score'] * self.FEATURE_WEIGHTS['safety'] +
            df['data_quality_score'] * self.FEATURE_WEIGHTS['data_quality'] +
            df['query_score'] * self.FEATURE_WEIGHTS['queries'] +
            df['coding_score'] * self.FEATURE_WEIGHTS['coding']
        ).astype(int)
        
        # Risk Velocity (approximation using multiple indicators)
        # Higher values indicate faster risk accumulation
        df['risk_velocity'] = (
            df['pending_sae'] * 3 +
            df['total_queries'] * 0.5 +
            df['total_missing_pages'] * 0.3 +
            df['max_missing_days'] * 0.1
        ) / subject_count
        
        # Protocol Compliance Index
        df['compliance_index'] = (100 - df['deviations_per_subject'] * 20).clip(0, 100)
        
        return df
    
    def _add_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add encoded categorical features."""
        
        # Site size category based on subject count
        df['site_size_category'] = pd.cut(
            df['subject_count'],
            bins=[0, 10, 50, 100, float('inf')],
            labels=[0, 1, 2, 3]  # Small, Medium, Large, Very Large
        ).astype(float).fillna(0)
        
        # Country risk encoding (simplified - in production this would be data-driven)
        # For now, just count unique values for ordinality
        if 'country' in df.columns:
            country_counts = df['country'].value_counts()
            df['country_prevalence'] = df['country'].map(country_counts).fillna(1)
        else:
            df['country_prevalence'] = 1
            
        # Study complexity (based on query diversity)
        query_cols = ['dm_queries', 'clinical_queries', 'medical_queries', 
                      'safety_queries', 'coding_queries']
        existing_cols = [c for c in query_cols if c in df.columns]
        if existing_cols:
            df['query_diversity'] = (df[existing_cols] > 0).sum(axis=1)
        else:
            df['query_diversity'] = 0
        
        return df
    
    def _add_risk_trajectory_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features representing risk trajectory and patterns."""
        
        # Risk concentration (how many risk factors are elevated)
        df['risk_concentration'] = (
            (df['sae_per_subject'] > df['sae_per_subject'].median()).astype(int) +
            (df['missing_per_subject'] > df['missing_per_subject'].median()).astype(int) +
            (df['queries_per_subject'] > df['queries_per_subject'].median()).astype(int) +
            (df['deviations_per_subject'] > df['deviations_per_subject'].median()).astype(int)
        )
        
        # Relative performance (percentile ranks)
        df['dqi_percentile'] = df['calculated_dqi'].rank(pct=True) * 100
        df['safety_percentile'] = df['safety_score'].rank(pct=True) * 100
        
        # Critical flags
        df['has_pending_sae'] = (df['pending_sae'] > 0).astype(int)
        df['high_missing_burden'] = (df['missing_burden_per_subject'] > 5).astype(int)
        df['high_query_load'] = (df['queries_per_subject'] > 10).astype(int)
        
        # Aggregate risk flag count
        df['critical_flag_count'] = (
            df['has_pending_sae'] + 
            df['high_missing_burden'] + 
            df['high_query_load']
        )
        
        return df
    
    def _generate_risk_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate risk labels for supervised learning."""
        
        # Multi-factor risk classification
        conditions = [
            # High Risk: DQI < 50 OR (any SAE AND DQI < 70) OR high risk velocity
            (df['calculated_dqi'] < 50) | 
            ((df['sae_count'] > 0) & (df['calculated_dqi'] < 70)) |
            (df['risk_velocity'] > df['risk_velocity'].quantile(0.85)),
            
            # Medium Risk: DQI between 50-80 OR moderate risk indicators
            (df['calculated_dqi'] >= 50) & (df['calculated_dqi'] < 80),
        ]
        
        choices = [2, 1]  # 2=High, 1=Medium, 0=Low (default)
        
        df['risk_label'] = np.select(conditions, choices, default=0)
        
        # Also keep string labels for reference
        risk_map = {0: 'Low', 1: 'Medium', 2: 'High'}
        df['risk_level_str'] = df['risk_label'].map(risk_map)
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names used for model training."""
        return [
            # Per-subject normalized
            'missing_per_subject', 'queries_per_subject', 'sae_per_subject',
            'deviations_per_subject', 'edrr_per_subject', 'missing_burden_per_subject',
            
            # Rates and ratios
            'sae_review_rate', 'coding_completion_rate', 'avg_query_latency',
            'safety_query_ratio', 'dm_query_ratio', 'signature_integrity',
            
            # Composite scores
            'safety_score', 'data_quality_score', 'query_score', 'coding_score',
            'calculated_dqi', 'risk_velocity', 'compliance_index',
            
            # Categorical
            'site_size_category', 'country_prevalence', 'query_diversity',
            
            # Trajectory
            'risk_concentration', 'dqi_percentile', 'safety_percentile',
            'has_pending_sae', 'high_missing_burden', 'high_query_load',
            'critical_flag_count',
            
            # Raw important metrics
            'subject_count', 'avg_missing_days', 'max_missing_days',
            'avg_clean_crf_pct'
        ]


if __name__ == "__main__":
    print("🔧 Testing Feature Engineering Pipeline...")
    
    fe = FeatureEngineer()
    features_df = fe.extract_all_features()
    
    if not features_df.empty:
        print(f"✅ Extracted features for {len(features_df)} sites")
        print(f"📊 Total features: {len(features_df.columns)}")
        print(f"\n📋 Feature columns:\n{list(features_df.columns)}")
        print(f"\n📈 Sample data:\n{features_df.head()}")
        
        # Save for model training
        features_df.to_csv("backend/ml/advanced_features.csv")
        print("\n💾 Saved features to backend/ml/advanced_features.csv")
    else:
        print("❌ No data found. Please run data ingestion first.")
