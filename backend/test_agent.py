from agent import ClinicalAgent
from dotenv import load_dotenv

load_dotenv()

# Initialize Agent
agent = ClinicalAgent()

# Test 1: Fallback / Mock Mode (unless Key is present)
print("\n--- Test 1: General Query ---")
response = agent.query("Show me missing pages count by site")
print(response['answer'])
print("SQL:", response.get('sql'))

# Test 2: Heuristic Insight
print("\n--- Test 2: SAE Analysis ---")
response = agent.query("Are there any pending SAEs?")
print(response['answer'])

print("\n--- Test 3: Unknown Topic ---")
response = agent.query("What is the weather?")
print(response['answer'])
