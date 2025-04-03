from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import pytz
from ..agents.search_agent import IncidentSearchAgent
from ..utils.logger import setup_logger
import traceback

# Setup logger
logger = setup_logger('sre_api')

app = FastAPI(
    title="SRE Incident Response Bot",
    description="Telecom domain SRE chatbot using RAG for incident resolution"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Configure logging in IST
ist = pytz.timezone('Asia/Kolkata')

# Initialize agent
incident_agent = IncidentSearchAgent()

class IncidentQuery(BaseModel):
    description: str

@app.post("/api/query")
async def process_query(query: IncidentQuery):
    try:
        logger.info(f"Received incident query: {query.description[:100]}...")
        
        # Process the incident
        logger.info("Processing incident through search agent...")
        response = await incident_agent.process_incident(query.description)
        
        logger.info(f"Successfully processed incident. Found {len(response['reference_incidents'])} reference incidents")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/")
async def root():
    try:
        logger.info("Health check request received")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    logger.info("Starting SRE Incident Response Bot...")
    # Add any initialization code here

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down SRE Incident Response Bot...")
    # Add any cleanup code here 