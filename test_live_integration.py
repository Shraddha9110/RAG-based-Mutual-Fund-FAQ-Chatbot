import os
import sys
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase3.chatbot_logic import MFFAQChatbot
from unittest.mock import patch

load_dotenv()

def test_live_llm_integration():
    print("--- Starting Live LLM Integration Test ---")
    
    # We mock the search to return a specific fact, so we can verify if the LLM uses it correctly.
    # This bypasses the sqlite3 issue while testing the LIVE Groq API.
    mock_fact = {
        "text": "SBI Large Cap Fund (Direct Plan - Growth) has an expense ratio of 0.8%.",
        "source": "https://www.indmoney.com/mutual-funds/sbi-large-cap-fund-direct-growth-3046",
        "scheme": "SBI Large Cap Fund"
    }

    with patch('phase3.chatbot_logic.SemanticRetriever.search') as mock_search:
        mock_search.return_value = [mock_fact]
        
        bot = MFFAQChatbot()
        query = "What is the expense ratio of SBI Large Cap?"
        
        print(f"Query: {query}")
        response, source = bot.generate_response(query)
        
        print("\n--- LLM Response ---")
        print(response)
        print(f"Source: {source}")
        print("--------------------")

        # Basic assertions
        if "0.8%" in response and source == mock_fact["source"]:
            print("[PASS] LLM correctly used the retrieved context and source.")
        else:
            print("[FAIL] LLM response did not match expected context or source.")

        if "Last updated from sources:" in response:
            print("[PASS] Footer present.")
        else:
            print("[FAIL] Footer missing.")

def test_live_guardrails():
    print("\n--- Starting Live Guardrail Test (PII & Advice) ---")
    bot = MFFAQChatbot()
    
    # Test PII
    pii_query = "My PAN is ABCDE1234F"
    print(f"Query: {pii_query}")
    response, _ = bot.generate_response(pii_query)
    print(f"Response: {response}")
    if "cannot process personal information" in response.lower():
        print("[PASS] PII guardrail triggered.")
    else:
        print("[FAIL] PII guardrail failed.")

    # Test Advice
    advice_query = "Recommend the best fund for 20% returns"
    print(f"Query: {advice_query}")
    response, _ = bot.generate_response(advice_query)
    print(f"Response: {response}")
    if "only provide factual information" in response.lower():
        print("[PASS] Advice guardrail triggered.")
    else:
        print("[FAIL] Advice guardrail failed.")

if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env. Please add it to run live tests.")
    else:
        test_live_llm_integration()
        test_live_guardrails()
