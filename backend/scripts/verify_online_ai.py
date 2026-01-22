
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv() # Load the .env file for this script

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_online():
    print("--- Verifying Online AI (Gemini) ---")
    
    # 1. Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY is NOT set in the environment.")
        print("   Please set it using: $env:GEMINI_API_KEY='your_key_here'")
        # Try looking in .env file manually just in case python-dotenv isn't loaded
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(dotenv_path):
            print(f"   Found .env file at: {dotenv_path}")
            with open(dotenv_path, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY"):
                        print("   (Key exists in .env file, but might not be loaded into shell)")
        return
        
    print(f"✅ GEMINI_API_KEY found: {api_key[:5]}...{api_key[-4:]}")

    # 2. Check Package
    try:
        import google.generativeai as genai
        print(f"✅ google.generativeai package version: {genai.__version__}")
    except ImportError:
        print("❌ google.generativeai package is NOT installed.")
        return

    # 3. Test Connectivity
    print("\nAttempting connection to Gemini...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello, are you online?")
        print(f"✅ Connection Successful! Response: {response.text}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_online()
