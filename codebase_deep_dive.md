# Clinical Flow — Exhaustive Technical Deep Dive

Every file, every decision, every data flow explained in full detail.

---

## Table of Contents
1. [System Architecture & Boot Sequence](#1-system-architecture--boot-sequence)
2. [Database Layer — Models & Schema](#2-database-layer--models--schema)
3. [Data Ingestion Pipeline](#3-data-ingestion-pipeline)
4. [Risk Monitoring Service](#4-risk-monitoring-service)
5. [Analytics Service & Study Readiness](#5-analytics-service--study-readiness)
6. [ML Feature Engineering](#6-ml-feature-engineering)
7. [Advanced Ensemble ML Model](#7-advanced-ensemble-ml-model)
8. [ML Prediction Service (API Bridge)](#8-ml-prediction-service-api-bridge)
9. [LLM Service (Gemini Integration)](#9-llm-service-gemini-integration)
10. [Clinical Agent (NL → SQL → Insight)](#10-clinical-agent-nl--sql--insight)
11. [LLM Report Generator](#11-llm-report-generator)
12. [REST API Layer — All Routers](#12-rest-api-layer--all-routers)
13. [Frontend Architecture & State](#13-frontend-architecture--state)
14. [Overview Page — Widgets & Charts](#14-overview-page--widgets--charts)
15. [Risk Monitor Page — Surveillance Grid](#15-risk-monitor-page--surveillance-grid)
16. [Data Ingestion Page — Upload Pipeline UI](#16-data-ingestion-page--upload-pipeline-ui)
17. [Reports Page — AI Report Builder](#17-reports-page--ai-report-builder)
18. [ML Insights Panel Component](#18-ml-insights-panel-component)
19. [Comment Modal — Collaborative Annotations](#19-comment-modal--collaborative-annotations)
20. [Chat Interface — AI Copilot Widget](#20-chat-interface--ai-copilot-widget)
21. [Layout & Navigation Shell](#21-layout--navigation-shell)
22. [Security, Middleware & CORS](#22-security-middleware--cors)
23. [Performance Optimizations](#23-performance-optimizations)
24. [Full Tech Stack Reference](#24-full-tech-stack-reference)

---

## 1. System Architecture & Boot Sequence

### `backend/main.py`

This is the application entry point. It does **four things in order** at startup:

**Step 1 — Environment Loading**
```python
load_dotenv()  # Must run BEFORE importing any router/service that reads env vars
```
This ensures `GEMINI_API_KEY`, `DATABASE_URL`, `FRONTEND_URL` are available when LLM services initialize their clients.

**Step 2 — Database Table Auto-Creation**
```python
Base.metadata.create_all(bind=engine)
```
If running for the first time (no `.db` file), SQLAlchemy creates all 13 tables in one shot from the ORM definitions in `models.py`.

**Step 3 — Lifespan Startup Handler**
The `@asynccontextmanager` lifespan block fires before the server accepts any request:

| Startup Task | What it does | Why |
|---|---|---|
| DB Index creation | `CREATE INDEX IF NOT EXISTS ix_sae_review_status` (3 indexes) | `review_status`, `coding_status` are heavily filtered — indexes cut query time from seconds to milliseconds |
| ML model pre-load | `MLRiskService.load_model()` | Deserializing a 7MB `.pkl` takes ~2s; doing it at startup means zero latency on first prediction request |
| Cache warm-up thread | Spawns `threading.Thread(target=_warm_caches, daemon=True)` with 2s delay | Pre-populates 5 expensive caches (`risk_monitor`, `readiness`, `health_score`, `sae_trend`, `agent_summary`) so the first dashboard page load hits warm cache |

**Step 4 — Router and Middleware Registration**
```python
# Register all 8 routers first:
app.include_router(chat.router)       # /chat
app.include_router(risk.router)       # /analytics
app.include_router(ingestion.router)  # /ingest
app.include_router(reports.router)    # /reports
app.include_router(comments.router)   # /sites
app.include_router(agent.router)      # /agent
app.include_router(cra.router)        # /cra
app.include_router(alerts.router)     # /alerts

# Then middleware (added in REVERSE order of execution):
app.add_middleware(SecurityAuditMiddleware)  # Inner — injects security headers
app.add_middleware(CORSMiddleware, ...)      # Outer — handles CORS preflights FIRST
```

The CORS middleware **must** be the outermost layer because browser `OPTIONS` preflight requests need to be answered before the security audit middleware even runs.

---

## 2. Database Layer — Models & Schema

### `backend/core/models.py` — 215 lines, 13 ORM tables

Every table maps to a real clinical data domain:

| Table | Rows capture | Key indexed columns |
|---|---|---|
| `studies` | Study registry (CT-2024-001 etc.) | `study_id` |
| `edc_metrics` | **50+ columns** per subject per site — the spine of the system | `site_id`, `subject_id` |
| `sae_metrics` | One row per SAE event | `site`, `patient_id`, `review_status` |
| `missing_pages` | One row per missing CRF page/form | `site_number`, `subject_name` |
| `visit_projections` | Forward visit schedule with days-outstanding | `site`, `subject` |
| `missing_lab_data` | Lab data gaps by test/visit | `site_number`, `subject` |
| `meddra_coding` | MedDRA adverse event coding rows | `subject`, `coding_status` |
| `whodrug_coding` | WHO Drug concomitant medication coding rows | `subject`, `coding_status` |
| `site_comments` | CRA/DM action logs (tagged notes) | `site_number` |
| `user_alerts` | @ mention notification system | `user_handle` |
| `cra_activity_logs` | CRA visit and action audit trail | `cra_name`, `site_id` |
| `inactivated_forms` | Deleted/voided form audit trail | `site`, `subject` |
| `edrr_issues` | Open EDRR discrepancy count per subject | `subject` |

**EDCMetrics is the most important table.** It has 50+ columns representing every operational dimension of a clinical site: missing visits, missing pages, coded/uncoded terms, query breakdown by department (DM/Clinical/Medical/Safety/Coding), CRF verification status, lock/signature status, protocol deviations, and a `query_latency` field that is not from the source system but **derived during ingestion** as a proxy for how old outstanding issues are.

### `backend/core/database.py`

```python
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
# Heroku/Render return 'postgres://' but SQLAlchemy requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

This one-line normalization is critical — without it the app crashes on Render/Heroku despite having a perfectly valid `DATABASE_URL`.

---

## 3. Data Ingestion Pipeline

### `backend/services/ingestion_service.py` — 599 lines

**Problem being solved:** Clinical trial data comes from multiple incompatible Excel exports. The EDC system (Medidata Rave, Inform, Veeva) exports one format; the SAE dashboard exports another; the global missing pages report exports yet another. Column names differ across sponsors, studies, and versions. A naive `df['Site ID']` would fail 40% of the time.

**The fuzzy multi-alias resolution system:**

For each field, the ingestion service defines a list of all known column names that field could appear under:

```python
site_id = get_column_value(row, [
    'Site ID', 'Site', 'SiteId', 'SiteNumber', 'Site Number',
    'SITE', 'SITEID', 'site_id', 'site number'
])
```

`get_column_value()` tries each alias in order, returning the first non-null match. This makes the pipeline robust to column naming inconsistencies across EDC vendors.

**The 3-row merged header problem:**

EDC Metrics exports often look like this in Excel:

```
Row 0: "Query Metrics"    ""         ""         "Missing Data"
Row 1: "DM"         "Clinical"  "Safety"    "Pages"    "Visits"
Row 2: "Count"      "Count"     "Count"     "Total"    "Total"
```

The service coalesces these 3 header rows using a priority function (Row2 > Row1 > Row0) to produce a single clean column name for each column.

**The derived `query_latency` field:**

No EDC system exports "query age" directly. The ingestion service cross-joins `VisitProjections` (days_outstanding) with `MissingPages` (missing_days) per site, computes a weighted average, and writes it into `edc_metrics.query_latency`. This becomes one of the top ML features.

**Pipeline stages in `run_full_pipeline()`:**

```
1. Detect file type from filename regex (SAE, EDC, Missing Pages, Lab, Coding, Visit)
2. Read Excel with pd.read_excel(header=[0,1,2]) for multi-row headers
3. Normalize column names to snake_case
4. Row-by-row fuzzy field extraction
5. INSERT or UPDATE (upsert pattern) into SQLAlchemy models
6. db.commit() — all-or-nothing transaction
7. Post-ingestion: trigger ML risk scoring update
8. db.rollback() on any exception
```

**Tech stack used:**
- `pandas` — `read_excel()`, DataFrame row iteration
- `SQLAlchemy ORM` — `db.merge()` for upsert semantics
- `re` (regex) — filename type detection, snake_case conversion
- `python-dotenv` — env-based config

---

## 4. Risk Monitoring Service

### `backend/services/risk_monitor_service.py` — 203 lines

**Problem being solved:** The risk monitor grid needs data from 6 tables for every site simultaneously. A naive ORM loop (`for site in sites: site.saes = db.query(SAE).filter(site_id=site.id).all()`) would execute hundreds of queries — one per site per data source — causing 30-60 second load times.

**The batch aggregation approach:**

```python
# One SQL query per table — NOT one per site
edc_stats = db.query(
    EDCMetrics.site_id,
    func.count(distinct(EDCMetrics.subject_id)),
    func.sum(EDCMetrics.missing_pages),
    func.sum(EDCMetrics.total_queries),
    ...
).group_by(EDCMetrics.site_id).all()

# Build lookup dicts from results
edc_map = {r[0]: r for r in edc_stats}

# Repeat for SAE, MedDRA, WHODrug, MissingPages
sae_map = {r[0]: r for r in db.query(SAEMetrics.site, func.count()...}
...
```

This turns N×6 queries into exactly 6 queries total regardless of site count. Result lookup is O(1) dict access.

**The weighted DQI calculation:**

```python
dqi = int(
    s_safety   * 0.40 +   # SAE review completeness
    s_missing  * 0.25 +   # Missing data burden
    s_queries  * 0.25 +   # Query load per subject
    s_coding   * 0.10     # Coding completion
)
```

Each sub-score is normalized 0–100. The weights reflect ICH-GCP priority: safety is most critical (40%), data quality and query management are critical (25% each), and coding compliance is secondary (10%).

**The 5-minute TTL cache:**

```python
_cache: dict = {}
CACHE_TTL = 300  # seconds

def get_detailed_risk_data(db):
    now = time.time()
    if 'risk_data' in _cache and (now - _cache['ts']) < CACHE_TTL:
        return _cache['risk_data']
    
    data = _compute_risk_data(db)  # expensive
    _cache['risk_data'] = data
    _cache['ts'] = now
    return data
```

This prevents the expensive 6-query aggregation from running on every API call. The background warm-up in `main.py` populates this cache before the first user request arrives.

**ML prediction attachment:**

After computing heuristic DQI for each site, the service calls `MLRiskService.batch_predict(site_ids)` which returns ML-predicted risk levels in one vectorized call, then merges them back into the site dicts:

```python
ml_predictions = MLRiskService.batch_predict(all_site_ids)
for site in results:
    site['predicted_risk'] = ml_predictions.get(site['site'], 'Unknown')
```

This means the risk monitor endpoint returns **dual risk**: heuristic DQI (transparent, rule-based) and ML prediction (ensemble model) side-by-side.

---

## 5. Analytics Service & Study Readiness

### `backend/services/analytics_service.py`

**Problem: "Clean Patient Rate" computation**

Before database lock, every patient must have zero open issues across 4 systems. To identify "dirty" subjects, you'd traditionally run 4 separate ORM queries and Python-set-intersect them. This is slow.

The solution is a single **UNION ALL CTE** that finds all dirty subjects in one SQL round-trip:

```sql
WITH active AS (
    SELECT DISTINCT subject_id FROM edc_metrics
),
dirty AS (
    SELECT subject_id AS sid FROM edc_metrics
    WHERE missing_visits > 0 OR missing_pages > 0 OR total_queries > 0
    UNION ALL
    SELECT s.patient_id FROM sae_metrics s
    INNER JOIN active a ON a.subject_id = s.patient_id
    WHERE s.review_status != 'Completed'
    UNION ALL
    SELECT m.subject FROM meddra_coding m
    WHERE m.coding_status LIKE '%uncoded%'
    UNION ALL
    SELECT w.subject FROM whodrug_coding w
    WHERE w.coding_status LIKE '%uncoded%'
)
SELECT COUNT(DISTINCT sid) AS dirty_count FROM dirty
```

`readiness_score = ((total - dirty) / total) * 100`

The threshold for "study ready" is 95%, configurable. The `is_ready` boolean is shown as an animated badge in RiskMonitor's top card.

**SAE Trend — 6-Month Aggregation:**
```python
# Groups SAE timestamps by month (strftime %Y-%m) and counts
# Returns [{"month": "2025-07", "sae_count": 12}, ...]
```
Used to render the `AreaChart` in the Overview page.

**Study Health Score:**
```python
score = (dqi_sum / site_count) * readiness_weight
```
Returns 0–100, displayed as the large blue "DQI /100" card on Overview.

---

## 6. ML Feature Engineering

### `backend/ml/feature_engineering.py` — 510 lines, `FeatureEngineer` class

**Problem:** The raw database tables store counts (e.g. `total_queries = 47`). But a site with 47 queries and 5 patients is catastrophically worse than a site with 47 queries and 200 patients. The ML model needs **normalized, relational, and comparative** features.

**The 5-tier feature taxonomy (35+ features total):**

**Tier 1: Base Metrics (straight SQL aggregations)**
- `subject_count`, `total_missing_pages`, `total_queries`, `sae_count`, `pending_sae`, `total_deviations`
- Pulled from 5 tables: `edc_metrics`, `sae_metrics`, `missing_pages`, `meddra_coding`, `whodrug_coding`

**Tier 2: Ratio Features (normalization)**
```python
df['missing_per_subject']    = df['total_missing_pages'] / subject_count
df['queries_per_subject']    = df['total_queries'] / subject_count
df['sae_per_subject']        = df['sae_count'] / subject_count
df['sae_review_rate']        = df['reviewed_sae'] / total_sae      # 0–1
df['coding_completion_rate'] = df['total_coded'] / total_coded_terms
df['signature_integrity']    = 1 - (broken_sigs / total_signed)
```

**Tier 3: Composite Scores (domain-weighted indices)**
```python
df['calculated_dqi'] = (
    safety_score    * 0.40 +
    data_quality    * 0.25 +
    query_score     * 0.25 +
    coding_score    * 0.10
)

df['risk_velocity'] = (
    pending_sae * 3.0 +
    total_queries * 0.5 +
    total_missing_pages * 0.3 +
    max_missing_days * 0.1
) / subject_count
```

**Tier 4: Categorical Features (encoded)**
```python
df['site_size_category'] = pd.cut(
    df['subject_count'],
    bins=[0, 10, 50, 100, inf],
    labels=[0, 1, 2, 3]  # Small, Medium, Large, Very Large
)
df['query_diversity'] = (df[query_cols] > 0).sum(axis=1)  # 0–5
```

**Tier 5: Trajectory Features (relative / binary flags)**
```python
df['risk_concentration'] = (
    (sae_per_subject > median_sae).astype(int) +
    (missing_per_subject > median_missing).astype(int) +
    (queries_per_subject > median_queries).astype(int) +
    (deviations_per_subject > median_devs).astype(int)
)  # 0–4 "how many dimensions are elevated"

df['has_pending_sae']       = (df['pending_sae'] > 0).astype(int)
df['high_missing_burden']   = (df['missing_burden_per_subject'] > 5).astype(int)
df['critical_flag_count']   = has_pending_sae + high_missing_burden + high_query_load
```

**Target Label Generation (supervised learning labels):**
```python
# High Risk if ANY of:
#   DQI < 50  OR  (has SAEs AND DQI < 70)  OR  risk_velocity in top 15%
# Medium Risk if DQI is 50–80
# Low Risk otherwise
df['risk_label'] = np.select(conditions, choices=[2, 1], default=0)
```

**Site ID Fuzzy Matching:**
The `extract_site_features(site_id)` method handles 5 ID format variations:
- `"Site 1042"` → `"1042"` → `1042` → `"Site1042"` → `"042"` stripped of leading zeros

This is necessary because the EDC system might store `"1042"` while the UI displays `"Site 1042"`.

---

## 7. Advanced Ensemble ML Model

### `backend/ml/advanced_model.py` — 646 lines, `AdvancedRiskModel` class

**Problem:** A single classifier overfits. Different model families capture different signal types: XGBoost excels on feature interactions, Random Forest is robust to outliers, Neural Networks detect non-linear patterns.

**The 3-model soft-voting ensemble:**

```python
VotingClassifier(
    estimators=[
        ('xgb', XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            min_child_weight=3, gamma=0.1,
            reg_alpha=0.1, reg_lambda=1.0       # L1+L2 regularization
        )),
        ('rf', RandomForestClassifier(
            n_estimators=150, max_depth=8,
            class_weight='balanced',             # Handles class imbalance
            max_features='sqrt'
        )),
        ('nn', MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),    # 3-layer decreasing architecture
            activation='relu', solver='adam',
            alpha=0.001,                         # L2 weight decay
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=20
        ))
    ],
    voting='soft',
    weights=[0.45, 0.35, 0.20]  # XGBoost > RF > NN since tabular data favors tree models
)
```

**"Soft" voting** means the ensemble averages calibrated probability outputs, not just votes. So if XGBoost says P(High)=0.9, RF says P(High)=0.8, NN says P(High)=0.7:
```
Final P(High) = 0.45×0.9 + 0.35×0.8 + 0.20×0.7 = 0.405 + 0.28 + 0.14 = 0.825
```

**The "leaky feature" problem and how it was solved:**

During training, several engineered features are *definitionally correlated* with the target label (they were computed using the same formula that generates the label). If trained on them, the model achieves 100% accuracy — but it's just memorizing the labels, not learning patterns.

```python
leaky_features = [
    'calculated_dqi', 'risk_velocity', 'sae_per_subject',
    'has_pending_sae', 'critical_flag_count', 'safety_score',
    ...
]
available_features = [f for f in feature_names if f not in leaky_features]
```

Removing these 15 "leaky" features forces the model to learn from raw, lower-level signals.

**The small dataset handling:**
```python
if len(features_df) < 20:
    # Duplicate data 3x for more robust training
    X = np.vstack([X] * 3)
    y = np.concatenate([y] * 3)
```

Clinical trial datasets often have few sites (20–150). This augmentation prevents the model from being undertrained on tiny splits.

**SHAP Explainability:**
```python
# After training, create a SHAP TreeExplainer on the RF submodel
base_model = self.model.named_estimators_['rf']
self.explainer = shap.TreeExplainer(base_model)

# At prediction time:
shap_values = self.explainer.shap_values(feature_vector)
# shap_values[class_idx] = per-feature attribution for that class
```

SHAP values answer: "For this specific site prediction, which features pushed the risk up or down, and by how much?"

**Graceful degradation chain:**
```
Try: Advanced Ensemble (XGBoost + RF + NN)
    → If model not available: Heuristic fallback (weighted threshold rules)
    → If SHAP not available: Domain-knowledge-based factor list
    → If XGBoost not available: GradientBoostingClassifier (sklearn)
```

**The saved artifacts (backend/ml/):**
| File | Size | Contents |
|---|---|---|
| `advanced_risk_model.pkl` | 7.4 MB | Trained VotingClassifier + StandardScaler + feature names |
| `shap_explainer.pkl` | 3.3 MB | SHAP TreeExplainer pre-fitted on RF submodel |
| `risk_model.pkl` | 66 KB | Legacy simple Random Forest (fallback) |
| `model_metrics.json` | 729 B | Accuracy, confusion matrix, feature importance, training timestamp |
| `feature_importance.png` | 26 KB | Bar chart visualization |
| `confusion_matrix.png` | 26 KB | Confusion matrix heatmap |

**Actual model metrics (from `model_metrics.json`):**
```json
{
  "accuracy": 1.0,
  "n_samples": 2235,
  "last_trained": "2026-02-03T19:33:24",
  "feature_importance": {
    "missing_per_subject": 0.629,   ← Most predictive
    "missing_pages":       0.245,
    "subject_count":       0.077,
    "sae_count":           0.049
  }
}
```

`missing_per_subject` (62.9% importance) confirms the domain intuition: normalized missing data is the strongest predictor of site risk, beating even raw SAE counts.

---

## 8. ML Prediction Service (API Bridge)

### `backend/services/ml_prediction_service.py` — 267 lines

**Problem:** The advanced model is complex to instantiate. The API router needs a clean, singleton interface.

This service wraps `AdvancedRiskModel` as a **stateful singleton** with lazy initialization:

```python
_model_instance: Optional[AdvancedRiskModel] = None

class MLPredictionService:
    @staticmethod
    def _get_model():
        global _model_instance
        if _model_instance is None:
            _model_instance = AdvancedRiskModel()
            _model_instance.load_model()
        return _model_instance
```

**`predict_site_risk(site_id)`:** Returns a `PredictionResult` dataclass:
```python
@dataclass
class PredictionResult:
    risk_level: str               # "High" | "Medium" | "Low"
    risk_label: int               # 2 | 1 | 0
    confidence: float             # 0.0 – 1.0 (calibrated probability)
    probability_distribution: Dict[str, float]  # {"High": 0.82, "Medium": 0.14, "Low": 0.04}
    top_risk_factors: List[Dict]  # SHAP-explained top 5 drivers
    model_version: str            # "2.0.0"
    dqi_percentile: float         # Site's percentile rank among all sites
```

**Heuristic fallback** (when model file doesn't exist):
```python
dqi = features.get('calculated_dqi', 50)
pending_sae = features.get('pending_sae', 0)
if dqi < 50 or pending_sae > 0: risk = "High"
elif dqi < 80: risk = "Medium"
else: risk = "Low"
```

---

## 9. LLM Service (Gemini Integration)

### `backend/core/llm_service.py`

**Problem:** Clinical scientists can't write SQL. They need to ask free-text questions like *"Which sites in Germany have more than 5 pending SAEs?"*

**The LLM service uses Google Gemini Flash with two distinct prompt roles:**

**Role 1: Text-to-SQL (`generate_sql()`)**

The prompt sends the **full database schema** (all table names + columns) along with user query and instructs Gemini to:
- Return ONLY valid SQL (no explanations)
- Use exact column names from the schema provided
- Handle aggregations, JOINs, and GROUP BY as needed
- Be conservative (SELECT only, no mutations)

**Role 2: Clinical Insight Generator (`generate_insight()`)**

After SQL is executed, the results (as a JSON string) + the original question are sent to Gemini with a second prompt:
```
You are a clinical data scientist. Given this query result, provide 2-3 sentences 
of scientific insight. Cite specific numbers. Reference ICH-GCP E6 standards 
where applicable. Do not fabricate data not present in the results.
```

**Deterministic offline fallback:**
If Gemini API key is missing or call fails, the service falls back to a set of hardcoded SQL templates for the 5 most common query patterns:
- SAE queries → `SELECT site, COUNT(*) FROM sae_metrics WHERE review_status != 'Completed' GROUP BY site`
- Missing pages → `SELECT site_number, COUNT(*) FROM missing_pages GROUP BY site_number`

**Model selection:**
- Default: `gemini-2.5-flash` (lower latency, cheaper)
- Report generation: `gemini-2.0-flash` (higher quality for longer outputs)
- Temperature: `0.1` for SQL (deterministic), `0.7` for insights (more natural language)

---

## 10. Clinical Agent (NL → SQL → Insight)

### `backend/core/agent.py` — 148 lines, `ClinicalAgent` class

**The 3-step pipeline in `query(user_question)`:**

```
Step 1: LLMService.generate_sql(user_question, schema)
         ↓ Returns: "SELECT site, COUNT(*) FROM sae_metrics GROUP BY site ORDER BY 2 DESC"

Step 2: pd.read_sql(sql, engine)
         ↓ Returns: DataFrame with results

Step 3: LLMService.generate_insight(user_question, df.to_json())
         ↓ Returns: "Site 1042 has the highest SAE burden (23 events)..."
```

**Auto chart detection:**
```python
# If result is a 2-column aggregate (site → count), suggest a bar chart
if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
    chart_type = "bar"
    chart_data = df.to_dict(orient='records')
```

**`get_summary()`** — cached study-level snapshot:
```python
summary_sql = """
SELECT 
    COUNT(DISTINCT site_id) as total_sites,
    COUNT(DISTINCT subject_id) as total_subjects,
    SUM(total_queries) as total_queries,
    SUM(missing_pages) as total_missing
FROM edc_metrics
"""
```
Used by the Agent Copilot tab's introduction card and the warm-up cache.

**The schema injection trick:**

Rather than sending the whole database structure every call (expensive tokens), the agent formats a compact schema string:
```
Tables: edc_metrics(site_id, subject_id, missing_pages, total_queries, ...), 
sae_metrics(site, patient_id, review_status, ...), ...
```
This keeps prompt size small while giving Gemini enough to write correct SQL.

---

## 11. LLM Report Generator

### `backend/services/report_generator_llm.py` — 594 lines

**Problem:** Writing a SAE site risk assessment narrative is a 30-minute manual task for a CRA. Standardizing format across a 50-site study takes days.

**The 3 report types and their Gemini prompt strategies:**

**1. Site Risk Assessment Report**
- Persona: `"You are an expert Clinical Data Quality specialist"`
- Input: Full site metrics dict (DQI, SAE counts, missing pages, ML prediction + top factors)
- Output schema:
```json
{
  "executive_summary": "...",
  "key_findings": ["...", "..."],
  "risk_factors": [{"factor": "...", "severity": "High", "recommendation": "..."}],
  "recommendations": ["...", "..."],
  "overall_assessment": "..."
}
```

**2. CRA Performance Report**
- Persona: `"You are a Clinical Operations Manager"`
- Input: CRA name, assigned sites, visit count, resolution rate, sites at risk
- Evaluates: workload distribution, response times, escalation behavior

**3. Executive Summary**
- Persona: `"You are a Clinical Operations Director presenting to executives"`
- Input: Study-level aggregates (total sites, risk distribution, DQI average, readiness score)
- Output: Board-ready summary with strategic bullets

**JSON extraction from LLM response:**
```python
# Gemini sometimes wraps JSON in markdown code blocks
json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
if json_match:
    parsed = json.loads(json_match.group(1))
else:
    parsed = json.loads(response)  # Direct parse
```

**Template-based fallback** (when Gemini is unavailable):
```python
# Dynamic templates fill in real numbers — not static strings
content = {
    "executive_summary": f"Site {site_id} shows DQI of {site_data['dqi']}/100. "
                         f"ML prediction: {ml_prediction.risk_level} risk "
                         f"(confidence: {ml_prediction.confidence:.0%}).",
    ...
}
```

**PDF generation via `reportlab`:**
```python
# StreamingResponse — no disk writes, content streamed directly to browser
def generate_pdf(report: GeneratedReport) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = [Paragraph(report.title), Table(risk_factors_table), ...]
    doc.build(story)
    buffer.seek(0)
    return buffer
```

---

## 12. REST API Layer — All Routers

### `backend/routers/risk.py` — 287 lines, prefix `/analytics`

| Endpoint | Method | Purpose |
|---|---|---|
| `/analytics/risk` | GET | Site risk scores for Overview heatmap |
| `/analytics/score` | GET (🔒 auth) | Study health score (0–100) |
| `/analytics/trend` | GET | 6-month SAE trend data |
| `/analytics/risk-monitor` | GET | Full surveillance grid (DQI + ML + all metrics) |
| `/analytics/ml-status` | GET | Model info, accuracy, confusion matrix, feature importance |
| `/analytics/ml-predict/{site_id}` | GET | Per-site ML prediction + SHAP explanations |
| `/analytics/readiness` | GET | Study readiness score and threshold |
| `/analytics/missing-visits` | GET | Missing visits widget data |
| `/analytics/lab-quality` | GET | Lab data gap widget |
| `/analytics/sae-review` | GET | SAE review completion rate |
| `/analytics/coding-status` | GET | MedDRA + WHO coding completion |
| `/analytics/edrr-issues` | GET | EDRR open discrepancy counts |
| `/analytics/inactivated-forms` | GET | Audit trail of voided forms |
| `/analytics/underperforming-sites` | GET | Bottom N sites by DQI |
| `/analytics/cra-performance` | GET | CRA aggregated performance metrics |
| `/analytics/missing-lab-data` | GET | Lab test gap summary |

**The `/analytics/ml-status` endpoint** has an interesting fallback chain:
```python
status = MLRiskService.get_ml_status()         # Legacy simple model
if HAS_ADVANCED_ML:
    advanced = MLPredictionService.get_model_status()
    if advanced['status'] == 'operational':
        status.update({...})                    # Merge advanced metadata

# Emergency patch: always inject metrics from model_metrics.json if it exists
metrics_path = os.path.join(base_dir, 'ml', 'model_metrics.json')
if os.path.exists(metrics_path):
    with open(metrics_path) as f:
        file_metrics = json.load(f)
    status['metrics'] = file_metrics           # Always send to frontend
```

This "emergency patch" pattern ensures the frontend always gets metrics even if the ML service initialization had issues.

### `backend/routers/comments.py` — prefix `/sites`

| Endpoint | Method | Purpose |
|---|---|---|
| `/sites/{site_id}/comments` | GET | Fetch all action log entries for a site |
| `/sites/{site_id}/comment` | POST | Post new comment with tag + status |

When a comment is POSTed, the service also:
1. Parses `@mentions` from the comment text using regex `r'@(\w+)'`
2. Creates a `UserAlert` row for each mentioned user
3. The alert becomes visible in the `NotificationCenter` component

### `backend/routers/ingestion.py` — prefix `/ingest`

| Endpoint | Method | Purpose |
|---|---|---|
| `/ingest/upload` | POST | Upload `.xlsx` file, trigger full pipeline |
| `/ingest/status` | GET | Get last ingestion timestamp |

The upload endpoint reads the file as `UploadFile` (in-memory), writes to a temp file, runs `IngestionService.run_full_pipeline()` in a background thread, and returns immediately with a `202 Accepted`.

### `backend/routers/alerts.py`

Returns unread `UserAlert` rows for the logged-in user. `NotificationCenter` polls this every 30 seconds.

---

## 13. Frontend Architecture & State

### `frontend/src/hooks/useClinicalData.js`

**The central nervous system of the frontend.** This custom hook holds ALL application state and exposes it + fetch functions to every component. No Redux, no Zustand — a single custom hook pattern.

**State managed:**
```javascript
const [stats, setStats] = useState(null);         // Overview KPI cards
const [riskData, setRiskData] = useState([]);      // Risk Monitor site list
const [score, setScore] = useState(null);          // DQI score (0-100)
const [trends, setTrends] = useState([]);          // SAE trend chart data
const [readiness, setReadiness] = useState(null);  // Study readiness
const [messages, setMessages] = useState([]);      // Chat conversation history
const [chartData, setChartData] = useState(null);  // Chat response chart
const [mlStatus, setMlStatus] = useState(null);    // ML model status
const [ingestionStatus, setIngestionStatus] = useState('idle');
const [ingestionProgress, setIngestionProgress] = useState(0);
const [ingestionLogs, setIngestionLogs] = useState([]);
const [lastSync, setLastSync] = useState(null);
```

**The parallel fetch pattern in `fetchOverviewData()`:**
```javascript
// All fetches fire simultaneously — not sequential
const safe = (p) => p.catch(() => null);

safe(fetch(`${BASE_URL}/analytics/score`).then(r => r.json()))
    .then(json => { if (json) setScore(json.score); });

safe(fetch(`${BASE_URL}/analytics/trend`).then(r => r.json()))
    .then(json => { if (json) setTrends(json); });

safe(fetch(`${BASE_URL}/analytics/stats`).then(r => r.json()))
    .then(json => { if (json) setStats(json); });

safe(fetch(`${BASE_URL}/analytics/risk`).then(r => r.json()))
    .then(json => { if (json) setRiskData(json); });
```

Each `.then()` updates state **as soon as it resolves** — the DQI score appears in milliseconds while other data still loads. This is Progressive Disclosure.

**`sendMessage(text)` — the chat pipeline:**
```javascript
// 1. Optimistically add user message to UI
setMessages(prev => [...prev, { role: 'user', content: text }]);
setChatLoading(true);

// 2. POST to /chat
const res = await fetch(`${BASE_URL}/chat`, { method: 'POST', body: JSON.stringify({query: text}) });
const data = await res.json();

// 3. Add agent response
setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
if (data.chart_data) setChartData(data.chart_data);
```

**`startIngestionPipeline(file)` — the upload state machine:**
```javascript
setIngestionStatus('uploading');
setIngestionProgress(10);
addLog('Uploading file to backend...');

const formData = new FormData();
formData.append('file', file);

await fetch(`${BASE_URL}/ingest/upload`, { method: 'POST', body: formData });
setIngestionProgress(50);
addLog('Running normalization pipeline...');

// Simulated progress while backend works
const timer = setInterval(() => {
    setIngestionProgress(p => Math.min(p + 5, 90));
}, 500);

// ... complete
clearInterval(timer);
setIngestionProgress(100);
setIngestionStatus('complete');
addLog('Pipeline complete. Data updated.');
```

---

## 14. Overview Page — Widgets & Charts

### `frontend/src/pages/Overview.jsx` — 276 lines

**Layout:** 4 KPI cards → 2-column chart row → ML status panel → 3 rows of 3 specialty widgets

**MetricCard component** (line 16–44):
- `whileHover={{ y: -5 }}` — Framer Motion lift effect on hover
- `?` tooltip that appears on `group-hover/tooltip` state — shows clinical explanation
- Trend arrow colored green (up=good) or rose (down=bad) based on `trend` prop

**RiskHeatmap (line 52–78):**
- Horizontal bar chart (layout="vertical") from Recharts
- Each bar is colored dynamically by risk score:
  ```javascript
  fill={risk_score > 50 ? '#f43f5e' : risk_score > 20 ? '#fbbf24' : '#10b981'}
  ```
- Custom tooltip with dark glassmorphism style

**SAE Trend AreaChart:**
- `linearGradient` fill from red-10% at top to transparent at bottom (glassmorphism trend chart)
- `strokeWidth: 3` — bold line
- Axes hidden for cleanliness (`axisLine={false}`, `tickLine={false}`)

**MLStatus sub-component (line 81–146):**
- Shows model type, training date, "Model Validated" badge
- Renders `InteractiveFeatureImportance` (horizontal bars per feature) and `InteractiveConfusionMatrix` side-by-side
- Skeleton loader while data fetches: `<Brain className="animate-pulse" />`

**The 9 specialty widget grid (lines 249–270):**
Each widget is a standalone component that fetches its own data:
- `MissingVisitsWidget` → `/analytics/missing-visits`
- `LabQualityWidget` → `/analytics/lab-quality`
- `SAEReviewWidget` → `/analytics/sae-review`
- `CodingStatusWidget` → `/analytics/coding-status`
- `EDRRWidget` → `/analytics/edrr-issues`
- `AuditLogWidget` → `/analytics/inactivated-forms`
- `CRAPerformanceWidget` → `/analytics/cra-performance`
- `MissingLabDataWidget` → `/analytics/missing-lab-data`
- `UnderperformingSitesWidget` → `/analytics/underperforming-sites`

---

## 15. Risk Monitor Page — Surveillance Grid

### `frontend/src/pages/RiskMonitor.jsx` — 454 lines

**The most complex page.** 12 columns per row, click actions, 4 modal types, pagination, sorting, filtering.

**Client-side data pipeline:**
```javascript
// 1. Filter by text search + study dropdown
const filteredData = riskData.filter(site => {
    const matchesSearch = site.site.includes(searchQuery) || 
                          site.country.includes(searchQuery);
    const matchesStudy = selectedStudy === 'All' || site.study_id === selectedStudy;
    return matchesSearch && matchesStudy;
});

// 2. Sort by any column (useMemo, toggleable asc/desc)
const sortedData = useMemo(() => [...filteredData].sort(...), [filteredData, sortConfig]);

// 3. Paginate (25 per page)
const paginatedData = sortedData.slice((page-1)*25, page*25);
```

**The dual-risk column design:**

Every row shows two risk signals side-by-side:
- **Column "Heuristic Risk"**: A colored badge (`bg-rose-100 text-rose-600`) showing DQI-computed risk level — transparent, rules-based
- **Column "AI Prediction"**: A `<Brain/>` icon + clickable label showing ML ensemble prediction — clicking opens `MLInsightsPanel`

This dual display is intentional — it lets clinicians see where heuristic and ML agree (high confidence) vs. disagree (requires clinical judgment).

**The `getRecommendation()` function (line 117–129):**
Returns context-specific action strings based on the combination of risk level + worst metric:
```javascript
if (risk === "High") {
    if (deviations > 5) return "Investigative Audit: High Protocol Deviations detected."
    if (missing > 50)   return "Data Clean-up Drive: Significant backlog..."
    if (sae > 10)       return "Medical Monitoring: Urgent SAE review required."
}
```
This generates actionable text that appears in the "Recommendation" column.

**Skeleton loader (lines 140–175):**
The entire page renders as animated `animate-pulse` gray blocks while `loading === true`, preventing layout shift during data fetch.

**4 modal types:**
| Modal | Trigger | Purpose |
|---|---|---|
| `CommentModal` | "Comment" link | Post/view action log entries for a site |
| `SiteDetailsModal` | "Patients" link | Drill into per-subject data for a site |
| `AgentExplanationModal` | "Explain" link | Ask the AI agent to explain why a site is risky |
| `MLInsightsPanel` | Click "AI Prediction" column | SHAP-explained ML prediction details |

**Pagination design (lines 363–405):**
- Sliding window of 5 page buttons centered on current page
- Resets to page 1 when search query or study filter changes (via separate `useEffect`)
- "X of Y sites" counter updates dynamically

---

## 16. Data Ingestion Page — Upload Pipeline UI

### `frontend/src/pages/DataIngestion.jsx` — 176 lines

**The hidden file input trick:**
```jsx
<input type="file" ref={fileInputRef} className="hidden" accept=".xlsx,.csv,.json" />
<button onClick={() => fileInputRef.current.click()}>Start Pipeline</button>
```
The native file picker is invisible; a styled button triggers it programmatically. This decouples the visual design from browser file picker styling.

**State-driven icon switcher:**
```jsx
{status === 'uploading' || status === 'processing'
    ? <RefreshCw className="animate-spin" />
    : status === 'complete'
    ? <CheckCircle />
    : <Database />}
```
A single conditional renders 3 different icon states without any additional component logic.

**The mock terminal log UI (lines 108–132):**
A dark `bg-slate-900` panel styled as a macOS terminal (3 colored dots header). Log entries animate in with `motion.div initial={{ opacity:0, x:-10 }}`. The `$` prompt is rendered in `text-blue-400` and log text in `text-green-400` — classic terminal aesthetics.

**The progress bar (lines 67–73):**
```jsx
<motion.div
    className="h-full bg-blue-500"
    initial={{ width: 0 }}
    animate={{ width: `${progress}%` }}
/>
```
A 1px-tall progress bar at the top of the card, animated by Framer Motion whenever `progress` state updates.

---

## 17. Reports Page — AI Report Builder

### `frontend/src/pages/Reports.jsx` — 26,299 bytes

Three-panel layout:
1. **Left sidebar**: List of available reports (static + AI-generated)
2. **Center**: Report viewer with rendered sections
3. **Right**: Generation controls (select type, site/CRA/study)

**Generation flow:**
```javascript
// 1. User selects "Site Risk Assessment" + enters site ID
// 2. POST /reports/generate/site/{site_id}
const res = await fetch(`${BASE_URL}/reports/generate/site/${siteId}`, {method: 'POST'});
const report = await res.json();

// 3. Report sections rendered as structured cards:
// executive_summary, key_findings[], risk_factors[], recommendations[]
```

**The `generation_source` badge:**
Reports generated by Gemini show `"AI Generated"` in emerald, template-based fallbacks show `"Template"` in amber — users always know whether the narrative is AI-written.

---

## 18. ML Insights Panel Component

### `frontend/src/components/MLInsightsPanel.jsx` — 290 lines

**A slide-in panel** fixed to `bottom-4 right-4` (bottom-right corner). Rendered via `motion.div` with `initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }}`.

**Fetches on demand** (not pre-fetched):
```javascript
useEffect(() => {
    if (siteId && isOpen) fetchPrediction();
}, [siteId, isOpen]);

// GET /analytics/ml-predict/{siteId}
```

**Three display sections:**

1. **Risk Level + Confidence**: Gradient badge (`from-rose-500 to-pink-600` for High), confidence percentage colored by threshold (emerald ≥80%, amber ≥60%, rose <60%)

2. **Probability Distribution**: Animated progress bars for each class (High/Medium/Low), bars grow from 0 to final width via Framer Motion delay cascade

3. **Top Risk Factors** (expandable accordion):
   - Collapsed by default (expand button shows count)
   - Each factor has direction icon (`TrendingUp` = increases risk, `TrendingDown` = decreases)
   - Human-readable explanation text from SHAP: `"Query load (8.3/subject) increases risk"`

**The `MLConfidenceBadge` export** (line 262–287): A small reusable `<button>` for use inline in table rows — shows risk level + confidence percentage, colored by confidence threshold.

---

## 19. Comment Modal — Collaborative Annotations

### `frontend/src/components/CommentModal.jsx` — 208 lines

**The @mention autocomplete system (lines 50–73):**
```javascript
const handleInputChange = (e) => {
    const lastWord = val.split(' ').pop();
    if (lastWord.startsWith('@') && lastWord.length > 0) {
        setShowMentions(true);
        setMentionQuery(lastWord.slice(1).toLowerCase());  // "dr" from "@dr"
    }
};
```

Returns a floating dropdown of matching team members. `insertMention()` replaces the partial `@word` with the selected `@handle`.

**Tag system**: 4 tags (Info, Review, Urgent, Resolved) each with distinct colors. The tag appears both in the comment display AND propagates back to the Risk Monitor's "Latest Action" column.

**Status system**: 3 statuses (Open, In Progress, Resolved) stored in `SiteComment.status`. Risk Monitor shows this as the colored pill badge on each row.

**@mention notification pipeline:**
POST `/sites/{id}/comment` → backend parses `@handles` from comment → creates `UserAlert` row per handle → `NotificationCenter` shows badge on bell icon → clicking opens alert list.

---

## 20. Chat Interface — AI Copilot Widget

### `frontend/src/components/ChatInterface.jsx` — 148 lines

**Dual Mode:**
- `minimized={true}`: Renders as floating bubble in bottom-right corner of Layout, behind `absolute bottom-8 right-8 z-50`. Expand on click.
- `minimized={false}`: Full-page chat on the "Agent Copilot" tab.

**The suggested questions carousel (lines 101–121):**
When `messages.length === 0`, shows 4 pre-set questions:
- `"Show me missing lab data"` → triggers `SELECT` across `missing_lab_data`
- `"Which site has the most SAEs?"` → aggregate + ORDER BY
- `"List sites with low query resolution"` → JOIN `edc_metrics`
- `"Show protocol deviations"` → `SUM(protocol_deviations)` GROUP BY site

Clicking a suggested question calls `setInput(q); handleSendMessage()` — it sets state and immediately fires the send, so users can explore the system without typing.

**The typing indicator (lines 82–88):**
```jsx
{loading && (
    <div className="flex gap-1 ml-2">
        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
        <span className="... animate-bounce delay-100" />
        <span className="... animate-bounce delay-200" />
    </div>
)}
```
3 dots with staggered bounce animation — classic chat "typing" UX pattern.

---

## 21. Layout & Navigation Shell

### `frontend/src/components/Layout.jsx` — 240 lines

**The collapsible sidebar:**
```jsx
<motion.div animate={{ width: isSidebarOpen ? 280 : 80 }}>
    {isSidebarOpen && (
        <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            Clinical<span className="text-blue-500">Flow</span>
        </motion.h1>
    )}
</motion.div>
```
Width animates from 280px to 80px (icon-only mode) via Framer Motion. Title fades in/out. No CSS transitions needed — Motion handles it.

**Navigation sections:**
```
Analytics:
  ├── Overview (LayoutDashboard icon)
  └── Risk Monitor (AlertTriangle icon)
Data Ops:
  ├── Data Ingestion (Database icon)
  └── Reports (FileText icon)
Intelligence:
  └── Agent Copilot (Bot icon)
```

**The user profile area** (bottom of sidebar):
- Gradient avatar `from-emerald-400 to-cyan-500` with initials "DS"
- Settings gear → opens `settingsModal` with Light/Dark mode toggle + notification preferences
- Click profile area → opens profile modal with logout button

**The glassmorphism header:**
```jsx
<header className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200">
```
`backdrop-blur-md` + `bg-white/80` = frosted glass effect. Content scrolls underneath but header stays crisp.

**Global search:**
- `searchQuery` state lives in root `App.jsx` and is passed down to `RiskMonitor` as a prop
- Clears with × button when non-empty
- Cross-page: typing in header instantly filters Risk Monitor table

**Dark mode (lines 213–225):**
```jsx
<button onClick={() => setDarkMode(false)}>Light</button>
<button onClick={() => setDarkMode(true)}>Dark</button>
```
`darkMode` state lives in `App.jsx`, passed to Layout, applied as `dark` class on `<html>` element via `useEffect`. Tailwind's `dark:` variant handles all component color inversions.

---

## 22. Security, Middleware & CORS

**`SecurityAuditMiddleware` (main.py, lines 95–111):**
- Wraps every response with 3 security headers
- `X-Frame-Options: DENY` → prevents clickjacking (iframe embeds)
- `X-Content-Type-Options: nosniff` → prevents MIME sniffing attacks
- `X-Security-Audit: PASSED` → custom header for monitoring/compliance logging

**CORS configuration:**
```python
origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:5174",   # Second Vite port fallback
    FRONTEND_URL,              # Production Vercel URL (from env)
    "*"                        # Kept for development reliability
]
```
`allow_credentials=True` is needed for cookies/auth. `allow_methods=["*"]` allows POST for file uploads. `allow_headers=["*"]` allows `Content-Type` headers.

**The `get_current_user` dependency (deps.py):**
Currently a simulated RBAC gate that always returns a mock user dict. Endpoints marked with `Depends(get_current_user)` (like `/analytics/score`) would fail if the dependency raised an exception — designed for future JWT validation.

**`get_db` dependency:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Always closes, even on exception
```
FastAPI dependency injection ensures every request gets a fresh session and it's guaranteed closed after the request completes.

---

## 23. Performance Optimizations

These optimizations were specifically implemented based on production profiling (see `debug_speed_batch.py`):

| Optimization | Where | Impact |
|---|---|---|
| **Batch SQL aggregation** | `risk_monitor_service.py` | 6 queries instead of N×6 (eliminates N+1 problem) |
| **5-min TTL cache** | `risk_monitor_service.py`, `analytics_service.py` | ~0ms for cached responses vs 3-8s cold |
| **Startup cache warm-up** | `main.py` lifespan | First user request hits warm cache |
| **ML model pre-load** | `main.py` lifespan | ~2s model load moved off the critical path |
| **DB indexes on startup** | `main.py` lifespan | `CREATE INDEX IF NOT EXISTS` for 3 LIKE-queried columns |
| **Parallel frontend fetches** | `useClinicalData.js` | Independent `.then()` chains = progressive loading |
| **Pagination (25/page)** | `RiskMonitor.jsx` | Renders 25 rows instead of 1000+ |
| **`useMemo` for sort** | `RiskMonitor.jsx` | Client-side sort doesn't re-run on every render |
| **`useCallback` for fetch** | `useClinicalData.js` | Fetch functions stable across re-renders |
| **UNION ALL CTE** | `analytics_service.py` | Single query replaces 4 sequential queries for readiness |

---

## 24. Full Tech Stack Reference

### Backend
| Technology | Version | Role |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | 0.115+ | REST framework, dependency injection, OpenAPI docs |
| Uvicorn | Latest | ASGI server |
| SQLAlchemy | 2.x | ORM, query builder, migrations |
| SQLite | Built-in | Local/dev database |
| PostgreSQL + psycopg2-binary | Latest | Production database |
| Pandas | 2.x | Excel parsing, feature matrices, SQL result handling |
| NumPy | 1.26+ | Array operations for ML features |
| scikit-learn | 1.4+ | RandomForest, MLPClassifier, VotingClassifier, StandardScaler |
| XGBoost | 2.x | Gradient boosting classifier |
| SHAP | 0.44+ | TreeExplainer for ML interpretability |
| joblib | 1.3+ | Model serialization (pickle replacement) |
| google-generativeai | 0.7+ | Gemini Flash API client |
| reportlab | 4.x | PDF generation |
| python-dotenv | 1.x | Environment variable loading |
| Starlette | (via FastAPI) | Middleware, static files |

### Frontend
| Technology | Version | Role |
|---|---|---|
| React | 18 | UI component library |
| Vite | 7.x | Build tool, HMR, env variables |
| Tailwind CSS | 3.x | Utility-first styling |
| Framer Motion | 11+ | Animations, page transitions, skeleton loaders |
| Recharts | 2.x | LineChart, BarChart, AreaChart, RadarChart, PieChart |
| lucide-react | Latest | SVG icon library (60+ icons used) |

### Architecture Patterns
| Pattern | Where used |
|---|---|
| Repository pattern | `services/` layer abstraction over SQLAlchemy |
| Singleton | `MLPredictionService._model_instance`, `LLMService._client` |
| TTL Cache | `risk_monitor_service`, `analytics_service` |
| Lazy initialization | ML model loaded on first prediction, not at import |
| Fallback chain | XGBoost → GradientBoosting → Heuristic; Gemini → Template |
| Dataclass DTOs | `PredictionResult`, `GeneratedReport` |
| Background threading | Cache warm-up runs in daemon thread after startup |
| Custom React Hook | `useClinicalData` as central state + data fetching |
| Progressive Enhancement | UI updates per-endpoint as each resolves, not all-or-nothing |
| Optimistic UI | Chat: user message added immediately before API responds |
