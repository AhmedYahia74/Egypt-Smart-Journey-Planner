call .venv\Scripts\activate.bat

:: Start Rasa services first
start cmd /k "rasa run actions"
start cmd /k "rasa run --enable-api"

:: Start the embedding service (needed by other services)
start cmd /k "uvicorn APIs.embedding_api:app --port 8001"

:: Start the combined recommendation API
start cmd /k "uvicorn APIs.recommendation_APIs.combined_api:app --port 8002"

:: Start the main chatbot API last (depends on other services)
start cmd /k "uvicorn APIs.chatbot_api:app --port 8000"
