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
    SELECT activity_id, A.name, A.description, 1 - (A.embedding <=> %s::vector) AS similarity , price 
    FROM activities A 
    JOIN states S ON A.state_id = S.state_id
    WHERE lower(S.name) LIKE %s 
    ORDER BY similarity desc limit 50
"""
LANDMARK_QUERY = """
    SELECT landmark_id, L.name, L.description, 1 - (L.embedding <=> %s::vector) AS similarity, price_foreign
    FROM landmarks L join states S on L.state_id = S.state_id
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




def convert_row_to_dict(row: tuple):
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "score": row[3],
        "price":row[4]
    }
def get_embedding(text: str) -> List[float]:
    response = requests.post(EMBEDDING_API_URL, json={"text": text})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error getting embedding")
    return response.json().get("embedding")

class ActivityRequestByText(BaseModel):
    city_name: str
    user_message: str
    preferred_activities: List[str]

@app.post("/suggest_landmarks_activities")
def suggest_activities(request: ActivityRequestByText):
    with get_db_connection() as conn:
        # Search for Activities and Landmarks by user message
        activities_by_message = get_activities_by_text(conn, request.city_name, request.user_message)
        landmarks_by_message = get_landmark_by_text(conn, request.city_name, request.user_message)

        # Search for Activities and Landmarks by user activities
        activities_by_user_activities = []
        landmarks_by_user_activities = []
        if request.preferred_activities:
            activities_by_user_activities = get_activities_by_user_activities(conn, request.city_name, request.preferred_activities)
            landmarks_by_user_activities = get_landmark_by_user_activities(conn, request.city_name, request.preferred_activities)

        activity_list = activities_by_message + activities_by_user_activities
        landmark_list = landmarks_by_message + landmarks_by_user_activities

        # remove duplicates
        activity_list = list({activity['id']: activity for activity in activity_list}.values())
        landmark_list = list({landmark['id']: landmark for landmark in landmark_list}.values())
        # sort by similarity
        activity_list.sort(key=lambda x: x['score'], reverse=True)
        landmark_list.sort(key=lambda x: x['score'], reverse=True)


        return {"activities": activity_list, "landmarks": landmark_list}




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



def get_landmark_by_text(conn, city_name, user_massage):
    with conn.cursor() as cursor:
        # get the embedding for the user message
        embedding = get_embedding(user_massage)
        cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%', ))
        result = cursor.fetchall()
        return [convert_row_to_dict(row) for row in result]
def get_landmark_by_user_activities(conn, city_name, user_activities):
    landmarks_list = []
    with conn.cursor() as cursor:
        for landmark in user_activities:
            # get the embedding for the activity
            embedding = get_embedding(landmark)
            cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%',))
            landmarks_list.extend(convert_row_to_dict(row) for row in cursor.fetchall())
        return list({landmark['id']: landmark for landmark in landmarks_list}.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)


city="luxor"
user_message="I want to visit luxor"
preferred_activities=["museums","monuments","temples","historical buildings","monuments","historical buildings","museums","monuments","temples"]
