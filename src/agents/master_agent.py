from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from typing import Dict, Any, List

class MasterAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.tools = [
            Tool(
                name="search_incidents",
                func=self.search_similar_incidents,
                description="Search for similar historical incidents using vector similarity"
            ),
            Tool(
                name="fetch_incident_details",
                func=self.get_incident_details,
                description="Get full details of specific incidents from MongoDB"
            ),
            Tool(
                name="generate_response",
                func=self.generate_response,
                description="Generate response using Claude-3-haiku with incident context"
            ),
            Tool(
                name="log_interaction",
                func=self.log_interaction,
                description="Log query and response details with timestamps in IST"
            )
        ]
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        ) 