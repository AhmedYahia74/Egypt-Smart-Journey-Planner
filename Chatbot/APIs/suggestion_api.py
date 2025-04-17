import requests

from config_helper import get_db_params, get_api_urls
from fastapi import FastAPI, HTTPException
import psycopg2

app = FastAPI()

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()


def concatenate_user_messages(user_msgs_json):
    user_msgs_str = ''
    for key, value in user_msgs_json.items():
        if value not in user_msgs_str:
            user_msgs_str += value + ' '
    return user_msgs_str


@app.get("/suggest_cities")
def suggest_cities(conversation_id: int):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**DB_Prams)
        cur = conn.cursor()
        user_msgs_embedding, user_values = get_user_msgs_embedding(conversation_id, cur, conn)

        if "error" in user_msgs_embedding:
            raise HTTPException(status_code=404, detail=user_msgs_embedding["error"])

        # get the cities the top 3 matched cities from the database
        select_query = "SELECT name, description, embedding <-> %s::vector AS similarity FROM states ORDER BY similarity LIMIT 3"

        cur.execute(select_query, (user_msgs_embedding["embedding"],))
        trips = cur.fetchall()
        return {"trips": trips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.get("/suggest_trips")
def suggest_trips(conversation_id: int, city_name: str):
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(**DB_Prams)
        cur = conn.cursor()
        user_msgs_embedding, user_values = get_user_msgs_embedding(conversation_id, cur, conn)

        if "error" in user_msgs_embedding:
            raise HTTPException(status_code=404, detail=user_msgs_embedding["error"])

        budget = user_values["budget"]
        start_date = user_values["arrival_date"][0]
        end_date = user_values["arrival_date"][1]
        duration = user_values.get("duration", "0").strip()
        # get the best 3 matched trips from the database considering the city name and trip date
        select_query = ('''SELECT *,embedding <-> %s::vector AS similarity
                            FROM trips
                            JOIN LATERAL (
                                SELECT
                                    CASE
                                        WHEN trips.duration ~ '^\d+ Hours' THEN (regexp_replace(trips.duration, '\D+', '', 'g'))::INT
                                        WHEN trips.duration ~ '^\d+ Days' THEN (regexp_replace(trips.duration, '(\D+).*', '', 'g'))::INT*24
                                        ELSE NULL
                                    END AS duration_hours
                            ) AS extracted_duration ON TRUE
                            WHERE lower(state) like %s
                            AND price <= %s
                            AND date BETWEEN %s AND %s and date is not null
                            AND is_active = true
                            AND duration_hours <= %s
                            ORDER BY similarity
                            LIMIT 3;
                            ''')
        select_prams = (user_msgs_embedding["embedding"],'%'+city_name.lower()+'%', int(budget), start_date, end_date, duration)

        cur.execute(select_query, select_prams)
        trips = cur.fetchall()

        return {"trips": trips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_user_msgs_embedding(conversation_id, cur=None, conn=None):
    cur.execute("SELECT user_msgs,slot_values FROM conversation_data WHERE conversation_id=%s", (conversation_id,))
    user_data = cur.fetchone()
    if not user_data:
        return {"error": "No conversation found with this conversation id"}
    user_msgs, user_values = concatenate_user_messages(user_data[0]), user_data[1]
    user_msgs_embedding = requests.post(EMBEDDING_API_URL, json={"text": user_msgs}).json()
    return user_msgs_embedding, user_values
