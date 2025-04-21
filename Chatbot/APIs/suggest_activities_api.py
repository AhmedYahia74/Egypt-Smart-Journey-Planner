import requests
from config_helper import get_db_params, get_api_urls
from fastapi import FastAPI, HTTPException
from contextlib import contextmanager
import psycopg2
from pydantic import BaseModel
from typing import List

app = FastAPI()

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()
ACTIVITY_QUERY = """
    SELECT activity_id, A.name, A.description, 1 - (A.embedding <=> %s::vector) AS similarity 
    FROM activities A 
    JOIN states S ON A.state_id = S.state_id
    WHERE lower(S.name) LIKE %s 
    ORDER BY similarity desc 
"""
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_Prams)
        yield conn
    finally:
        if conn:
            conn.close()

class ActivityRequestByText(BaseModel):
    city_name: str
    user_massage: str
    user_activities: List[str] = []


def format_activity(row: tuple):
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "similarity": row[3]
    }
def get_embedding(text: str) -> List[float]:
    response = requests.post(EMBEDDING_API_URL, json={"text": text})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error getting embedding")
    return response.json().get("embedding")


@app.post("/suggest_activities")
def suggest_activities(request: ActivityRequestByText):
    with get_db_connection() as conn:
        activities_by_message = get_activities_by_massage(conn, request.city_name, request.user_massage)
        activities_by_user_activities = []
        if user_activities:
            activities_by_user_activities = get_activities_by_user_activities(conn, request.city_name, request.user_activities)

        activity_list = activities_by_message + activities_by_user_activities
        # remove duplicates
        activity_list = list({activity['id']: activity for activity in activity_list}.values())
        # sort by similarity
        unique_activities=activity_list.sort(key=lambda x: x['similarity'], reverse=True)
        return {"activities": unique_activities}




def get_activities_by_massage(conn, city_name, user_massage):
    with conn.cursor() as cursor:
        # get the embedding for the user message
        embedding = get_embedding(user_massage)
        cursor.execute(ACTIVITY_QUERY, (embedding, '%' + city_name.lower() + '%', ))
        result = cursor.fetchall()
        return [format_activity(row) for row in result]

def get_activities_by_user_activities(conn, city_name, user_activities):
    activities_list = []
    with conn.cursor() as cursor:
        for activity in user_activities:
            # get the embedding for the activity
            embedding = get_embedding(activity)
            cursor.execute(ACTIVITY_QUERY, (embedding, '%' + city_name.lower() + '%',))
            activities_list.extend(format_activity(row) for row in cursor.fetchall())
        return list({activity['id']: activity for activity in activities_list}.values())


