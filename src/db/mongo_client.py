from pymongo import MongoClient
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client.sre_incidents
        self.collection = self.db.incidents
    
    def store_incident(self, incident: Dict[str, Any]):
        return self.collection.insert_one(incident)
    
    def get_incident_details(self, incident_no: str) -> Dict[str, Any]:
        return self.collection.find_one({'incident_no': incident_no})
    
    def get_multiple_incidents(self, incident_nos: List[str]) -> List[Dict[str, Any]]:
        return list(self.collection.find({'incident_no': {'$in': incident_nos}})) 