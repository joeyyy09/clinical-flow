# Data Documentation: Preprocessing & Integrity

This document outlines the systematic approach used to ensure data quality and integrity within the ClinicalFlow ML pipeline.

## 1. Data Cleaning & Normalization
- **Handling Missing Values**: We use `fillna(0)` for metric counts (SAEs, Missing Pages) as a missing entry in clinical trials often implies zero events of that type for the specific snapshot.
- **Normalization**: Column names are normalized across diverse Excel sources (e.g., "Site ID", "Site #", "SITE_NO" all map to `site_id`) to ensure consistent feature extraction.
- **Outlier Detection**: Heuristics filter out impossible values (e.g., negative missing days) before they enter the training set.

## 2. Feature Engineering
We derive high-order features to capture site performance dynamics:
- **Missingness Density**: `missing_pages / total_subjects`. Captures the intensity of data entry issues.
- **SAE Review Rate**: `reviewed_saes / total_saes`. Indicates the responsiveness of the clinical team.
- **Risk Target (Labeling)**: A three-class target (0: Low, 1: Medium, 2: High) is derived using a compound heuristic that reflects audit failure risk.

## 3. Data Integrity & Leakage Prevention
- **Temporal Integrity**: We ensure that features and labels are derived from the same data snapshot to prevent "future leak".
- **Train-Test Split**: We use a standard 80/20 stratified split to ensure that the model generalizes well to unseen sites.
- **Site-Level Separation**: Data is split by Site ID. No site present in the training set appears in the testing set, preventing the model from simply memorizing specific site IDs.

## 4. Reproducibility
- **Random Seed**: All stochastic operations (Train-Test split, Random Forest initialization) use `random_state=42`.
- **Environment**: Managed via `backend/requirements-ml.txt`.
- **Database Logic**: Deterministic SQLAlchemy queries ensure the same feature set is generated from the same raw data.
