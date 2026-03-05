import os
import sys
import re
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# Add project root to path to allow absolute imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase2_indexing.retriever import SemanticRetriever

load_dotenv()

class MFFAQChatbot:
    def __init__(self, db_path='vector_db'):
        self.retriever = SemanticRetriever(db_path=db_path)
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY", "your_groq_api_key_here"))
        
        self.system_prompt = """
You are a helpful and factual Mutual Fund FAQ Assistant.
Your goal is to answer questions about specific mutual fund facts like expense ratio, exit load, NAV, turnover, minimum SIP, lock-in period, riskometer, benchmark, and returns.

ANSWER FORMAT EXAMPLES:
- For NAV queries: "The NAV of [Fund Name] today is [NAV Value]. NAV or Net Asset Value is the per unit price of a mutual fund. For example, if the NAV of a fund is ₹10, it means you can get 1000 units of that mutual fund at ₹10,000."
- For Return queries: "[Fund Name] has generated a return of [1Y]% in 1 year, [3Y]% in 3 years, [5Y]% in 5 years."

STRICT POLICIES:
1. RAG-ONLY: ONLY use the provided context to answer. If the information is not in the context, say "I am sorry, but I do NOT have that info in my records."
2. CONCISE: Max 3 sentences per answer.
3. TRANSPARENCY: Every answer must include exactly ONE source link from the context at the end.
4. ADVICE/PERFORMANCE: Reject requests for advice or "best fund" performance comparisons. Suggest consulting a financial advisor or the official SEBI portal: https://www.sebi.gov.in/investor-education.html
5. PII: NEVER accept or store PAN, Aadhaar, account numbers, etc. If detected, reject immediately.
6. FOOTER: Every response must end with 'Last updated from sources: [Current Date]'.
"""

    def get_context(self, query):
        results = self.retriever.search(query, top_k=2)
        if not results:
            return "No relevant facts found.", []
        
        context_str = "\n".join([f"- {r['text']} (Source: {r['source']})" for r in results])
        sources = [r['source'] for r in results]
        return context_str, sources

    def generate_response(self, query):
        # 1. PII Detection (Basic)
        pii_patterns = [
            r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', # PAN
            r'\b[0-9]{12}\b',                # Aadhaar
            r'\b[0-9]{10}\b',                # Phone
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' # Email
        ]
        if any(re.search(pattern, query) for pattern in pii_patterns):
            return "I cannot process personal information like PAN, Aadhaar, or contact details. Please do not share sensitive data.", None

        # 2. Performance/Advice Rejection (Heuristic before LLM)
        advice_keywords = ["best fund", "should i invest", "give me advice", "top performers", "highest return"]
        if any(kw in query.lower() for kw in advice_keywords):
            return "I can only provide factual information about fund characteristics. For performance comparisons or investment advice, please consult a SEBI-registered financial advisor. Learn more: https://www.sebi.gov.in/investor-education.html", "https://www.sebi.gov.in/investor-education.html"

        # 3. RAG Retrieval
        context, sources = self.get_context(query)
        
        # 4. LLM Call
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0,
            )
            answer = chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}", None

        # Post-processing: Append Footer
        footer = f"\n\nLast updated from sources: {datetime.now().strftime('%Y-%m-%d')}"
        if not any(footer in answer for footer in [footer]): # Simple check
             answer += footer
             
        source = sources[0] if sources else None
        return answer, source

if __name__ == "__main__":
    bot = MFFAQChatbot()
    ans, src = bot.generate_response("What is the NAV of SBI Large Cap?")
    print(f"Response:\n{ans}\nSource: {src}")
