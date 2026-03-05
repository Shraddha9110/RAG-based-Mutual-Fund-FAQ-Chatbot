import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase2_indexing.chroma_manager import ChromaManager
from phase2_indexing.keyword_retriever import KeywordRetriever

class SemanticRetriever:
    def __init__(self, db_path="vector_db", collection_name="mf_faq_collection"):
        # Ensure db_path is absolute or relative to root
        if not os.path.isabs(db_path):
             db_path = os.path.join(PROJECT_ROOT, db_path)
             
        self.manager = ChromaManager(db_path=db_path, collection_name=collection_name)
        
        # Fallback: Keyword Retriever
        data_path = os.path.join(PROJECT_ROOT, 'data/funds.json')
        self.fallback = KeywordRetriever(data_path=data_path)

    def search(self, query, top_k=3):
        # 1. Try ChromaDB
        results = self.manager.query(query_texts=[query], n_results=top_k)
        
        parsed_results = []
        if results and results.get('documents') and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                parsed_results.append({
                    "text": results['documents'][0][i],
                    "source": results['metadatas'][0][i]['source'],
                    "scheme": results['metadatas'][0][i].get('scheme', 'General'),
                    "score": results['distances'][0][i] if 'distances' in results else 0
                })
        
        # 2. Fallback to Keyword Search if no results from Chroma
        if not parsed_results:
            print("Retriever: ChromaDB returned no results or is unavailable. Using Keyword fallback.")
            parsed_results = self.fallback.search(query, top_k=top_k)
            
        return parsed_results

if __name__ == "__main__":
    # Test the retriever
    retriever = SemanticRetriever()
    results = retriever.search("What is the expense ratio of SBI Large Cap?")
    for r in results:
        print(f"Match: {r['text']} | Source: {r['source']}")
