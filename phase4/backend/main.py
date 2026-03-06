import sys
import os
import json
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from phase3.chatbot_logic import MFFAQChatbot
from phase5_scheduler.scheduler import MFDataScheduler

load_dotenv()

app = FastAPI(title="SBI Mutual Fund FAQ API")

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = MFFAQChatbot()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    source: str = None

class LastUpdatedResponse(BaseModel):
    last_updated: str = None
    last_run_status: bool = None
    last_run_time: str = None
    data_path_exists: bool = False
    total_funds: int = 0

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "model": "Llama-3.3-70b-versatile-RAG"}

@app.get("/api/last-updated", response_model=LastUpdatedResponse)
def get_last_updated():
    """
    Get the last updated timestamp for fund data.
    Returns information about when the data was last refreshed.
    """
    try:
        scheduler = MFDataScheduler()
        status = scheduler.get_status()
        
        # Count total funds
        total_funds = 0
        data_path = os.path.join(PROJECT_ROOT, 'data', 'funds.json')
        if os.path.exists(data_path):
            try:
                with open(data_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        total_funds = len(data)
            except:
                pass
        
        return LastUpdatedResponse(
            last_updated=status.get('last_updated'),
            last_run_status=status.get('last_run_status'),
            last_run_time=status.get('last_run_time'),
            data_path_exists=status.get('data_path_exists', False),
            total_funds=total_funds
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trigger-update")
def trigger_update():
    """
    Manually trigger a full data update cycle.
    This runs the scraper and re-indexes the knowledge base.
    """
    try:
        scheduler = MFDataScheduler()
        success = scheduler.trigger_full_update()
        return {
            "success": success,
            "message": "Update completed successfully" if success else "Update failed",
            "last_updated": scheduler.get_last_updated()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    try:
        # Use the real generate_response method
        answer, source = chatbot.generate_response(request.query)
        return QueryResponse(answer=answer, source=source or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suggestions")
def get_suggestions():
    """Reads funds.json and generates varying random suggestion questions."""
    data_path = os.path.join(PROJECT_ROOT, 'data', 'funds.json')
    if not os.path.exists(data_path):
        return {"suggestions": ["What is a mutual fund?"]}
        
    try:
        with open(data_path, 'r') as f:
            funds = json.load(f)
            
        if not funds:
             return {"suggestions": ["What is a mutual fund?"]}
             
        # Select up to 6 random funds
        sample_funds = random.sample(funds, min(6, len(funds)))
        suggestions = []
        
        # Varied question templates
        templates = [
            "What is the expense ratio of {scheme_name}?",
            "What is the NAV for {scheme_name}?",
            "Tell me about the exit load of {scheme_name}.",
            "What is the minimum SIP amount for {scheme_name}?",
            "Is there a lock-in period for {scheme_name}?",
            "What is the risk rating of {scheme_name}?"
        ]
        
        for i, fund in enumerate(sample_funds):
            template = templates[i % len(templates)]
            suggestions.append(template.format(scheme_name=fund['scheme_name']))
            
        return {"suggestions": suggestions}
    except Exception as e:
        return {"suggestions": ["What is a mutual fund?", "How does SIP work?"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
