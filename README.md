# SRE Incident Management System

An intelligent system for managing and analyzing SRE (Site Reliability Engineering) incidents using AI. The system provides semantic search capabilities, incident analysis, and a user-friendly interface for incident management.

## Directory Structure

```
.
├── data/
│   ├── incidents/          # JSON files for individual incidents
│   └── vector_store/       # FAISS index and mapping files
├── src/
│   ├── agents/            # AI agents for incident analysis
│   │   ├── master_agent.py
│   │   └── search_agent.py
│   ├── api/              # FastAPI backend
│   │   ├── main.py
│   │   └── routes.py
│   ├── chatbot/          # SRE chatbot implementation
│   │   └── sre_bot.py
│   ├── data_generator/   # Synthetic incident data generation
│   │   └── incident_generator.py
│   ├── data_loader/      # Data loading utilities
│   │   └── load_incidents.py
│   ├── db/              # Database connections
│   │   └── mongo_client.py
│   ├── static/          # Frontend assets
│   │   ├── index.html
│   │   ├── script.js
│   │   └── styles.css
│   ├── utils/           # Utility functions
│   │   ├── export_incidents.py
│   │   └── logger.py
│   └── vector_store/    # FAISS vector store implementation
│       └── faiss_store.py
├── generate_data.py     # Script to generate sample incidents
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Requirements

- Python 3.11 or higher
- MongoDB 6.0 or higher
- Virtual environment (venv or conda)

## API Keys Required

The following API keys need to be set in your `.env` file:

```
MONGODB_URI=your_mongodb_connection_string
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

## MongoDB Setup

1. Create a MongoDB database named `sre_incidents`
2. Create a collection named `incidents`
3. Ensure your MongoDB URI includes the database name: `mongodb+srv://username:password@cluster.mongodb.net/sre_incidents`

## Installation & Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd sre-incident-agentic
   ```

2. Create and activate a virtual environment (or anaconda as per your wish):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys (see above)

5. Generate sample incidents (optional):
   ```bash
   python generate_data.py
   ```

6. Export incidents from MongoDB to local directory JSON files  (if needed):
   ```bash
   python -m src.utils.export_incidents
   ```

7. Create FAISS index:
   ```bash
   python -m src.data_loader.load_incidents
   ```

8. Start the FastAPI server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

The application will be available at `http://localhost:8000`

## Module Descriptions

### Agents
- `search_agent.py`: Implements semantic search and incident analysis using LLMs (Claude and GPT-4)
- `master_agent.py`: Orchestrates multiple agents for complex incident analysis

### API
- `main.py`: FastAPI application setup and configuration
- `routes.py`: API endpoint definitions

### Data Management
- `incident_generator.py`: Generates synthetic incident data using AI
- `load_incidents.py`: Loads incidents into FAISS for vector search
- `mongo_client.py`: MongoDB connection and CRUD operations
- `export_incidents.py`: Exports MongoDB incidents to JSON files

### Vector Store
- `faiss_store.py`: FAISS implementation for semantic search

### Frontend
- `index.html`, `script.js`, `styles.css`: Web interface for incident management
- `index2.html`, `script2.js`, `styles2.css`: Enhanced UI with additional features

### Utilities
- `logger.py`: Centralized logging configuration

## Features

- Semantic search for similar incidents
- AI-powered incident analysis
- Root cause analysis
- Resolution steps identification
- Preventive measures suggestion
- User-friendly web interface
- Fallback mechanisms for API overload
- Comprehensive logging

## Error Handling

The system includes robust error handling:
- Automatic retries for API calls
- Fallback to alternative LLMs
- Graceful degradation
- Detailed logging in IST timezone

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 