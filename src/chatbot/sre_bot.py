from anthropic import Anthropic
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class SREChatbot:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    def generate_response(self, query: str, context_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Prepare context from similar incidents
        context = self._prepare_context(context_incidents)
        
        # Generate response using Claude
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{
                "role": "system",
                "content": "You are an expert SRE chatbot specializing in telecom incidents. Use the provided historical incidents to suggest solutions."
            }, {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuery: {query}\n\nProvide root cause, resolution, and preventive measures based on similar historical incidents."
            }]
        )
        
        return {
            "response": response.content,
            "reference_incidents": [inc["incident_no"] for inc in context_incidents]
        }
    
    def _prepare_context(self, incidents: List[Dict[str, Any]]) -> str:
        context = []
        for incident in incidents:
            context.append(
                f"Incident {incident['incident_no']}:\n"
                f"Root Cause: {incident['root_cause']}\n"
                f"Resolution: {incident['resolution']}\n"
                f"Preventive Measures: {incident['preventive_measures']}\n"
            )
        return "\n\n".join(context) 