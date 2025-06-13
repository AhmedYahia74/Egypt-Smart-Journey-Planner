import aiohttp
from config_helper import get_db_params, get_api_urls
from fastapi import APIRouter, HTTPException
from contextlib import asynccontextmanager
import psycopg2
from psycopg2 import pool
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import time
import logging

router = APIRouter()
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
    city_name: str = Field(..., min_length=1, description="Name of the city")
    user_message: str = Field(..., min_length=1, description="User's message for landmark search")
    preferred_landmarks: List[str] = Field(default_factory=list, description="List of preferred landmarks")

class LandmarkResponse(BaseModel):
    id: int
    name: str 
    description: str
    score: float 
    price: float 
    longitude: float 
    latitude: float 

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool with retry logic."""
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
            await asyncio.sleep(retry_delay)
            retry_delay *= 2
        finally:
            if conn:
                try:
                    connection_pool.putconn(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")

def convert_row_to_dict(row: tuple) -> Dict[str, Any]:
    """Convert database row to dictionary format."""
    try:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "score": row[3],
            "price": row[4],
            "longitude": row[5],
            "latitude": row[6]
        }
    except Exception as e:
        logger.error(f"Error converting row to dict: {str(e)}")
        raise

async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using the embedding API."""
    try:
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                EMBEDDING_API_URL,
                json={"text": text},
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'embedding' not in result:
                        logger.error(f"No embedding in response: {result}")
                        return None
                    return result['embedding']
                else:
                    logger.error(f"Error getting embedding: {response.status}")
                    return None
    except aiohttp.ClientTimeout:
        logger.error("Embedding API request timed out")
        return None
    except aiohttp.ClientError as e:
        logger.error(f"Error calling embedding API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting embedding: {str(e)}")
        return None

async def get_landmark_by_text(conn, city_name: str, user_message: str) -> List[Dict[str, Any]]:
    """Get landmarks based on user message similarity."""
    try:
        embedding = await get_embedding(user_message)
        if not embedding:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%'))
            result = cursor.fetchall()
            return [convert_row_to_dict(row) for row in result]
    except Exception as e:
        logger.error(f"Error in get_landmark_by_text: {str(e)}")
        return []

async def get_landmark_by_user_activities(conn, city_name: str, user_activities: List[str]) -> List[Dict[str, Any]]:
    """Get landmarks based on user preferred activities."""
    try:
        landmarks_list = []
        with conn.cursor() as cursor:
            for activity in user_activities:
                embedding = await get_embedding(activity)
                if not embedding:
                    continue
                    
                cursor.execute(LANDMARK_QUERY, (embedding, '%' + city_name.lower() + '%'))
                landmarks_list.extend(convert_row_to_dict(row) for row in cursor.fetchall())
                
        # Remove duplicates while preserving order
        return list({landmark['id']: landmark for landmark in landmarks_list}.values())
    except Exception as e:
        logger.error(f"Error in get_landmark_by_user_activities: {str(e)}")
        return []

@router.post("/recommend", response_model=Dict[str, List[LandmarkResponse]])
async def get_landmarks(request: LandmarksRequestByText):
    """
    Search for landmarks based on user message and preferred activities.
    
    Args:
        request: LandmarksRequestByText containing city name, user message, and preferred landmarks
        
    Returns:
        Dictionary containing list of landmarks
    """
    try:
        async with get_db_connection() as conn:
            # Search for Landmarks by user message
            landmarks_by_message = await get_landmark_by_text(conn, request.city_name, request.user_message)

            # Search for Landmarks by user activities
            landmarks_by_user_activities = []
            if request.preferred_landmarks:
                landmarks_by_user_activities = await get_landmark_by_user_activities(
                    conn, request.city_name, request.preferred_landmarks
                )

            # Combine and deduplicate results
            landmark_list = landmarks_by_message + landmarks_by_user_activities
            landmark_list = list({landmark['id']: landmark for landmark in landmark_list}.values())
            
            # Sort by similarity score
            landmark_list.sort(key=lambda x: x['score'], reverse=True)

            if not landmark_list:
                raise HTTPException(
                    status_code=404,
                    detail=f"No landmarks found for city: {request.city_name}"
                )

            return {"landmarks": landmark_list}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_landmarks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching for landmarks"
        )


