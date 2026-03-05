from chatbot import MFFAQChatbot

def test_bot():
    bot = MFFAQChatbot('data/funds.json')
    
    test_queries = [
        "What is the NAV of HDFC Flexi Cap?",
        "What is the portfolio turnover of SBI Flexicap Fund?",
        "Tell me about the lock-in period of Sundaram ELSS.",
        "How to download SBI Capital Gains statement?",
        "Should I invest in SBI Small Cap Fund?", # Advice rejection
        "Which is the best fund for me?" # Advice rejection
    ]
    
    for q in test_queries:
        print(f"Query: {q}")
        response, source = bot.generate_response_dummy(q)
        print(f"Response:\n{response}")
        print("-" * 30)

if __name__ == "__main__":
    test_bot()
