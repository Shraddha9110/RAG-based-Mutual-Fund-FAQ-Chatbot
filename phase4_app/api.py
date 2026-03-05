import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Add project root to path to allow imports from other phase folders
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from phase3.chatbot_logic import MFFAQChatbot

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

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": "RAG-Bot-v2"}

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    try:
        answer, source = chatbot.generate_response_dummy(request.query)
        return QueryResponse(answer=answer, source=source or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/last_updated")
def get_last_updated():
    try:
        file_path = os.path.join(project_root, "data", "funds.json")
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            # Format: 'March 05, 2026, 16:04 PM'
            date_time = datetime.fromtimestamp(mtime).strftime("%B %d, %Y, %I:%M %p")
            return {"last_updated": date_time}
        else:
            return {"last_updated": "Unknown"}
    except Exception as e:
        return {"last_updated": f"Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
