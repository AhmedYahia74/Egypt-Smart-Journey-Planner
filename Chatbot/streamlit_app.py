import streamlit as st
import requests
import json
import asyncio
import websockets
from config_helper import get_api_urls
import threading
import queue
import logging
from typing import Dict, Any
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API URLs
LOCAL_HOST_URL = "http://localhost:8000"  # Fixed base URL
CHATBOT_WS_URL = "ws://localhost:8000"  # Fixed WebSocket URL

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'pending_messages' not in st.session_state:
    st.session_state.pending_messages = []

CONVERSATION_ID = "123"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def display_plan(plan):
    st.markdown(f"**🏨 Hotel:** {plan['hotel']['hotel_name']}  ")
    st.markdown(f"Price per night: ${plan['hotel'].get('price_per_night', 'N/A')}  ")
    st.markdown(f"Facilities: {', '.join(plan['hotel'].get('facilities', []))}")
    st.markdown("**🎯 Activities:**")
    for activity in plan.get('activities', []):
        st.markdown(f"- {activity['name']} ({activity['duration']} hours, ${activity['price']})  ")
        st.markdown(f"  _{activity['description']}_")
    st.markdown("**🏛️ Landmarks:**")
    for landmark in plan.get('landmarks', []):
        st.markdown(f"- {landmark['name']} (${landmark['price']})  ")
        st.markdown(f"  _{landmark['description']}_")
    st.markdown(f"**💰 Total Cost:** ${plan.get('total_plan_cost', 'N/A')}")
    st.markdown("---")

def process_response(data: Dict[str, Any]):
    """Process response and add to chat history"""
    try:
        if data["type"] == "bot_message":
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": data["content"]
            })
        elif data["type"] == "bot_data":
            if isinstance(data["content"], dict) and "hotel" in data["content"]:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "",
                    "plan": data["content"]
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": str(data["content"])
                })
        elif data["type"] == "error":
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Error: {data['content']}"
            })
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Error processing response: {str(e)}"
        })

async def wait_for_bot_response(websocket, response_queue: queue.Queue, timeout: float = 30.0):
    """Wait for bot response with timeout"""
    try:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                if data["type"] == "bot_message" or data["type"] == "bot_data":
                    response_queue.put(data)
                    return True
                elif data["type"] == "user_message":
                    continue  # Skip user message confirmations
            except asyncio.TimeoutError:
                continue  # Continue waiting if no message received
        return False
    except Exception as e:
        logger.error(f"Error waiting for bot response: {str(e)}")
        return False

async def connect_and_send(message: str, response_queue: queue.Queue):
    """Connect to WebSocket and send message"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Connecting to WebSocket at {CHATBOT_WS_URL}/ws/{CONVERSATION_ID} (Attempt {attempt + 1}/{MAX_RETRIES})")
            async with websockets.connect(
                f"{CHATBOT_WS_URL}/ws/{CONVERSATION_ID}",
                ping_interval=30,
                ping_timeout=30,
                close_timeout=30,
                max_size=None
            ) as websocket:
                logger.info("WebSocket connected successfully")
                
                # Send the message as text
                logger.info(f"Sending message: {message}")
                await websocket.send(message)
                logger.info("Message sent successfully")
                
                # Wait for bot response
                if await wait_for_bot_response(websocket, response_queue):
                    logger.info("Successfully received bot response")
                    return
                
                logger.warning(f"No bot response received on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    
        except Exception as e:
            logger.error(f"WebSocket error on attempt {attempt + 1}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
            else:
                response_queue.put({
                    "type": "error",
                    "content": f"Failed to get response after {MAX_RETRIES} attempts. Please try again."
                })

def send_message(message: str):
    """Send message through WebSocket"""
    try:
        logger.info(f"Sending message: {message}")
        # Add user message to chat history immediately
        st.session_state.chat_history.append({"role": "user", "content": message})
        
        # Create a queue for this message's responses
        response_queue = queue.Queue()
        
        # Create and start a new thread for the WebSocket connection
        thread = threading.Thread(
            target=lambda: asyncio.run(connect_and_send(message, response_queue)),
            daemon=True
        )
        thread.start()
        
        # Wait for the thread to complete
        thread.join(timeout=60)
        
        if thread.is_alive():
            logger.warning("Message sending thread is still running after timeout")
            thread._stop()
            st.session_state.pending_messages.append({
                "type": "error",
                "content": "The bot is taking too long to respond. Please try again."
            })
        
        # Process any responses received
        while not response_queue.empty():
            data = response_queue.get()
            st.session_state.pending_messages.append(data)
            
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Error sending message: {str(e)}"
        })

def reset_chat():
    """Reset the chat conversation"""
    try:
        logger.info("Attempting to reset chat")
        response = requests.post(
            f"{LOCAL_HOST_URL}/reset_chat/{CONVERSATION_ID}"
        )
        
        if response.status_code == 200:
            st.session_state.chat_history.clear()
            st.session_state.pending_messages.clear()
            st.success("Chat has been reset!")
            logger.info("Chat reset successful")
        else:
            st.error("Failed to reset chat.")
            logger.error(f"Chat reset failed with status code: {response.status_code}")
    except Exception as e:
        st.error(f"Error resetting chat: {str(e)}")
        logger.error(f"Error resetting chat: {str(e)}")

# Set up the Streamlit page
st.set_page_config(page_title="Rahhal Chatbot", page_icon="🤖")
st.title("Rahhal Chatbot")

# Add a reset button
if st.button("Reset Chat"):
    reset_chat()

# Process any pending messages
while st.session_state.pending_messages:
    data = st.session_state.pending_messages.pop(0)
    process_response(data)

# Display chat history using st.chat_message
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        if "plan" in message:
            display_plan(message["plan"])
        else:
            st.markdown(message["content"])

# Chat input form
with st.form(key='chat_form', clear_on_submit=True):
    user_input = st.text_input("Type your message here:")
    submit_button = st.form_submit_button(label='Send')

if submit_button and user_input:
    # Send message through WebSocket
    send_message(user_input)
    st.rerun()