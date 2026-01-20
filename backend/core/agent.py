import traceback
import pandas as pd
from sqlalchemy import create_engine
from .llm_service import LLMService

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
        Provides a high-level summary of the clinical trial data.
        
        Returns:
            dict: The result of a general summary query.
        """
        # Fallback to simple summary if needed
        return self.query("summarize the count of all records")
