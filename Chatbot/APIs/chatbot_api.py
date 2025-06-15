import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from config_helper import  get_api_urls

app = FastAPI()

NGROK_URL = get_api_urls().get('ngrok')
LOCAL_HOST_URL = get_api_urls().get('local')
RASA_SERVER_URL = get_api_urls().get('rasa_server')
RASA_RESET_URL = get_api_urls().get('rasa_reset')
SUGGEST_PLAN_URL = get_api_urls().get('suggest_plan')
SUGGEST_HOTELS_URL = get_api_urls().get('suggest_hotels')
SUGGEST_LANDMARKS_ACTIVITIES_URL = get_api_urls().get('suggest_landmarks_activities')



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        LOCAL_HOST_URL,
        NGROK_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connections = {}


SUGGEST_MSG="suggest your trip"

# after finishing testing, set the conversation_id to int and replace every id with conversation_id
@app.websocket("/ws/{conversation_id}")
async def manage_chat_session(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    connections[conversation_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            if data.strip():
                await websocket.send_text(f"You: {data}")
                print(f"User {conversation_id} sent: {data}")

                response = requests.post(RASA_SERVER_URL, json={"sender": conversation_id, "message": data})

                if response.status_code == 200:
                    messages = response.json()

                    for msg in messages:
                        text = msg.get("text", "")
                        await websocket.send_text(f'Rahhal: {text}')
                else:
                    await websocket.send_text("Rahhal: Error connecting to the server.")
    except WebSocketDisconnect:
        print(f"User {conversation_id} disconnected.")
        connections.pop(conversation_id, None)
    except Exception as e:
        await websocket.send_text(f"Rahhal: An error occurred - {str(e)}")
        await websocket.close()

# don't forget to change the user_id to int and replace id with conversation_id
# Reset chat

@app.post("/reset_chat/{conversation_id}")
async def reset_chat(conversation_id: str):
    try:
        reset_payload = {"event": "restart", "timestamp": None}
        response = requests.post(RASA_RESET_URL.format(conversation_id=conversation_id), json=reset_payload)

        if response.status_code == 200:
            return {"status": "success", "message": f"Chat reset for {conversation_id}."}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset chat in Rasa.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import  uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)