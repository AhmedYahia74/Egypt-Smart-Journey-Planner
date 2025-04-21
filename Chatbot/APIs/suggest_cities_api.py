import requests
from config_helper import get_db_params, get_api_urls
from fastapi import FastAPI, HTTPException
import psycopg2

app = FastAPI()

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()
@app.get("/suggest_cities")
def suggest_cities(user_msgs: str):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_Prams)
        cur = conn.cursor()
        # get the user messages embedding
        user_msgs_embedding = requests.post(EMBEDDING_API_URL, json={"text": user_msgs}).json()

        # get the cities the top 3 matched cities from the database
        select_query = "SELECT name, description,1 - (embedding <=> %s::vector) AS similarity FROM states ORDER BY similarity desc LIMIT 3"

        cur.execute(select_query, (user_msgs_embedding["embedding"],))
        cities = cur.fetchall()
        print(type(cities[0][0]))
        cities_list = [{"name": city[0], "description": city[1], "similarity": city[2]} for city in cities]

        return {"top_cities": cities_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

