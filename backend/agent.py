
import os
import pandas as pd
from sqlalchemy import create_engine
from typing import List

# Simple Agentic wrapper
# In a real scenario, we would use LangChain's SQLDatabaseChain or PandasDataFrameAgent

class ClinicalAgent:
    def __init__(self, db_path="sqlite:///./clinical_trials.db"):
        self.engine = create_engine(db_path)
    
    def query(self, user_query: str):
        user_query = user_query.lower()
        
        # Primitive implementation of "intent recognition"
        if "missing pages" in user_query:
            return self.analyze_missing_pages()
        elif "sae" in user_query or "adverse events" in user_query:
            return self.analyze_sae()
        elif "count" in user_query or "summary" in user_query:
            return self.get_summary()
        elif "underperforming" in user_query or "worst sites" in user_query or "risk" in user_query:
            return self.identify_underperformers()
        else:
            return {
                "answer": "I can help with: Missing Pages analysis, SAE metrics, Study Summaries, and identifying Underperforming Sites. Try asking 'Which sites are underperforming?'",
                "data": []
            }

    def analyze_missing_pages(self):
        df = pd.read_sql("SELECT * FROM missing_pages", self.engine)
        if df.empty:
             return {"answer": "No missing pages data found.", "data": []}
             
        # Generate some insights
        top_site = df['site_number'].value_counts().idxmax()
        total_missing = df.shape[0]
        avg_days = df['missing_days'].mean()
        
        insight = f"There are {total_missing} missing pages recorded. Site {top_site} has the highest number of missing pages. The average delay is {avg_days:.1f} days."
        
        return {
            "answer": insight,
            "data": df.head(10).to_dict(orient="records"),
            "chart_type": "bar",
            "chart_data": df['site_number'].value_counts().head(5).to_dict()
        }

    def analyze_sae(self):
        df = pd.read_sql("SELECT * FROM sae_metrics", self.engine)
        if df.empty:
            return {"answer": "No SAE data found.", "data": []}
            
        pending_review = df[df['review_status'] != 'Reviewed'].shape[0]
        total = df.shape[0]
        
        insight = f"Total SAEs recorded: {total}. There are {pending_review} SAEs pending review."
        
        return {
            "answer": insight,
            "data": df.head(10).to_dict(orient="records"),
            "chart_type": "pie",
            "chart_data": df['review_status'].value_counts().to_dict()
        }

    def get_summary(self):
        # Count entries in each table
        with self.engine.connect() as conn:
            sae_count = pd.read_sql("SELECT count(*) FROM sae_metrics", conn).iloc[0,0]
            missing_count = pd.read_sql("SELECT count(*) FROM missing_pages", conn).iloc[0,0]
            edc_count = pd.read_sql("SELECT count(*) FROM edc_metrics", conn).iloc[0,0]
            
        insight = f"Database Summary: {sae_count} SAE records, {missing_count} Missing Page records, {edc_count} EDC metrics records."
        
        return {
            "answer": insight,
            "data": [
                {"Metric": "SAE Records", "Value": int(sae_count)},
                {"Metric": "Missing Pages", "Value": int(missing_count)},
                {"Metric": "EDC Metrics", "Value": int(edc_count)}
            ]
        }

    def identify_underperformers(self):
        # Join logic to find sites with high missing pages or high SAEs
        df = pd.read_sql("""
            SELECT site_number, count(*) as missing_cnt 
            FROM missing_pages 
            GROUP BY site_number 
            ORDER BY missing_cnt DESC 
            LIMIT 5
        """, self.engine)
        
        if df.empty:
             return {"answer": "No underperforming sites detected based on current data.", "data": []}
             
        sites = df['site_number'].tolist()
        counts = df['missing_cnt'].tolist()
        
        insight = f"The top 5 underperforming sites based on Missing Data Volume are: {', '.join(sites)}. Site {sites[0]} is critical with {counts[0]} missing pages."
        
        return {
            "answer": insight,
            "data": df.to_dict(orient="records"),
            "chart_type": "bar",
            "chart_data": dict(zip(sites, counts))
        }
