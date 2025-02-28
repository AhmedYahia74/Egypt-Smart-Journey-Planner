from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

NGROK_URL =  "https://d50e-156-203-119-173.ngrok-free.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        NGROK_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"
RASA_RESET_URL = "http://localhost:5005/conversations/{user_id}/tracker/events"

# Store active WebSocket connections
connections = {}

html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot</title>
    <style>
        #chat-container {{
            border: 1px solid black;
            padding: 10px;
            width: 300px;
            height: 300px;
            overflow: auto;
        }}
        #messageInput {{
            width: 200px;
        }}
    </style>
</head>
<body>
    <h2>Chatbot Interface</h2>
    <div id="chat-container"></div>
    <br>
    <input type="text" id="messageInput" autocomplete="off"/>
    <button onclick="sendMessage()">Send</button>
    <button onclick="clearChat()">Clear Chat</button>

    <script>
        let userId = localStorage.getItem("user_id") || "user_" + Math.floor(Math.random() * 100000);
        localStorage.setItem("user_id", userId);

        let wsUrl = window.location.hostname.includes("ngrok") 
            ? "{NGROK_URL.replace("https://", "wss://")}/ws/" + userId
            : "ws://127.0.0.1:8000/ws/" + userId;

        let ws = new WebSocket(wsUrl);

        ws.onopen = function() {{
            console.log("Connected to WebSocket!");
        }};

        ws.onmessage = function(event) {{
            let messages = document.getElementById('chat-container');
            let message = document.createElement('div');
            message.textContent = event.data;
            messages.appendChild(message);
        }};

        ws.onerror = function(error) {{
            console.error("WebSocket Error:", error);
        }};

        ws.onclose = function() {{
            console.log("WebSocket disconnected. Reconnecting...");
            setTimeout(() => {{
                ws = new WebSocket(wsUrl);
            }}, 3000);
        }};

        function sendMessage() {{
            let input = document.getElementById("messageInput");
            if (input.value.trim() !== "") {{
                ws.send(input.value);
                input.value = "";
            }}
        }}

        async function clearChat() {{
            let messages = document.getElementById('chat-container');
            messages.innerHTML = "";

            try {{
                let response = await fetch("{NGROK_URL}/reset_chat/" + userId, {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }}
                }});

                if (response.ok) {{
                    console.log("Chat reset successfully!");
                }} else {{
                    console.error("Failed to reset chat.");
                }}
            }} catch (error) {{
                console.error("Error resetting chat:", error);
            }}
        }}
    </script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            if data.strip():
                await websocket.send_text(f"You: {data}")

                response = requests.post(RASA_SERVER_URL, json={"sender": user_id, "message": data})

                if response.status_code == 200:
                    messages = response.json()
                    for msg in messages:
                        text = msg.get("text", "").strip()
                        if text:
                            await websocket.send_text(f'Rahhal: {text}')
                else:
                    await websocket.send_text("Rahhal: Error connecting to the server.")
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected.")
        connections.pop(user_id, None)  # Safely remove user
    except Exception as e:
        await websocket.send_text(f"Rahhal: An error occurred - {str(e)}")
        await websocket.close()

@app.post("/reset_chat/{user_id}")
async def reset_chat(user_id: str):
    try:
        reset_payload = {"event": "restart", "timestamp": None, "sender_id": user_id}
        response = requests.post(RASA_RESET_URL.format(user_id=user_id), json=reset_payload)

        if response.status_code == 200:
            return {"status": "success", "message": f"Chat reset for {user_id}."}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset chat in Rasa.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
