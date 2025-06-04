call .venv\Scripts\activate.bat
start cmd /k "rasa run actions"
start cmd /k "rasa run --enable-api"
start cmd /k "uvicorn APIs.embedding_api:app --port 8001"
start cmd /k "uvicorn APIs.suggest_hotels_api:app --port 3001"
start cmd /k "uvicorn APIs.suggest_cities_api:app --port 3000"
start cmd /k "uvicorn APIs.suggest_landmarks_activities_api:app --port 3002"
start cmd /k "uvicorn APIs.suggest_plan_api:app --port 3003"
start cmd /k "uvicorn APIs.chatbot_api:app --port 8000"
