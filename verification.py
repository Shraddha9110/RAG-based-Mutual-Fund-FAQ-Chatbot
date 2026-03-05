from retriever import SimpleRetriever
from chatbot import MFFAQChatbot

def test_retriever():
    retriever = SimpleRetriever('data/sbi_schemes.json')
    test_cases = [
        ("What is the expense ratio of SBI Large Cap?", "SBI Large Cap Fund (Direct Plan - Growth) has expense ratio of 0.8%"),
        ("Minimum SIP for Flexicap?", "SBI Flexicap Fund (Direct Plan - Growth) has minimum SIP of ₹500"),
        ("Lock in period for SBI ELSS?", "SBI ELSS Tax Saver Fund (Direct Plan - Growth) has lock-in period of 3 Years")
    ]
    
    print("--- Testing Retriever Accuracy ---")
    for query, expected_snippet in test_cases:
        results = retriever.search(query, top_k=1)
        if results and expected_snippet.lower() in results[0]['text'].lower():
            print(f"[PASS] Query: {query}")
        else:
            print(f"[FAIL] Query: {query} | Got: {results[0]['text'] if results else 'None'}")

def test_guardrails():
    bot = MFFAQChatbot('data/sbi_schemes.json')
    print("\n--- Testing Guardrails (Mock) ---")
    
    # Test case 1: Specific fact with source
    query = "What is the benchmark for SBI ELSS?"
    context, sources = bot.get_context(query)
    if sources and "https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth-2754" in sources[0]:
        print(f"[PASS] Source inclusion for: {query}")
    else:
        print(f"[FAIL] Source missing for: {query}")

    # Test case 2: No Advice Policy check (contextual search should yield results, bot should handle advice)
    query = "Should I invest in SBI Large Cap?"
    context, sources = bot.get_context(query)
    # The retriever should find facts, but the system prompt is responsible for the actual "advice" guardrail.
    # Here we just verify that context is found for the scheme even if it is an advice query.
    if any("SBI Large Cap" in s for s in sources):
        print(f"[PASS] Context found for Advice Query: {query}")
    else:
        print(f"[FAIL] Context NOT found for Scheme Mention: {query}")

if __name__ == "__main__":
    test_retriever()
    test_guardrails()
