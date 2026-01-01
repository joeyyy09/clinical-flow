
import os
import pandas as pd
import traceback
from sqlalchemy import create_engine
from llm_service import LLMService

class ClinicalAgent:
    def __init__(self, db_path="sqlite:///./clinical_trials.db"):
        self.engine = create_engine(db_path)
        self.llm = LLMService()
    
    def query(self, user_query: str):
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
        # Fallback to simple summary if needed
        return self.query("summarize the count of all records")
