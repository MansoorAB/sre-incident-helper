import os
import json
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class TelecomIncidentGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Common incident patterns to ensure some repetition
        self.incident_patterns = {
            "network_outage": {
                "components": [
                    "Multi-RAT Core Network", "5G SA Core", "Cloud-native IMS", 
                    "O-RAN Implementation", "Transport MPLS Network", 
                    "Distributed DNS Infrastructure", "Network Slicing Function",
                    "NFV Infrastructure", "Container Platform"
                ],
                "symptoms": [
                    "complete service loss", "intermittent connectivity", 
                    "degraded performance", "authentication failures",
                    "signaling storms", "service registration failures"
                ]
            },
            "latency_issues": {
                "components": [
                    "Regional Data Centers", "MEC Infrastructure", 
                    "Fiber Backhaul Links", "Cloud-RAN Platform",
                    "Inter-DC WAN", "Edge Computing Nodes"
                ],
                "thresholds": [
                    ">100ms", ">200ms", ">500ms", 
                    "jitter >50ms", "packet loss >0.1%"
                ]
            },
            "capacity_problems": {
                "components": [
                    "Virtualized Core", "RAN Cluster", "SDN Backhaul",
                    "International Gateway", "Subscriber Database",
                    "Load Balancer Infrastructure"
                ],
                "symptoms": [
                    "congestion", "throttling", "packet loss",
                    "connection pool exhaustion", "memory overutilization",
                    "CPU saturation"
                ]
            },
            "service_degradation": {
                "services": [
                    "HD Voice", "5G Data Services", "Emergency Services",
                    "Roaming Platform", "Location Services", "MMTEL",
                    "Network Slices", "IoT Platform"
                ],
                "impact_levels": [
                    "minor", "moderate", "severe",
                    "critical", "regional", "system-wide"
                ]
            },
            "platform_issues": {
                "components": [
                    "Orchestration Platform", "CI/CD Pipeline",
                    "Monitoring Infrastructure", "Log Analytics Platform",
                    "Automation Framework", "Configuration Management"
                ],
                "symptoms": [
                    "deployment failures", "auto-scaling issues",
                    "monitoring gaps", "automation failures",
                    "configuration drift", "resource leaks"
                ]
            }
        }

    def _generate_incident_prompt(self, incident_type: str) -> str:
        """Generate a detailed prompt for the incident type."""
        pattern = self.incident_patterns[incident_type]
        component = random.choice(pattern.get("components", pattern.get("services", [])))
        
        base_prompt = f"""Generate a detailed telecom SRE incident report for a {incident_type} affecting {component}. 
        The report should include:
        1. Incident title (one line)
        2. Description including initial symptoms and user impact
        3. Timeline of key events
        4. Root cause analysis
        5. Resolution steps taken
        6. Preventive measures for future
        7. Keywords (comma-separated technical terms relevant to this incident)

        IMPORTANT: Return only the raw JSON without any markdown formatting (no ``` or ```json).
        The response should be a valid JSON object with this exact structure:
        {{
            "title": "string",
            "description": "string",
            "timeline": ["string"],
            "root_cause": "string",
            "resolution": "string",
            "preventive_measures": ["string"],
            "severity": "string (P1/P2/P3/P4)",
            "duration_minutes": number,
            "affected_users_percentage": number,
            "keywords": ["string"]
        }}

        Make it realistic, technical, and include specific telecom terms and metrics."""

        return base_prompt

    def generate_incident(self, incident_type: str = None) -> Dict[str, Any]:
        """Generate a single incident report."""
        if incident_type is None:
            incident_type = random.choice(list(self.incident_patterns.keys()))

        prompt = self._generate_incident_prompt(incident_type)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an experienced telecom SRE engineer with deep knowledge of mobile networks, protocols, and operations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            incident_data = json.loads(response.choices[0].message.content)
            
            # Add metadata
            incident_data["id"] = f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            incident_data["type"] = incident_type
            incident_data["timestamp"] = datetime.now().isoformat()
            
            return incident_data
            
        except Exception as e:
            print(f"Error generating incident: {str(e)}")
            return None

    def generate_dataset(self, num_incidents: int = 50, output_dir: str = "data/incidents") -> List[Dict[str, Any]]:
        """Generate a dataset of incidents with some repetitive patterns."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        incidents = []
        
        # Ensure some repetition in incident types
        incident_types = []
        for _ in range(num_incidents):
            # 35% chance to repeat a previous incident type
            if incidents and random.random() < 0.35:
                incident_type = random.choice(incident_types)
            else:
                incident_type = random.choice(list(self.incident_patterns.keys()))
            incident_types.append(incident_type)
            
            incident = self.generate_incident(incident_type)
            if incident:
                # Save individual incident file
                filename = f"incident_{incident['id']}.json"
                with open(os.path.join(output_dir, filename), 'w') as f:
                    json.dump(incident, f, indent=2)
                
                incidents.append(incident)
                print(f"Generated incident {len(incidents)}/{num_incidents}")
        
        # Save to CSV
        csv_filename = os.path.join(output_dir, "incidents.csv")
        self._save_to_csv(incidents, csv_filename)
        
        return incidents

    def _save_to_csv(self, incidents: List[Dict[str, Any]], filename: str):
        """Save incidents to CSV format."""
        import csv
        
        fieldnames = [
            'id', 'type', 'timestamp', 'title', 'description', 'root_cause',
            'resolution', 'severity', 'duration_minutes', 'affected_users_percentage',
            'keywords'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for incident in incidents:
                # Prepare row data
                row = {
                    'id': incident['id'],
                    'type': incident['type'],
                    'timestamp': incident['timestamp'],
                    'title': incident['title'],
                    'description': incident['description'],
                    'root_cause': incident['root_cause'],
                    'resolution': incident['resolution'],
                    'severity': incident['severity'],
                    'duration_minutes': incident['duration_minutes'],
                    'affected_users_percentage': incident['affected_users_percentage'],
                    'keywords': ','.join(incident['keywords'])
                }
                writer.writerow(row)

def main():
    """Generate a sample dataset of incidents."""
    generator = TelecomIncidentGenerator()
    incidents = generator.generate_dataset(num_incidents=50)
    print(f"Generated {len(incidents)} incidents successfully.") 