import requests

from DB_config import DB_Prams
from fastapi import FastAPI
import psycopg2

app = FastAPI()

EMBEDDING_API_URL="http://localhost:9000/empadding"
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

        if not user_data[0]:
            return {"error":"No user message found in this conversation"}
        if not user_data[1]:
            return {"error":"No slot values found in this conversation"}
        user_msgs,slot_values=user_data[0],user_data[1]
        user_msgs_embedding = requests.post(EMBEDDING_API_URL, json={"text": user_msgs}).json()

        # get the cities the top 3 matched cities from the database
        select_query="SELECT city_name, description, embedding <-> %s::vector AS similarity FROM states ORDER BY similarity LIMIT 3"

        cur.execute(select_query,(str(user_msgs_embedding),))
        cities=cur.fetchall()
        return {"cities":cities}
    except Exception as e:
        print(f"Error in founding conversation: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

