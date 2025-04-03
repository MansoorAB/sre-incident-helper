import os
import json
from typing import Dict, Any, List, Set
from pymongo import MongoClient
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

# Load environment variables
load_dotenv()

# Configure logging with IST timezone
class ISTFormatter(logging.Formatter):
    def converter(self, timestamp):
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.fromtimestamp(timestamp, ist)
    
    def formatTime(self, record, datefmt=None):
        ist_time = self.converter(record.created)
        if datefmt:
            return ist_time.strftime(datefmt)
        return ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')

# Setup logging
def setup_logging():
    logger = logging.getLogger('incident_loader')
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File handler
    file_handler = logging.FileHandler('logs/incident_loader.log')
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = ISTFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S %Z')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class IncidentDataLoader:
    def __init__(self):
        # Setup logging
        self.logger = setup_logging()
        
        # MongoDB setup
        self.mongo_client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.mongo_client.sre_incidents
        self.collection = self.db.incidents

        # FAISS and embedding setup
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2',
                                        use_auth_token=os.getenv("HUGGINGFACE_API_KEY"))
        self.index = None
        self.incident_map = {}

    def get_existing_incidents(self) -> Set[str]:
        """Get set of incident numbers already in MongoDB."""
        existing = set(doc['incident_no'] for doc in self.collection.find({}, {'incident_no': 1}))
        self.logger.info(f"Found {len(existing)} existing incidents in MongoDB")
        return existing

    def load_existing_faiss_index(self) -> bool:
        """Load existing FAISS index and mapping if they exist."""
        try:
            faiss_path = 'data/vector_store/incident_index.faiss'
            map_path = 'data/vector_store/incident_map.json'
            
            if os.path.exists(faiss_path) and os.path.exists(map_path):
                self.index = faiss.read_index(faiss_path)
                with open(map_path, 'r') as f:
                    self.incident_map = json.load(f)
                self.logger.info("Successfully loaded existing FAISS index")
                return True
            else:
                self.logger.info("No existing FAISS index found")
                return False
        except Exception as e:
            self.logger.error(f"Error loading existing FAISS index: {str(e)}")
            return False

    def create_new_faiss_index(self):
        """Create new FAISS index from all MongoDB incidents."""
        try:
            # Get all incidents from MongoDB
            all_incidents = list(self.collection.find({}))
            self.logger.info(f"Creating new FAISS index from {len(all_incidents)} incidents")

            texts_for_embedding = []
            incident_numbers = []

            for incident in all_incidents:
                search_text = f"{incident.get('description', '')} {' '.join(incident.get('keywords', []))}"
                texts_for_embedding.append(search_text)
                incident_numbers.append(incident['incident_no'])

            if texts_for_embedding:
                # Create embeddings
                embeddings = self.model.encode(texts_for_embedding)
                dimension = embeddings.shape[1]

                # Initialize FAISS index
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(embeddings))
                
                # Create mapping
                self.incident_map = {str(i): inc_no for i, inc_no in enumerate(incident_numbers)}
                
                # Save index and mapping
                self.save_faiss_index()
                self.logger.info("Successfully created and saved new FAISS index")
                return True
            else:
                self.logger.warning("No incidents found to create FAISS index")
                return False

        except Exception as e:
            self.logger.error(f"Error creating new FAISS index: {str(e)}")
            return False

    def save_faiss_index(self):
        """Save FAISS index and mapping."""
        try:
            if not os.path.exists('data/vector_store'):
                os.makedirs('data/vector_store')

            faiss.write_index(self.index, 'data/vector_store/incident_index.faiss')
            with open('data/vector_store/incident_map.json', 'w') as f:
                json.dump(self.incident_map, f)
            self.logger.info("Saved FAISS index and mapping to disk")
        except Exception as e:
            self.logger.error(f"Error saving FAISS index: {str(e)}")
            raise

    def load_incidents(self, incidents_dir: str):
        """Load incidents into FAISS and MongoDB."""
        self.logger.info("Starting incident loading process...")

        # Step 1: Get existing incidents from MongoDB
        existing_incidents = self.get_existing_incidents()

        # Step 2: Check for existing FAISS index
        has_existing_index = self.load_existing_faiss_index()
        if not has_existing_index:
            self.logger.info("No existing FAISS index found, creating new one...")
            if not self.create_new_faiss_index():
                self.logger.error("Failed to create new FAISS index")
                return

        # Step 3: Process new incidents
        new_incidents = []
        for filename in os.listdir(incidents_dir):
            if not filename.endswith('.json'):
                continue

            try:
                with open(os.path.join(incidents_dir, filename), 'r') as f:
                    incident = json.load(f)
                    
                # Skip if incident already exists
                if incident['incident_no'] in existing_incidents:
                    continue
                    
                # Add to MongoDB
                self.collection.insert_one(incident)
                new_incidents.append(incident)
                self.logger.info(f"Added incident {incident['incident_no']} to MongoDB")
                
            except Exception as e:
                self.logger.error(f"Error processing {filename}: {str(e)}")
                continue

        # Step 4: Update FAISS index with new incidents (if any)
        if new_incidents:
            self.logger.info(f"Adding {len(new_incidents)} new incidents to FAISS index")
            try:
                # Prepare new embeddings
                texts = [f"{inc.get('description', '')} {' '.join(inc.get('keywords', []))}" 
                        for inc in new_incidents]
                embeddings = self.model.encode(texts)

                # Add to existing index
                self.index.add(np.array(embeddings))

                # Update mapping
                start_idx = max(int(idx) for idx in self.incident_map.keys()) + 1
                for i, incident in enumerate(new_incidents):
                    self.incident_map[str(start_idx + i)] = incident['incident_no']

                # Save updated index
                self.save_faiss_index()
                self.logger.info("Successfully updated FAISS index with new incidents")

            except Exception as e:
                self.logger.error(f"Error updating FAISS index: {str(e)}")
                raise
        else:
            self.logger.info("No new incidents to add to FAISS index")

    def test_search(self, query: str, k: int = 5):
        """Test search functionality."""
        self.logger.info(f"Testing search with query: {query}")
        
        try:
            # Get query embedding
            query_vector = self.model.encode([query])
            
            # Search in FAISS
            D, I = self.index.search(np.array(query_vector), k)
            
            # Get incident numbers
            incident_numbers = [self.incident_map[str(i)] for i in I[0]]
            
            # Log the indices and distances
            self.logger.info(f"FAISS indices: {I[0]}")
            self.logger.info(f"Distances: {D[0]}")
            self.logger.info(f"Incident numbers retrieved: {incident_numbers}")
            
            # Fetch full incidents from MongoDB
            incidents = list(self.collection.find({"incident_no": {"$in": incident_numbers}}))
            
            self.logger.info(f"Found {len(incidents)} relevant incidents")
            for incident in incidents:
                self.logger.info(f"Incident: {incident['incident_no']}, "
                               f"Title: {incident['title']}, "
                               f"Score: {D[0][incident_numbers.index(incident['incident_no'])]}")
                
        except Exception as e:
            self.logger.error(f"Error during search: {str(e)}")

def main():
    loader = IncidentDataLoader()
    
    # Load incidents
    loader.load_incidents("data/incidents")
    
    # Test search functionality
    test_query = "network latency issues in core network"
    loader.test_search(test_query)

if __name__ == "__main__":
    main() 