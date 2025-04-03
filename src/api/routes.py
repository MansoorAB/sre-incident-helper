from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..vector_store.faiss_store import FaissVectorStore
from ..db.mongo_client import MongoDBClient
from ..chatbot.sre_bot import SREChatbot

router = APIRouter()
vector_store = FaissVectorStore()
mongo_client = MongoDBClient()
chatbot = SREChatbot()

class ChatRequest(BaseModel):
    query: str
    additional_context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    reference_incidents: List[str]

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Find similar incidents
        similar_incident_nos = vector_store.search(request.query)
        
        # Get full incident details
        similar_incidents = mongo_client.get_multiple_incidents(similar_incident_nos)
        
        # Generate response
        response = chatbot.generate_response(request.query, similar_incidents)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 