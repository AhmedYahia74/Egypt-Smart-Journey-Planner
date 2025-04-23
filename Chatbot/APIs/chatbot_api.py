import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from config_helper import get_db_params, get_api_urls

app = FastAPI()

NGROK_URL = get_api_urls().get('ngrok')
LOCAL_HOST_URL = get_api_urls().get('local')
RASA_SERVER_URL = get_api_urls().get('rasa_server')
RASA_RESET_URL = get_api_urls().get('rasa_reset')


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

html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot</title>
    <style>
        body {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f4f4f4;
        }}

        #chat-container {{
            border: 1px solid black;
            padding: 10px;
            width: 350px;
            height: 400px;
            overflow: auto;
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: 10px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        }}

        .message {{
            padding: 8px 12px;
            margin: 5px;
            border-radius: 15px;
            max-width: 70%;
            word-wrap: break-word;
        }}

        .user-message {{
            background-color: #d1e7dd;
            align-self: flex-end;
        }}

        .bot-message {{
            background-color: #f8d7da;
            align-self: flex-start;
        }}

        #input-container {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }}

        #messageInput {{
            width: 250px;
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }}

        button {{
            padding: 6px 12px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            background-color: #007bff;
            color: white;
        }}

        button:hover {{
            background-color: #0056b3;
        }}
    </style>
</head>
<body>
    <div>
        <h2 style="text-align: center;">Rahhal</h2>
        <div id="chat-container"></div>
        <div id="input-container">
            <input type="text" id="messageInput" autocomplete="on"/>
            <button id="sendBtn">Send</button>
            <button id="clearBtn" style="background-color: red;">Clear</button>
        </div>
    </div>

    <script>
        let userId = localStorage.getItem("user_id") || "user_" + Math.floor(Math.random() * 100000);
        localStorage.setItem("user_id", userId);

        let wsUrl = "{NGROK_URL}".replace("https://", "wss://") + "/ws/" + userId;

        let ws = new WebSocket(wsUrl);

        ws.onopen = function() {{
            console.log("Connected to WebSocket!");
        }};

        ws.onmessage = function(event) {{
            let messages = document.getElementById('chat-container');
            let message = document.createElement('div');
            message.textContent = event.data;
            message.classList.add("message");

            if (event.data.startsWith("You:")) {{
                message.classList.add("user-message");
            }} else {{
                message.classList.add("bot-message");
            }}

            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
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

        document.getElementById("sendBtn").addEventListener("click", sendMessage);
        document.getElementById("clearBtn").addEventListener("click", clearChat);

    </script>
</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)

def handle_city_description(websocket: WebSocket, conversation_id: str, data: str):
    pass

# after finishing testing , set the conversation_id to int and replace every id with conversation_id
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
                        text = msg.get("text", "").strip()
                        buttons= msg.get("buttons", [])
                        if text and not buttons:
                            await websocket.send_text(f'Rahhal: {text}')
                        elif buttons:
                            button_labels = [{"title": btn["title"], "payload": btn["payload"]} for btn in buttons]
                            await websocket.send_text(f'Rahhal: {json.dumps({"text": text, "buttons": button_labels})}')

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