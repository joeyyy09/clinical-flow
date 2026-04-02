import traceback
import time
import pandas as pd
from sqlalchemy import create_engine, text
from .llm_service import LLMService
from .database import SessionLocal

# Simple TTL cache for get_summary — avoids re-querying on every page load
_summary_cache: dict = {}
_SUMMARY_CACHE_TTL = 300  # 5 minutes

class ClinicalAgent:
    """
    An AI-powered agent designed to analyze clinical trial data.
    
    This agent combines SQL generation and scientific insight generation 
    using a Large Language Model (LLM) to answer natural language queries 
    about clinical trial datasets.
    """
    def __init__(self, db_path="sqlite:///./clinical_trials.db"):
        """
        Initializes the ClinicalAgent with a database connection and LLM service.
        
        Args:
            db_path (str): The SQLAlchemy-compatible connection string for the database.
        """
        self.engine = create_engine(db_path)
        self.llm = LLMService()
    
    def query(self, user_query: str):
        """
        Processes a natural language query from the user.
        
        The process involves:
        1. Generating a SQL query from the natural language input.
        2. Executing the generated SQL against the database.
        3. Using the LLM to generate scientific insights based on the retrieved data.
        4. (Optional) Generating a visualization configuration if the data is suitable.
        
        Args:
            user_query (str): The natural language question or command from the user.
            
        Returns:
            dict: A dictionary containing the answer (insight), data records, 
                  chart configuration, and the generated SQL.
        """
        print(f"🤖 User Query: {user_query}")
        
        # 1. Generate SQL
        sql_query = self.llm.generate_sql(user_query)
        print(f"📝 Generated SQL: {sql_query}")
        
        try:
            # 2. Execute SQL
            with self.engine.connect() as conn:
                df = pd.read_sql(sql_query, conn)
                
            if df.empty:
                 return {
                    "answer": "Analysis complete. No matching records were found in the current dataset.",
                    "data": [],
                    "sql": sql_query
                }
            
            # 3. Generate Scientific Insight
            data_records = df.head(10).to_dict(orient="records")
            insight = self.llm.generate_insight(data_records, user_query)
            
            # 4. Generate Visualization Config (Heuristic for now)
            chart_type = None
            chart_data = None
            
            # If the result has 'count' and multiple rows, it's likely a bar/pie chart
            if 'count' in df.columns or df.shape[1] == 2:
                if df.shape[0] > 1:
                    chart_type = 'bar'
                    # Assume first column is category, second is value
                    label_col = df.columns[0]
                    value_col = df.columns[1]
                    chart_data = dict(zip(df[label_col].astype(str), df[value_col]))

            return {
                "answer": insight,
                "data": data_records,
                "chart_type": chart_type,
                "chart_data": chart_data,
                "sql": sql_query
            }
            
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            print(f"❌ SQL: {sql_query}")
            traceback.print_exc()
            return {
                "answer": f"I attempted to analyze the data but encountered a query error. \n\nGenerated SQL: `{sql_query}` \n\nError: {str(e)}",
                "data": []
            }

    def get_summary(self):
        """
        Provides a high-level summary of the clinical trial data for the dashboard.
        Returns strict format for frontend: [ {Metric: name, Value: count}, ... ]
        Cached for 5 minutes to avoid repeated DB scans on every page load.
        """
        cached = _summary_cache.get('summary')
        if cached and (time.time() - cached['ts']) < _SUMMARY_CACHE_TTL:
            return cached['data']

        try:
            # Use the shared session pool instead of a separate engine
            db = SessionLocal()
            try:
                subject_count = db.execute(text(
                    "SELECT COUNT(DISTINCT subject_id) FROM edc_metrics"
                )).scalar() or 0

                edc_missing = db.execute(text(
                    "SELECT COALESCE(SUM(missing_pages), 0) FROM edc_metrics"
                )).scalar() or 0

                global_missing = db.execute(text(
                    "SELECT COALESCE(SUM(missing_days), 0) FROM missing_pages"
                )).scalar() or 0

                edc_sae = db.execute(text(
                    "SELECT COALESCE(SUM(esae_review_dm + esae_review_safety), 0) FROM edc_metrics"
                )).scalar() or 0

                global_sae = db.execute(text(
                    "SELECT COUNT(*) FROM sae_metrics"
                )).scalar() or 0
            finally:
                db.close()

            result = {
                "answer": "Dashboard data loaded.",
                "data": [
                    {"Metric": "SAE Records",   "Value": int(max(edc_sae, global_sae))},
                    {"Metric": "Missing Pages", "Value": int(max(edc_missing, global_missing))},
                    {"Metric": "EDC Metrics",   "Value": int(subject_count)}
                ]
            }
            _summary_cache['summary'] = {'ts': time.time(), 'data': result}
            return result
        except Exception as e:
            print(f"Summary Error: {e}")
            return {"answer": "Error loading metrics", "data": []}
