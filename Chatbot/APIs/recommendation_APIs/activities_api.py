import requests
from config_helper import get_db_params, get_api_urls
from fastapi import FastAPI, HTTPException
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from pydantic import BaseModel
from typing import List
import time
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()
ACTIVITY_QUERY = """
    SELECT activity_id, A.name, A.description, 1 - (A.embedding <=> %s::vector) AS similarity , price , A.duration_in_hours
    FROM activities A 
    JOIN states S ON A.state_id = S.state_id
    WHERE lower(S.name) LIKE %s 
    ORDER BY similarity desc limit 50
"""


# Create a connection pool
connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_Prams
)

class ActivityRequestByText(BaseModel):
    city_name: str
    user_message: str
    preferred_activities: List[str]

@app.post("/api/activities/search")
def get_activities(request: ActivityRequestByText):
    try:
        with get_db_connection() as conn:
            # Search for Activities by user message
            activities_by_message = get_activities_by_text(conn, request.city_name, request.user_message)

            # Search for Activities by user activities
            activities_by_user_activities = []
            if request.preferred_activities:
                activities_by_user_activities = get_activities_by_user_activities(conn, request.city_name, request.preferred_activities)

            activity_list = activities_by_message + activities_by_user_activities

            # remove duplicates
            activity_list = list({activity['id']: activity for activity in activity_list}.values())
            # sort by similarity
            activity_list.sort(key=lambda x: x['score'], reverse=True)

            return {"activities": activity_list}
    except Exception as e:
        logger.error(f"Error in get_activities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@contextmanager
def get_db_connection():
    conn = None
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            conn = connection_pool.getconn()
            yield conn
            break
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise HTTPException(status_code=500, detail="Database connection failed after multiple attempts")
            time.sleep(retry_delay)
            retry_delay *= 2
        finally:
            if conn:
                try:
                    connection_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")


def convert_row_to_dict(row: tuple):
    ret = {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "score": row[3],
        "price": row[4],
        'duration': row[5]
    }
    return ret


def get_embedding(text: str) -> List[float]:
    response = requests.post(EMBEDDING_API_URL, json={"text": text})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error getting embedding")
    return response.json().get("embedding")

def get_activities_by_text(conn, city_name, user_massage):
    with conn.cursor() as cursor:
        # get the embedding for the user message
        embedding = get_embedding(user_massage)
        cursor.execute(ACTIVITY_QUERY, (embedding, '%' + city_name.lower() + '%', ))
        result = cursor.fetchall()
        result= [convert_row_to_dict(row) for row in result]

        return result

def get_activities_by_user_activities(conn, city_name, user_activities):
    activities_list = []
    with conn.cursor() as cursor:
        for activity in user_activities:
            # get the embedding for the activity
            embedding = get_embedding(activity)
            cursor.execute(ACTIVITY_QUERY, (embedding, '%' + city_name.lower() + '%',))
            activities_list.extend(convert_row_to_dict(row) for row in cursor.fetchall())
        activities_list = list({activity['id']: activity for activity in activities_list}.values())

        return activities_list


if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=3002)
    finally:
        if connection_pool:
            connection_pool.closeall()

