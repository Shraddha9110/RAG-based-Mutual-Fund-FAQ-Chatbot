import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase2_indexing.retriever import SemanticRetriever

class TestPhase2Indexing(unittest.TestCase):
    @patch('phase2_indexing.retriever.ChromaManager')
    def test_semantic_retrieval_logic(self, mock_manager_class):
        # Mock manager query
        mock_manager = mock_manager_class.return_value
        mock_manager.query.return_value = {
            'documents': [['SBI Large Cap NAV is 104.23']],
            'metadatas': [[{'source': 'https://example.com', 'scheme': 'SBI Large Cap'}]],
            'distances': [[0.1]]
        }
        
        retriever = SemanticRetriever()
        results = retriever.search("What is the NAV of SBI Large Cap?")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['scheme'], 'SBI Large Cap')
        self.assertIn("104.23", results[0]['text'])
        self.assertEqual(results[0]['source'], 'https://example.com')

if __name__ == "__main__":
    unittest.main()
