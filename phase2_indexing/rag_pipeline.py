import sys
import os
import json

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase2_indexing.chroma_manager import ChromaManager

def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def create_chunks(data):
    chunks = []
    metadata = []
    ids = []
    
    for i, scheme in enumerate(data):
        base_name = scheme['scheme_name']
        source_url = scheme['url']
        
        fields = {
            "expense ratio": scheme.get('expense_ratio'),
            "exit load": scheme.get('exit_load'),
            "minimum SIP": scheme.get('min_sip'),
            "minimum lumpsum": scheme.get('min_lumpsum'),
            "lock-in period": scheme.get('lock_in'),
            "riskometer rating": scheme.get('risk'),
            "benchmark": scheme.get('benchmark'),
            "AUM": scheme.get('aum'),
            "NAV": scheme.get('nav'),
            "Portfolio Turnover": scheme.get('turnover')
        }
        
        for field_name, value in fields.items():
            if value and value != "N/A":
                content = f"The {field_name} of {base_name} is {value}."
                chunks.append(content)
                metadata.append({"source": source_url, "scheme": base_name, "type": field_name})
                ids.append(f"id_{i}_{field_name.replace(' ', '_')}")

    statement_info = [
        {
            "text": "To download your Capital Gains statement for SBI Mutual Fund: 1. Visit the SBI MF website investor portal. 2. Login with your Folio/PAN. 3. Go to Service Request > Statements > Capital Gains.",
            "source": "https://www.sbimf.com/en-us/investor-corner/investor-services",
            "type": "statement"
        },
        {
            "text": "To download your Capital Gains statement for HDFC Mutual Fund: 1. Visit the HDFC MF portal. 2. Navigate to 'Online Console' or 'Request Statement'. 3. Select Capital Gains and choose financial year.",
            "source": "https://www.hdfcfund.com/investor-services/request-statement",
            "type": "statement"
        }
    ]
    
    for i, info in enumerate(statement_info):
        chunks.append(info['text'])
        metadata.append({"source": info['source'], "scheme": "General", "type": "statement"})
        ids.append(f"static_info_{i}")
                
    return chunks, metadata, ids

def main():
    data_path = os.path.join(PROJECT_ROOT, 'data/funds.json')
    db_path = os.path.join(PROJECT_ROOT, 'vector_db')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    data = load_data(data_path)
    chunks, metadata, ids = create_chunks(data)
    
    manager = ChromaManager(db_path=db_path)
    manager.add_documents(
        documents=chunks,
        metadatas=metadata,
        ids=ids
    )
    
    print(f"Successfully added {len(chunks)} chunks to vector database at {db_path}.")

if __name__ == "__main__":
    main()
