@echo off
call .venv\Scripts\activate.bat

:: Start Rasa services first

start cmd /k "call .venv\Scripts\activate.bat && rasa run --enable-api"
start cmd /k "call .venv\Scripts\activate.bat && rasa run actions"
:: Start the embedding service (needed by other services)
start cmd /k "call .venv\Scripts\activate.bat && uvicorn APIs.embedding_api:app --port 8001 --reload"


:: Start the combined recommendation API
start cmd /k "call .venv\Scripts\activate.bat && uvicorn APIs.recommendation_system.combined_api:app --port 8002 --reload"

:: Start the main chatbot API last (depends on other services)
start cmd /k "call .venv\Scripts\activate.bat && uvicorn APIs.chatbot_api:app --port 8000 --reload"
