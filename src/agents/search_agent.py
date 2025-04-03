from langchain.agents import Tool, initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from ..vector_store.faiss_store import FaissVectorStore
from pymongo import MongoClient
from ..utils.logger import setup_logger
import traceback

load_dotenv()

logger = setup_logger('search_agent')

class IncidentSearchAgent:
    def __init__(self):
        logger.info("Initializing IncidentSearchAgent...")
        self.vector_store = FaissVectorStore()
        self.mongo_client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.mongo_client.sre_incidents
        self.collection = self.db.incidents
        
        # Initialize Claude
        self.llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7
        )
        
        # Define tools
        self.tools = [
            Tool(
                name="search_similar_incidents",
                func=self.search_similar_incidents,
                description="Search for similar incidents using semantic search"
            ),
            Tool(
                name="get_incident_details",
                func=self.get_incident_details,
                description="Get full incident details from MongoDB"
            ),
            Tool(
                name="generate_response",
                func=self.generate_response,
                description="Generate response using similar incidents"
            )
        ]
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        logger.info("IncidentSearchAgent initialized successfully")

    def search_similar_incidents(self, query: str) -> List[str]:
        """Search for similar incidents using FAISS."""
        if self.vector_store.index is None:
            logger.error("FAISS index is not initialized. Cannot perform search.")
            raise Exception("FAISS index is not initialized.")
        return self.vector_store.search(query, k=5)

    def get_incident_details(self, incident_no: str):
        """Get full incident details from MongoDB."""
        try:
            incident = self.collection.find_one({"incident_no": incident_no})
            if incident:
                # Remove MongoDB's _id field
                incident.pop('_id', None)
                return incident
            return None
        except Exception as e:
            logger.error(f"Error fetching incident details: {str(e)}")
            raise

    def generate_response(self, query: str, incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using Claude."""
        context = self._prepare_context(incidents)
        
        prompt = PromptTemplate(
            template="""You are an expert SRE chatbot specializing in telecom incidents.
            Based on the following similar incidents and their resolutions, provide a comprehensive response
            to the current incident query.

            Similar Incidents:
            {context}

            Current Incident Query: {query}

            Provide a detailed response in the following format:
            
            Root Cause Analysis:
            • [Root cause point 1]
            • [Root cause point 2]
            ...

            Resolution Steps:
            • [Resolution step 1]
            • [Resolution step 2]
            ...

            Preventive Measures:
            • [Preventive measure 1]
            • [Preventive measure 2]
            ...

            Note: Please use bullet points (•) for each item and ensure each point is clear and concise.
            Do not include incident references within the sections - they will be displayed separately.""",
            input_variables=["context", "query"]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(context=context, query=query)
        
        return {
            "response": response,
            "reference_incidents": [inc["incident_no"] for inc in incidents]
        }

    def _prepare_context(self, incidents: List[Dict[str, Any]]) -> str:
        context = []
        for incident in incidents:
            context.append(
                f"Incident {incident['incident_no']}:\n"
                f"Description: {incident.get('description', '')}\n"
                f"Root Cause: {incident.get('root_cause', '')}\n"
                f"Resolution: {incident.get('resolution', '')}\n"
                f"Preventive Measures: {incident.get('preventive_measures', '')}\n"
            )
        return "\n\n".join(context)

    async def process_incident(self, query: str) -> Dict[str, Any]:
        """Process incident query and generate response."""
        try:
            logger.info("Starting incident processing...")
            
            # Search for similar incidents
            logger.info("Searching for similar incidents...")
            similar_incident_nos = self.search_similar_incidents(query)
            logger.info(f"Found {len(similar_incident_nos)} similar incidents")
            
            # Get full incident details
            logger.info("Retrieving incident details from MongoDB...")
            similar_incidents = [self.get_incident_details(incident_no) for incident_no in similar_incident_nos]
            logger.info(f"Retrieved {len(similar_incidents)} incident details")
            
            # Generate response
            logger.info("Generating response using Claude...")
            response = self.generate_response(query, similar_incidents)
            logger.info("Response generated successfully")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_incident: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise 