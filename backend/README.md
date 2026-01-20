# Backend Documentation: Clinical Trial Insights

This folder contains the core logic, API, and AI agent for the Clinical Trial Insights platform. The backend is built with FastAPI and uses SQLAlchemy for database management.

## Core Components

### 1. API Layer (`main.py`)
- **FastAPI**: Serves the REST API.
- **Routes**: Includes endpoints for data ingestion, chat, analytics, and report generation.
- **CORS**: Configured to allow communication with the frontend dev server.

### 2. AI Intelligence (`agent.py` & `llm_service.py`)
- **ClinicalAgent**: The high-level orchestrator that takes natural language queries, converts them to SQL, and generates scientific insights.
- **LLMService**: Handles the direct integration with Google Gemini (via `google-generativeai`). It manages prompts and fallbacks to mock analysis if the API is unavailable.

### 3. Data Processing (`ingestion.py` & `analytics.py`)
- **Ingestion**: A pipeline that scans for clinical trial data (Excel files) and normalizes them into the database.
- **Analytics**: Contains heuristic scoring models (Health Score, DQI) and data aggregation logic for the dashboard and risk monitor.

### 4. Database (`database.py` & `models.py`)
- **SQLite**: Used for data storage.
- **Models**: Defines schemas for SAE Metrics, Missing Pages, EDC Metrics, and Site Comments.

## Data Ingestion Flow

1. Files are scanned in the `data/` and `uploads/` directories.
2. Excel files are identified by name patterns (e.g., "SAE Dashboard", "EDC_Metrics").
3. Columns are normalized and mapped to the database schema.
4. Data is persisted to `clinical_trials.db`.

## Key Logic
- **Risk Heatmap**: Aggregates missing records by site.
- **DQI (Data Quality Index)**: A weighted metric based on missingness, safety reporting, and query latency.
- **AI Chat**: Uses LLM-generated SQL to ensure the chatbot is grounded in real database facts.
