# Travel Planning Chatbot

A conversational AI chatbot that helps users plan their trips in Egypt by recommending cities, hotels, activities, and landmarks based on their preferences.

## Prerequisites

- Docker
- Docker Compose
- Git

## Project Structure

```
Chatbot/
├── actions/                 # Custom action server code
├── APIs/                   # API services
│   ├── recommendation_APIs/ # Recommendation APIs
│   └── embedding_api.py    # Embedding service
├── data/                   # Training data
├── models/                 # Trained Rasa models
└── docker-compose.yml     # Docker configuration
```

## Running the Chatbot

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Chatbot
   ```

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```
   This will start:
   - Rasa Core (main model server) on port 5005
   - Rasa Action Server on port 5055
   - API Service on ports 8000, 8001, and 8002

3. **Test the chatbot:**
   - Use the Rasa shell: `docker-compose run --rm rasa-core rasa shell`
   - Or connect to the REST API at `http://localhost:5005/webhooks/rest/webhook`

## Handling Codebase Changes

### When to Retrain the Model

You need to retrain the Rasa model when you make changes to:
- NLU data (intents, examples, entities)
- Stories or rules
- Domain file (slots, responses, actions, forms)
- Config pipeline (config.yml)

To retrain:
```bash
docker-compose run --rm rasa-core rasa train
```

### When to Rebuild Containers

You need to rebuild containers when you make changes to:
- Custom action code (Python files in `actions/`)
- FastAPI backend code (APIs)
- Docker or deployment files

To rebuild:
```bash
docker-compose down
docker-compose up --build
```

