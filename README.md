# Clinical Flow: Intelligent Clinical Trial Operational Dataflow


<img width="1917" height="924" alt="Screenshot 2026-01-31 133404" src="https://github.com/user-attachments/assets/ce0ef97c-eaed-49df-80af-671e38ce3f9b" />


## Executive Summary
**Clinical Flow** is an advanced **AI-powered Risk Surveillance Platform** engineered to solve the "Data Fragmentation" crisis in clinical trials. By unifying disparate operational logs (EDC, Safety, Lab) into a single **Knowledge Graph**, it enables real-time risk detection, predictive analytics, and autonomous problem-solving.

> **Hackathon Status**: ✅ Complete | **Architecture**: Service-Oriented | **AI**: Gemini 2.0 Pro + Ensemble ML

This platform explicitly addresses the **Problem Statements**:
1.  **Fragmented Data** $\rightarrow$ Unified via **Fuzzy Ingestion Logic** into a "Golden Record".
2.  **Reactive Monitoring** $\rightarrow$ Shifted to **Predictive Risk Modeling** using a weighted Ensemble Model.
3.  **Manual Processes** $\rightarrow$ Automated via **Agentic Copilots** that write reports and explain risks.

---

## System Architecture & Data Flow

The system uses a **Service-Repository** pattern to ensure separation of concerns and scalability.

<img width="791" height="528" alt="image" src="https://github.com/user-attachments/assets/e5901f8b-e17f-4af7-b2f4-d1e9803d611d" />

### 1. The Intelligence Layer (Backend)
*   **Framework**: FastAPI (Python 3.11) with Uvicorn.
*   **Database**: SQLite (Prototype) with SQLAlchemy ORM (migratable to PostgreSQL).
*   **Security**:
    *   **Middleware**: Custom `SecurityAuditMiddleware` for logging and header injection (`X-Frame-Options`).
    *   **RBAC**: Dependency-injected permission validation (Admin/Viewer).

### 2. The Experience Layer (Frontend)
*   **Framework**: React 18 + Vite.
*   **State Management**: Custom `useClinicalData` hook for centralized SWR-style caching.
*   **Visualization**: Recharts for high-performance time-series rendering.
*   **UX**: Fully responsive, dark-mode enabled, with Optimistic UI updates.

---

## The Machine Learning Engine

We moved beyond simple heuristics to a robust **Ensemble Architecture**.

### A. Model Architecture
Our final risk score is a **Soft Voting Classifier** combining three distinct models to maximize robustness:

$$ \text{Risk Score} = (0.45 \times P_{XGB}) + (0.35 \times P_{RF}) + (0.20 \times P_{NN}) $$

1.  **XGBoost (45%)**: Gradient Boosting for capturing complex, non-linear feature interactions (e.g., "High Enrollment" + "Low Queries").
2.  **Random Forest (35%)**: Bagging algorithim for stability against noisy/missing data.
3.  **Neural Network (20%)**: Multi-layer Perceptron for finding deep latent patterns.

### B. Feature Engineering (35+ Features)
*   **Velocity Metrics**: `SAE_Rate_Per_Month`, `Query_Resolution_Speed`.
*   **Quality Metrics**: `Missing_Page_Density`, `Protocol_Deviation_Index`.
*   **Complexity Metrics**: `Subject_Visit_Ratio`, `Form_Count`.

### C. Explainability (XAI)
We use **SHAP (Shapley Additive Explanations)** to provide "Global Interpretability". The dashboard doesn't just say "High Risk" — it says:
> *"Risk driven by **Maintenance Delay (+0.12)** and **SAE Velocity (+0.08)**"*

---

## Repository Structure

```graphql
clinical-flow/
├── backend/
│   ├── core/           # DB Config, Security Deps, Agent Setup
│   ├── services/       # Business Logic (Ingestion, ML, Analytics)
│   ├── routers/        # API Endpoints (REST)
│   ├── ml/             # Model Training, Inference, & Feature Eng.
│   └── tests/          # Pytest Suite
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable UI (Charts, Modals, Widgets)
│   │   ├── pages/      # Route Views (Overview, Risk, Reports)
│   │   ├── hooks/      # State Logic (useClinicalData)
│   │   └── lib/        # Utilities
├── docs/               # Architecture Diagrams & Screenshots
└── rules/              # Reference Data & Rulesets
```

---

## Application Deep Dive

### 1. Overview Dashboard
*The "Command Center" for study leadership, consolidating real-time data from 23 studies.*

**A. Top-Level KPIs**
*   **Study Health Score (DQI)**: A live gauge (0-100) aggregating SAE velocity, Missing Page density, and Query Latency.
*   **Patient Status**: Total Enrolled vs. Screen Failures vs. Completed.
*   **Safety Signals**: Pending SAEs requiring Medical Monitor review.
*   **Query Operations**: Open vs. Answered queries with "Average Resolution Time".
  <img width="1919" height="921" alt="Screenshot 2026-01-31 041920" src="https://github.com/user-attachments/assets/46023a15-3a6c-4d5f-91df-d8bbc32bccb5" />


