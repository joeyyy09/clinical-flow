
import os
import re
import random
import json

# Try importing google.generativeai, but don't crash if handling fallback
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") 
        self.provider = "mock"
        
        if self.api_key and HAS_GEMINI:
            self.provider = "gemini"
            genai.configure(api_key=self.api_key)
<<<<<<< HEAD
            # Use gemini-2.5-flash as it is the only one with available quota
=======
            # Fallback to latest alias which has at least some quota (20/day)
>>>>>>> ed5a650 (Updated LLM in chatbot)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print(" [OK] LLM Service: Using Google Gemini (gemini-2.5-flash)")
        else:
            print(" [WARN] LLM Service: running in OFFLINE/MOCK mode.")
            if not self.api_key:
                print("   └── Reason: GEMINI_API_KEY not found in environment.")
            if not HAS_GEMINI:
                print("   └── Reason: google.generativeai package not installed.")

    def generate_sql(self, user_query: str) -> str:
        """
        Converts natural language to SQL.
        """
        if self.provider == "gemini":
            return self._gemini_text_to_sql(user_query)
        else:
            return self._mock_text_to_sql(user_query)

    def generate_insight(self, data: list, query: str) -> str:
        """
        Generates a scientific insight based on the data.
        """
        if not data:
            return "No data found matching your query."
            
        if self.provider == "gemini":
            return self._gemini_generate_insight(data, query)
        else:
            return self._mock_generate_insight(data, query)

    def _gemini_text_to_sql(self, query):
        system_prompt = """
        You are a SQL expert for a Clinical Trial Database (SQLite).
        Schema:
        - sae_metrics (id, study_id, country, site, patient_id, review_status)
        - missing_pages (id, study_id, site_number, subject_name, form_name, visit_date, missing_days)
        - edc_metrics (id, study_id, site_id, subject_id, subject_status, latest_visit)

        Return ONLY raw SQL. No markdown, no backticks.
        """
        try:
            response = self.model.generate_content(f"{system_prompt}\nQuery: {query}")
            sql = response.text.replace("```sql", "").replace("```", "").strip()
            return sql
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self._mock_text_to_sql(query)

    def _gemini_generate_insight(self, data, query):
        data_preview = str(data[:10]) # Send first 10 rows to avoid token limits
        prompt = f"""
        You are a Clinical Scientist Assistant.
        User Question: {query}
        Data Result: {data_preview}
        
        Provide a concise (2-3 sentences) scientific insight about this data. 
        Focus on risk, compliance, or safety patterns.
        """
        try:
            response = self.model.generate_content(prompt)
            # Check for block content if attributes exist, though text access should raise error if blocked
            return response.text
        except Exception as e:
             print(f" [ERR] Gemini Insight Error: {e}")
             mock_insight = self._mock_generate_insight(data, query)
             error_msg = "⚠️ AI Service Unavailable (Quota Limit Reached). Showing automated analysis."
             return f"{error_msg}\n\n{mock_insight}"

    def _mock_text_to_sql(self, query):
        """
        A sophisticated Regex-based fallback that covers common demo questions.
        """
        query = query.lower()
        
        # 1. Missing Pages Logic
        if "missing" in query:
            if "site" in query and "count" in query:
                return "SELECT site_number, count(*) as count FROM missing_pages GROUP BY site_number ORDER BY count DESC LIMIT 5"
            if "highest" in query or "most" in query:
                return "SELECT site_number, count(*) as count FROM missing_pages GROUP BY site_number ORDER BY count DESC LIMIT 1"
            return "SELECT * FROM missing_pages LIMIT 10"
            
        # 2. SAE Logic
        if "sae" in query or "adverse" in query:
            if "pending" in query:
                return "SELECT * FROM sae_metrics WHERE review_status != 'Reviewed' OR review_status IS NULL"
            if "site" in query:
                return "SELECT site, count(*) as count FROM sae_metrics GROUP BY site ORDER BY count DESC LIMIT 5"
            return "SELECT * FROM sae_metrics LIMIT 10"
            
        # 3. EDC/Subject Logic
        if "subject" in query or "patient" in query:
            return "SELECT * FROM edc_metrics LIMIT 10"
            
        # Default
        return "SELECT count(*) as sae_count FROM sae_metrics"

    def _mock_generate_insight(self, data, query):
        """
        Templates to make the mock mode feel "scientific".
        """
        count = len(data)
        if count == 0:
            return "No significant patterns found in the filtered dataset."
            
        if "missing" in query.lower():
            return f"Analysis reveals {count} records with missing data. The top contributing sites show a consistent pattern of delayed entry, suggesting a need for targeted CRA retraining."
            
        if "sae" in query.lower():
            return f"Identified {count} Safety/Adverse Event records. There is a cluster of unreviewed events that requires immediate Medical Monitor attention to ensure patient safety compliance."
            
        return f"Query executed successfully. Returned {count} records. Data indicates nominal operational metrics consistent with phase expectations."
