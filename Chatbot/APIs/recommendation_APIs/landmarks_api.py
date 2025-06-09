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

LANDMARK_QUERY = """
    SELECT landmark_id, L.name, L.description, 1 - (L.embedding <=> %s::vector) AS similarity, price_foreign, L.longitude, L.latitude
    FROM landmarks L join states S on L.state_id = S.state_id
    WHERE lower(S.name) LIKE %s
    ORDER BY similarity desc
   """

# Create a connection pool
connection_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    **DB_Prams
)

class LandmarksRequestByText(BaseModel):
    city_name: str
    user_message: str
    preferred_landmarks: List[str]

@app.post("/api/landmarks/search")
def get_landmarks(request: LandmarksRequestByText):
    try:
        with get_db_connection() as conn:
            # Search for Landmarks by user message
            landmarks_by_message = get_landmark_by_text(conn, request.city_name, request.user_message)

            # Search for Landmarks by user activities
            landmarks_by_user_activities = []
            if request.preferred_landmarks:
                landmarks_by_user_activities = get_landmark_by_user_activities(conn, request.city_name, request.preferred_landmarks)

            landmark_list = landmarks_by_message + landmarks_by_user_activities

            # remove duplicates
            landmark_list = list({landmark['id']: landmark for landmark in landmark_list}.values())
            # sort by similarity
            landmark_list.sort(key=lambda x: x['score'], reverse=True)

            return {"landmarks": landmark_list}
    except Exception as e:
        logger.error(f"Error in get_landmarks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@contextmanager
def get_db_connection():
    conn = None
    max_retries = 3
    retry_delay = 1
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


def convert_row_to_dict(row: tuple, kind):
    ret = {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "score": row[3],
        "price": row[4]
    }
    if kind == 'a':
        ret['duration'] = row[5]
    else:
        ret['longitude'] = row[5]
        ret['latitude'] = row[6]
    return ret


def get_embedding(text: str) -> List[float]:
    response = requests.post(EMBEDDING_API_URL, json={"text": text})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error getting embedding")
    return response.json().get("embedding")

def get_landmark_by_text(conn, city_name, user_massage):
    with conn.cursor() as cursor:
        # get the embedding for the user message
        embedding = get_embedding(user_massage)
        cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%', ))
        result = cursor.fetchall()
        return [convert_row_to_dict(row,'l') for row in result]
def get_landmark_by_user_activities(conn, city_name, user_activities):
    landmarks_list = []
    with conn.cursor() as cursor:
        for landmark in user_activities:
            # get the embedding for the activity
            embedding = get_embedding(landmark)
            cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%',))
            landmarks_list.extend(convert_row_to_dict(row,'l') for row in cursor.fetchall())
        return list({landmark['id']: landmark for landmark in landmarks_list}.values())

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(app, host="0.0.0.0", port=3004)
    finally:
        if connection_pool:
            connection_pool.closeall()
