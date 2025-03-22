import requests

from DB_config import DB_Prams
from fastapi import FastAPI
import psycopg2

app = FastAPI()

EMBEDDING_API_URL="http://localhost:8000/empadding"

def concatenate_user_messages(user_msgs_json):
    user_msgs_str = ''
    for key, value in user_msgs_json.items():
        if value not in user_msgs_str:
            user_msgs_str += value + ' '
    return user_msgs_str

@app.get("/suggest_cities")
def suggest_cities(conversation_id:int):
    conn=None
    cur=None
    print("Conversation ID: ",conversation_id)
    try:
        conn=psycopg2.connect(**DB_Prams)
        cur=conn.cursor()
        cur.execute("SELECT user_msgs,slot_values FROM conversation_data WHERE conversation_id=%s",(conversation_id,))
        user_data=cur.fetchone()
        if not user_data:
            return {"error":"No conversation found with this conversation id"}


        user_msgs,user_values=concatenate_user_messages(user_data[0]),user_data[1]
        user_msgs_embedding = requests.post(EMBEDDING_API_URL, json={"text": user_msgs}).json()

        # get the cities the top 3 matched cities from the database
        select_query="SELECT name, description, embedding <-> %s::vector AS similarity FROM states ORDER BY similarity LIMIT 3"

        cur.execute(select_query,(str(user_msgs_embedding["empadding"]),))
        cities=cur.fetchall()
        return {"cities":cities}
    except Exception as e:
        print(f"Error in founding conversation: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

