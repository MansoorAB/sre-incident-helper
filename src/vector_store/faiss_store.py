from typing import List, Dict, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

class FaissVectorStore:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2',
                                         use_auth_token=os.getenv("HUGGINGFACE_API_KEY"))
        self.index = None
        self.incident_map = {}
        # Load existing index during initialization
        self.load_index()
        
    def load_index(self):
        """Load existing FAISS index and mapping."""
        try:
            if os.path.exists('data/vector_store/incident_index.faiss'):
                self.index = faiss.read_index('data/vector_store/incident_index.faiss')
                with open('data/vector_store/incident_map.json', 'r') as f:
                    self.incident_map = json.load(f)
                print("Successfully loaded existing FAISS index")
                return True
        except Exception as e:
            print(f"Error loading existing FAISS index: {str(e)}")
        return False
        
    def create_index(self, dimension: int):
        self.index = faiss.IndexFlatL2(dimension)
    
    def add_incidents(self, incidents_dir: str):
        texts = []
        for filename in os.listdir(incidents_dir):
            if filename.endswith('.json'):
                with open(os.path.join(incidents_dir, filename), 'r') as f:
                    incident = json.load(f)
                    # Create searchable text from incident details
                    text = f"{incident['incident_description']} {incident['incident_no']} {' '.join(incident['keywords'])}"
                    texts.append(text)
                    self.incident_map[len(texts)-1] = incident['incident_no']
        
        # Convert texts to embeddings
        embeddings = self.model.encode(texts)
        if self.index is None:
            self.create_index(embeddings.shape[1])
        self.index.add(np.array(embeddings))
    
    def search(self, query: str, k: int = 5) -> List[str]:
        if self.index is None:
            raise Exception("FAISS index not initialized. Please ensure index is created or loaded.")
        query_embedding = self.model.encode([query])
        D, I = self.index.search(np.array(query_embedding), k)
        return [self.incident_map[str(i)] for i in I[0]] 