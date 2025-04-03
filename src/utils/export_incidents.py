import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

# Load environment variables
load_dotenv()

# Configure logging
def setup_logger():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up logging with IST timezone
    logger = logging.getLogger('mongo_export')
    logger.setLevel(logging.INFO)

    # Create formatter with IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    formatter.converter = lambda *args: datetime.now(ist).timetuple()

    # File handler
    file_handler = logging.FileHandler(f'logs/mongo_export_{datetime.now(ist).strftime("%Y%m%d_%H%M%S")}.log')
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def export_incidents():
    logger = setup_logger()
    
    try:
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client.sre_incidents
        collection = db.incidents

        # Create data directory if it doesn't exist
        data_dir = os.path.join('data', 'incidents')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Created directory: {data_dir}")

        # Get all incidents
        incidents = collection.find({})
        count = 0

        # Export each incident to a JSON file
        for incident in incidents:
            try:
                # Remove MongoDB's _id field
                incident_id = incident.pop('_id')
                
                # Create filename using incident_no
                filename = f"INC_{incident['incident_no']}.json"
                filepath = os.path.join(data_dir, filename)

                # Write to JSON file
                with open(filepath, 'w') as f:
                    json.dump(incident, f, indent=2)
                
                count += 1
                logger.info(f"Exported incident {incident['incident_no']} to {filename}")

            except Exception as e:
                logger.error(f"Error exporting incident {incident.get('incident_no', 'unknown')}: {str(e)}")
                continue

        logger.info(f"Successfully exported {count} incidents to {data_dir}")

    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {str(e)}")
    finally:
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    export_incidents() 