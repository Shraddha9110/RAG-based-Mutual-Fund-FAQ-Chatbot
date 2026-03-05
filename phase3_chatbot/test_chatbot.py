import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase3_chatbot.chatbot import MFFAQChatbot

class TestMFFAQChatbot(unittest.TestCase):
    def setUp(self):
        # Mock retriever to avoid DB dependency in logic tests
        self.patcher = patch('phase3_chatbot.chatbot.SemanticRetriever')
        self.mock_retriever_class = self.patcher.start()
        self.mock_retriever = self.mock_retriever_class.return_value
        
        # Mock Groq client
        self.groq_patcher = patch('phase3_chatbot.chatbot.Groq')
        self.mock_groq_class = self.groq_patcher.start()
        self.mock_groq = self.mock_groq_class.return_value
        
        self.bot = MFFAQChatbot()

    def tearDown(self):
        self.patcher.stop()
        self.groq_patcher.stop()

    def test_pii_rejection(self):
        query = "My PAN is ABCDE1234F"
        response, source = self.bot.generate_response(query)
        self.assertIn("cannot process personal information", response)
        self.assertIsNone(source)

    def test_advice_rejection(self):
        query = "Which is the best fund for me?"
        response, source = self.bot.generate_response(query)
        self.assertIn("only provide factual information", response)
        self.assertIn("sebi.gov.in", response)

    def test_rag_logic_mock(self):
        # Mock retriever response
        self.mock_retriever.search.return_value = [
            {"text": "SBI Large Cap NAV is 104.23", "source": "https://example.com", "scheme": "SBI Large Cap"}
        ]
        
        # Mock Groq response
        mock_msg = MagicMock()
        mock_msg.content = "The NAV of SBI Large Cap is 104.23 according to the records."
        self.mock_groq.chat.completions.create.return_value.choices = [MagicMock(message=mock_msg)]
        
        query = "What is the NAV of SBI Large Cap?"
        response, source = self.bot.generate_response(query)
        
        self.assertIn("104.23", response)
        self.assertEqual(source, "https://example.com")
        self.assertIn("Last updated from sources:", response)

if __name__ == "__main__":
    unittest.main()
