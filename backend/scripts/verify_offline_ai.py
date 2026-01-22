
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_service import LLMService

def verify_offline():
    print("--- Verifying Offline Deterministic AI ---")
    
    # 1. Initialize Service (Force Offline if needed, though script env likely lacks key)
    service = LLMService()
    # Force provider to offline just to be sure for this test
    service.provider = "offline" 
    print(f"Service Provider: {service.provider}")
    
    # 2. Test SQL Generation
    queries = [
        "Show me sites with missing lab data",
        "Which site has the most missing pages?",
        "List pending SAEs",
        "Show site performance"
    ]
    
    print("\n[SQL Generation Tests]")
    for q in queries:
        sql = service.generate_sql(q)
        print(f"Query: '{q}'\n  -> SQL: {sql}")
        
    # 3. Test Insight Generation
    print("\n[Insight Generation Test]")
    # Mock some data structure resembling DB results
    mock_data = [
        {"site_id": "101", "total_queries": 50, "resolved": 10},
        {"site_id": "102", "total_queries": 150, "resolved": 100},
        {"site_id": "103", "total_queries": 20, "resolved": 20}
    ]
    insight = service.generate_insight(mock_data, "how is performance?")
    print(f"Data: {mock_data}\n  -> Insight: {insight}")

if __name__ == "__main__":
    verify_offline()
