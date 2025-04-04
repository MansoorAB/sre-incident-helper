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
from langchain_openai import ChatOpenAI
import time
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = setup_logger('search_agent')

class IncidentSearchAgent:
    def __init__(self):
        logger.info("Initializing IncidentSearchAgent...")
        self.vector_store = FaissVectorStore()
        self.mongo_client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.mongo_client.sre_incidents
        self.collection = self.db.incidents
        
        # Initialize primary and fallback LLMs
        self.primary_llm = ChatAnthropic(
            model="claude-3-haiku-20240307",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7
        )
        
        self.fallback_llm = ChatOpenAI(
            # model="gpt-4-0125-preview",
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
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
            llm=self.primary_llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        logger.info("IncidentSearchAgent initialized successfully")

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=1, max=10))
    def _classify_with_primary(self, query: str) -> bool:
        """Attempt classification with primary LLM (Claude-3-haiku)."""
        prompt = PromptTemplate(
            template="""You are a strict query classifier for a telecom incident response system.
            Your task is to determine if the following query is specifically about a telecom-related incident or technical issue.
            
            Query: {query}
            
            Classification Rules:
            1. The query MUST be about a technical incident or issue
            2. The incident MUST be telecom-related
            3. General questions about people, places, or non-technical topics are NOT incidents
            4. Questions about technology that aren't about incidents/issues should be classified as non-incidents
            5. The query should indicate some form of problem, failure, degradation, or technical challenge
            
            Examples:
            - "Network latency in core routers" -> true (technical telecom incident)
            - "5G service degradation in downtown" -> true (technical telecom incident)
            - "High latency in 5G Core affecting users" -> true (technical telecom incident)
            - "Tell me about 5G technology" -> false (general tech question, not an incident)
            - "Who is the CEO of Verizon" -> false (not an incident)
            - "What is the weather today" -> false (not an incident)
            
            Respond with ONLY 'true' if it's a telecom incident query, or 'false' if it's not.
            
            Classification (true/false):""",
            input_variables=["query"]
        )
        
        chain = prompt | self.primary_llm
        response = chain.invoke({"query": query})
        result = response.content.strip().lower() if hasattr(response, 'content') else str(response).strip().lower()
        logger.info(f"Primary LLM classification for '{query}': {result}")
        return result == 'true'

    def _classify_with_fallback(self, query: str) -> bool:
        """Attempt classification with fallback LLM (gpt-4o-mini)."""
        try:
            prompt = PromptTemplate(
                template="""You are a strict query classifier for a telecom incident response system.
                Your task is to determine if the following query is specifically about a telecom-related incident or technical issue.
                
                Query: {query}
                
                Classification Rules:
                1. The query MUST be about a technical incident or issue
                2. The incident MUST be telecom-related
                3. General questions about people, places, or non-technical topics are NOT incidents
                4. Questions about technology that aren't about incidents/issues should be classified as non-incidents
                5. The query should indicate some form of problem, failure, degradation, or technical challenge
                
                Examples:
                - "Network latency in core routers" -> true (technical telecom incident)
                - "5G service degradation in downtown" -> true (technical telecom incident)
                - "High latency in 5G Core affecting users" -> true (technical telecom incident)
                - "Tell me about 5G technology" -> false (general tech question, not an incident)
                - "Who is the CEO of Verizon" -> false (not an incident)
                - "What is the weather today" -> false (not an incident)
                
                Respond with ONLY 'true' if it's a telecom incident query, or 'false' if it's not.
                
                Classification (true/false):""",
                input_variables=["query"]
            )
            
            chain = prompt | self.fallback_llm
            response = chain.invoke({"query": query})
            result = response.content.strip().lower() if hasattr(response, 'content') else str(response).strip().lower()
            logger.info(f"Fallback LLM classification for '{query}': {result}")
            return result == 'true'
        except Exception as e:
            logger.warning(f"Fallback LLM classification failed: {str(e)}")
            return None

    def _classify_with_keywords(self, query: str) -> bool:
        """Fallback to keyword-based classification when both LLMs fail."""
        incident_keywords = ['latency', 'outage', 'degradation', 'failure', 'error', 'down', 'issue', 'problem']
        telecom_keywords = ['network', '5g', '4g', 'core', 'service', 'connectivity', 'packet', 'traffic']
        
        query_lower = query.lower()
        has_incident = any(keyword in query_lower for keyword in incident_keywords)
        has_telecom = any(keyword in query_lower for keyword in telecom_keywords)
        
        logger.info(f"Keyword classification for '{query}': has_incident={has_incident}, has_telecom={has_telecom}")
        return has_incident and has_telecom

    def _is_telecom_incident_query(self, query: str) -> bool:
        """Check if the query is related to a telecom incident using multiple fallback methods."""
        try:
            # Try primary LLM first (with 2 retries)
            return self._classify_with_primary(query)
        except Exception as e:
            logger.warning(f"Primary LLM classification failed after retries: {str(e)}. Trying fallback LLM...")
            
            # Try fallback LLM
            fallback_result = self._classify_with_fallback(query)
            if fallback_result is not None:
                return fallback_result
            
            # If both LLMs fail, use keyword-based classification
            logger.warning("Both LLMs failed. Using keyword-based classification...")
            return self._classify_with_keywords(query)

    def search_similar_incidents(self, query: str) -> tuple[List[str], List[float]]:
        """Search for similar incidents using FAISS and return incidents with scores."""
        if self.vector_store.index is None:
            logger.error("FAISS index is not initialized. Cannot perform search.")
            raise Exception("FAISS index is not initialized.")
        return self.vector_store.search_with_scores(query, k=5)

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

    async def process_incident(self, query: str) -> Dict[str, Any]:
        """Process incident query and generate response."""
        try:
            # First, check if this is a telecom incident query
            if not self._is_telecom_incident_query(query):
                logger.info(f"Non-incident query detected: {query}")
                return {
                    "is_non_incident_query": True,
                    "response": "",
                    "reference_incidents": []
                }

            # Continue with incident processing for valid queries
            logger.info(f"Processing telecom incident query: {query}")
            incident_ids, similarity_scores = self.vector_store.search_with_scores(query, k=5)
            
            # Get full incident details
            similar_incidents = list(self.collection.find({"incident_no": {"$in": incident_ids}}))
            
            # Create a mapping of incident_no to similarity score
            similarity_map = dict(zip(incident_ids, similarity_scores))
            
            # Generate response
            response = self.generate_response(query, similar_incidents, similarity_map)
            response["is_non_incident_query"] = False
            
            return response
            
        except Exception as e:
            logger.error(f"Error in process_incident: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=1, max=10))
    def generate_response(self, query: str, incidents: List[Dict[str, Any]], similarity_map: Dict[str, float]) -> Dict[str, Any]:
        """Generate response using LLM with fallback."""
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

        try:
            # Try with primary LLM using new syntax
            chain = prompt | self.primary_llm
            response = chain.invoke({"context": context, "query": query})
            response_text = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.warning(f"Primary LLM failed: {str(e)}. Falling back to GPT-4...")
            # Fallback to GPT-4 using new syntax
            chain = prompt | self.fallback_llm
            response = chain.invoke({"context": context, "query": query})
            response_text = response.content if hasattr(response, 'content') else str(response)

        return {
            "response": response_text,
            "reference_incidents": [
                {
                    "incident_no": inc["incident_no"],
                    "similarity": similarity_map[inc["incident_no"]]
                } 
                for inc in incidents
            ]
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