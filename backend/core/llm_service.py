
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
        self.provider = "offline" 
        
        if self.api_key and HAS_GEMINI:
            self.provider = "gemini"
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print(" [OK] LLM Service: Using Google Gemini (gemini-2.5-flash)")
        else:
            print(" [INFO] LLM Service: Running in DETERMINISTIC OFFLINE MODE.")

    def generate_sql(self, user_query: str) -> str:
        """
        Converts a natural language query into a valid SQL query.
        """
        if self.provider == "gemini":
            return self._gemini_text_to_sql(user_query)
        else:
            return self._deterministic_text_to_sql(user_query)

    def generate_insight(self, data: list, query: str) -> str:
        """
        Generates a concise scientific insight.
        """
        if not data:
            return "No data found matching your query."
            
        if self.provider == "gemini":
            return self._gemini_generate_insight(data, query)
        else:
            return self._calculated_insight(data, query)

    def _deterministic_text_to_sql(self, query):
        """
        Rule-based SQL generation for offline mode.
        """
        q = query.lower()
        
        # 1. Missing Lab Data
        if "lab" in q and ("missing" in q or "gap" in q):
            return "SELECT site_number, test_name, issue FROM missing_lab_data LIMIT 10"

        # 2. Missing Pages
        if "missing" in q and "page" in q:
            if "site" in q:
                return "SELECT site_number, count(*) as count FROM missing_pages GROUP BY site_number ORDER BY count DESC LIMIT 5"
            return "SELECT * FROM missing_pages ORDER BY missing_days DESC LIMIT 10"
            
        # 3. SAE / Adverse Events
        if "sae" in q or "adverse" in q:
            if "unreviewed" in q or "pending" in q:
                return "SELECT * FROM sae_metrics WHERE review_status != 'Reviewed'"
            return "SELECT study_id, site, case_status FROM sae_metrics LIMIT 10"
            
        # 4. Sites / Performance / Deviations
        if "deviation" in q:
            return "SELECT site_id, protocol_deviations FROM edc_metrics ORDER BY protocol_deviations DESC LIMIT 10"

        if "site" in q or "performance" in q:
            return "SELECT site_id, total_queries, queries_resolved FROM edc_metrics ORDER BY total_queries DESC LIMIT 10"

        # Default fallback
        return "SELECT * FROM edc_metrics LIMIT 5"

    def _calculated_insight(self, data, query):
        """
        Generates a data-driven summary without using an LLM.
        """
        try:
            count = len(data)
            if count == 0: 
                return "No records found."
                
            # Try to identify numerical columns to aggregate
            first_row = data[0] if isinstance(data[0], dict) else data[0].__dict__
            
            # Helper to find numeric keys
            numeric_keys = [k for k, v in first_row.items() if isinstance(v, (int, float)) and not k.endswith('id')]
            
            summary = f"Analysis Complete. Found {count} records."
            
            if numeric_keys:
                key = numeric_keys[0] # Pick first metric
                total = sum(d[key] for d in data if isinstance(d, dict)) # Dict access
                avg = total / count
                summary += f" Average '{key}' is {avg:.1f}."
                
                # Find max
                max_val = max(d[key] for d in data if isinstance(d, dict))
                summary += f" Maximum observed value is {max_val}."
            else:
                summary += " Data contains primarily qualitative fields."
                
            summary += " (Generated via Offline Deterministic Engine)"
            return summary
            
        except Exception as e:
            return f"Data retrieved successfully ({len(data)} records). Stats calculation unavailable."

    def _gemini_text_to_sql(self, query):
        system_prompt = """
        You are a SQL expert for a Clinical Trial Database (SQLite).
        Schema:
        - sae_metrics (id, study_id, country, site, patient_id, review_status, case_status)
        - missing_pages (id, study_id, site_number, subject_name, form_name, visit_date, missing_days)
        - edc_metrics (id, study_id, site_id, subject_id, subject_status, latest_visit, total_queries, queries_resolved, protocol_deviations)
        - missing_lab_data (id, study_id, site_number, test_name, issue, lab_category)
        - visit_projection (id, study_id, site, subject, days_outstanding)

        Return ONLY raw SQL. No markdown, no backticks.
        """
        try:
            response = self.model.generate_content(f"{system_prompt}\nQuery: {query}")
            sql = response.text.replace("```sql", "").replace("```", "").strip()
            return sql
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "Error: Gemini API Unreachable"

    def _gemini_generate_insight(self, data, query):
        # 1. Calculate Stats locally (Smart Calculation)
        count = len(data)
        stats_summary = f"Total Records: {count}."
        
        try:
            if count > 0 and isinstance(data[0], dict):
                first = data[0]
                # Find numeric keys (simple heuristic)
                numerics = [k for k,v in first.items() if isinstance(v, (int, float)) and not k.endswith('id')]
                if numerics:
                    key = numerics[0]
                    vals = [d[key] for d in data if d.get(key) is not None]
                    if vals:
                        avg_val = sum(vals) / len(vals)
                        max_val = max(vals)
                        stats_summary += f" Average '{key}': {avg_val:.1f}. Max '{key}': {max_val}."
        except:
            pass # Fallback to just count

        data_preview = str(data[:10]) # Send first 10 rows to avoid token limits
        prompt = f"""
        You are a Clinical Scientist Assistant compliant with ICH-GCP.
        User Question: {query}
        
        Real-time Calculations:
        {stats_summary}
        
        Data Preview (First 10 rows): 
        {data_preview}
        
        INSTRUCTIONS:
        1. Answer based ONLY on the provided Data and Calculations. Do NOT invent data.
        2. If you interpret a code (e.g., 'UPHST'), YOU MUST include the original code in parentheses (e.g., "Urinalysis (UPHST)").
        3. If the data is empty or inconclusive, state that clearly.
        4. Focus on risk, compliance, or safety patterns.
        
        Provide a concise (2-3 sentences) scientific insight.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
             print(f" [ERR] Gemini Insight Error: {e}")
             return "Error: Gemini Insight Generation Failed"
