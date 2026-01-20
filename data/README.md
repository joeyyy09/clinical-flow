# Clinical Trial Data Samples

This directory contains anonymized sample datasets used for demonstrating the ClinicalFlow platform's ingestion and analysis capabilities.

## File Categorization

The ingestion engine (`backend/ingestion.py`) dispatches files based on their naming patterns:

### 1. Safety & SAEs
- **Pattern**: `SAE Dashboard` or `eSAE`
- **Example**: `eSAE Dashboard DM_Safety 1_updated.xlsx`
- **Stored in**: `sae_metrics` table.
- **Key Metrics**: Country, Site, Patient ID, Review Status.

### 2. EDC & Data Management
- **Pattern**: `Global_Missing_Pages`
- **Example**: `Global_Missing_Pages_Report_updated.xlsx`
- **Stored in**: `missing_pages` table.
- **Key Metrics**: Site Number, Subject Name, Form Name, Missing Days.

### 3. Subject Tracking
- **Pattern**: `EDC_Metrics`
- **Example** (Mocked): User uploads of clinical performance metrics.
- **Stored in**: `edc_metrics` table.
- **Key Metrics**: Site ID, Subject ID, Subject Status, Latest Visit.

## Source Information
These files are largely derived from historical clinical trial benchmarks and are anonymized to ensure no Protected Health Information (PHI) is present.

## Testing
A small `test_upload.xlsx` is provided for verifying basic spreadsheet parsing logic.
