try:
    import chromadb
except RuntimeError as e:
    if "sqlite3" in str(e):
        print(f"Warning: ChromaDB import failed due to sqlite3 version: {e}")
        chromadb = None
    else:
        raise e
except ImportError:
    chromadb = None
import os

class ChromaManager:
    def __init__(self, db_path="vector_db", collection_name="mf_faq_collection"):
        self.db_path = db_path
        self.collection_name = collection_name
        if chromadb:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        else:
            self.client = None
            self.collection = None

    def add_documents(self, documents, metadatas, ids):
        if self.collection:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        else:
            print("ChromaDB not initialized. Documents not added.")

    def query(self, query_texts, n_results=3):
        if self.collection:
            return self.collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
        return None

    def get_collection_count(self):
        return self.collection.count() if self.collection else 0
