"""
Script to generate synthetic telecom SRE incident data.
"""

from src.data_generator import TelecomIncidentGenerator

def main():
    print("Starting synthetic telecom SRE incident data generation...")
    
    # Create generator instance
    generator = TelecomIncidentGenerator()
    
    # Generate 50 incidents
    incidents = generator.generate_dataset(num_incidents=300)
    
    print(f"\nGenerated {len(incidents)} incidents successfully!")
    print("Data has been saved to the data/incidents directory.")
    print("\nExample incident types generated:")
    incident_types = {}
    for incident in incidents:
        incident_type = incident['type']
        incident_types[incident_type] = incident_types.get(incident_type, 0) + 1
    
    for incident_type, count in incident_types.items():
        print(f"- {incident_type}: {count} incidents")

if __name__ == "__main__":
    main() 