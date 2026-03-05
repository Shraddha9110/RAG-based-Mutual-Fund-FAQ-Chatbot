import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase3.chatbot_logic import MFFAQChatbot

class TestPhase3Chatbot(unittest.TestCase):
    def setUp(self):
        # Mock retriever to avoid DB dependency
        self.patcher = patch('phase3.chatbot_logic.SemanticRetriever')
        self.mock_retriever_class = self.patcher.start()
        self.mock_retriever = self.mock_retriever_class.return_value
        
        # Mock Groq client
        self.groq_patcher = patch('phase3.chatbot_logic.Groq')
        self.mock_groq_class = self.groq_patcher.start()
        self.mock_groq = self.mock_groq_class.return_value
        
        self.bot = MFFAQChatbot()

    def tearDown(self):
        self.patcher.stop()
        self.groq_patcher.stop()

    def test_pii_filtering(self):
        query = "Reset my password for email test@example.com"
        response, source = self.bot.generate_response(query)
        self.assertIn("cannot process personal information", response)
        self.assertIsNone(source)

    def test_advice_filtering(self):
        query = "Recommend the best mutual fund for 10% returns"
        response, source = self.bot.generate_response(query)
        self.assertIn("only provide factual information", response)
        self.assertIn("sebi.gov.in", response)

    def test_rag_compliance_mock(self):
        # Mocking factual context retrieval
        self.mock_retriever.search.return_value = [
            {"text": "SBI Flexicap Fund has NAV of 121.93.", "source": "https://example.com/sbi", "scheme": "SBI Flexicap"}
        ]
        
        # Mock LLM generation
        mock_msg = MagicMock()
        mock_msg.content = "SBI Flexicap Fund has an NAV of 121.93. Refer to the source for more details."
        self.mock_groq.chat.completions.create.return_value.choices = [MagicMock(message=mock_msg)]
        
        query = "What is the NAV of SBI Flexicap?"
        response, source = self.bot.generate_response(query)
        
        self.assertIn("121.93", response)
        self.assertEqual(source, "https://example.com/sbi")
        self.assertIn("Last updated from sources:", response)

if __name__ == "__main__":
    unittest.main()