**B. Advanced Visualizations**
*   **Site Risk Heatmap**: Geographic distribution of "High Risk" sites using color-coded intensity.
*   **SAE Velocity Trends**: 6-month time-series forecasting safety spikes.
*   **ML Explainability**: Feature Importance selection (e.g., "Why is Site 101 risky? -> High Protocol Deviations").
*   <img width="1917" height="990" alt="Screenshot 2026-01-31 042410" src="https://github.com/user-attachments/assets/d582183b-7b56-4b13-9ffc-e5332b7c7254" />


**C. Operational Widgets**
*   **CRA Performance**: Bar charts comparing query resolution rates per Clinical Research Associate.
*   **Lab Data Gaps**: Live list of missing Units/Ranges preventing analysis.
*   **Medical Coding**: MedDRA/WHODrug coding completion rates.
*   **Audit Trail**: "Inactivated Forms Log" tracking data deletions.
  <img width="1751" height="881" alt="Screenshot 2026-01-31 043029" src="https://github.com/user-attachments/assets/94e1e343-0349-4f1f-be92-20280dbe6f48" />


### 2. Risk Monitor
*A comprehensive surveillance grid for detailed site data.*
*   **Dual-Risk Scoring**: Displays both **Heuristic Risk** (Rule-based) and **AI Prediction** (Ensemble ML) side-by-side.
*   **Clean Patient Rate**: A visual progress bar showing the percentage of subjects at a site with **ZERO** open issues.
*   **Agentic Recommendations**: AI-suggested next actions (e.g., "Targeted SDV recommended due to high deviation count") to guide CRA workflow.
  <img width="1913" height="934" alt="Screenshot 2026-01-31 105255" src="https://github.com/user-attachments/assets/456e1bdc-8a70-444f-b97a-e17ee2fae7d5" />



### 3. Data Ingestion Pipeline
*An intelligent, drag-and-drop interface for raw operational data.*
*   **Fuzzy Logic Engine**: Automatically maps inconsistent Excel headers (e.g., "Pt_ID", "Subj#") to the canonical "Golden Record" schema using Levenshtein distance.
*   **Real-time ML Training**: Uploading new data triggers a background job (`FastAPI BackgroundTasks`) to retrain the Risk Model immediately.
*   **ACID Compliance**: Transactional integrity ensures that if any row in a batch is invalid, the entire upload is rolled back to prevent data corruption.
  <img width="1918" height="935" alt="Screenshot 2026-01-31 105819" src="https://github.com/user-attachments/assets/19608eb8-8fe5-4ea5-ab63-a9ba3a42e23a" />


### 4. Agent Copilot ("Dr. Smith")
*A RAG-powered conversational interface for instant answers.*
*   **Natural Language to SQL**: Converts questions like *"Show me sites with >5 SAEs"* into optimized database queries.
*   **Dynamic Visualization**: The Agent can render **React Charts** (Bar, Line, Pie) directly inside the chat bubble to visualize the answer.
*   **Contextual RAG**: Retrieves specific protocol constraints and past study data to answer complex compliance questions accurately.

### 5. AI Report Generator
*Automated compliance documentation and status reporting.*
*   **3 Report Types**:
    *   **Site Risk Assessment**: Deep dive into a specific site's blockers.
    *   **CRA Performance**: Resource utilization and responsiveness metrics.
    *   **Executive Summary**: High-level study health overview.
*   **GenAI Authorship**: **Google Gemini 2.0 Pro** analyzes the raw metrics to write a human-like narrative summary, highlighting key risks and trends.
*   **PDF Export**: Instant serialization of the generated report for offline sharing and audit trails.
  <img width="1919" height="918" alt="Screenshot 2026-01-31 111424" src="https://github.com/user-attachments/assets/d0d3a7de-5d76-4201-af63-f5df28ef2c80" />

---

## Getting Started

### Prerequisites
*   Python 3.10+
*   Node.js 18+

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/joeyyy09/clinical-flow.git
    cd clinical-flow
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    # Train the models
    python train_all.py
    ```

3.  **Frontend Setup**
    ```bash
    cd ../frontend
    npm install
    ```

### Running the Platform

1.  **Start the Backend API**
    ```bash
    uvicorn main:app --reload --host 127.0.0.1 --port 8000
    ```

2.  **Start the Frontend UI**
    ```bash
    npm run dev
    ```

3.  **Access**: [http://localhost:5173](http://localhost:5173)

---

## Future Roadmap

*   **Phase 1 (Hardening)**: Auth0 Integration, PostgreSQL Migration.
*   **Phase 2 (Connectivity)**: Direct API adapters for Medidata Rave / Veeva Vault.
*   **Phase 3 (Autonomy)**: "Self-Driving" Query Management (AI drafts responses for CRAs).

---

*Clinical Flow - Precision Intelligence for Clinical Excellence.*
