import aiohttp
from config_helper import get_db_params, get_api_urls
from fastapi import APIRouter, HTTPException
from contextlib import asynccontextmanager
import psycopg2
from psycopg2 import pool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()

ACTIVITY_QUERY = """
    SELECT activity_id, A.name, A.description, 1 - (A.embedding <=> %s::vector) AS similarity, 
           price, A.duration_in_hours, S.name as state_name
    FROM activities A 
    JOIN states S ON A.state_id = S.state_id
    WHERE lower(S.name) LIKE %s 
    ORDER BY similarity desc limit 50
"""

# Create a connection pool
try:
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        **DB_Prams
    )
except Exception as e:
    logger.error(f"Failed to create connection pool: {str(e)}")
    raise

class ActivityRequestByText(BaseModel):
    city_name: str
    user_message: str
    preferred_activities: List[str]

class ActivityResponse(BaseModel):
    id: int 
    name: str 
    description: str
    score: float 
    price: Optional[float]
    duration: float
    state: str 

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
            "score": round(row[3] * 100, 2),  # Convert to percentage
            "price": float(row[4]) if row[4] is not None else None,
            "duration": row[5],
            "state": row[6]
        }
    except Exception as e:
        logger.error(f"Error converting row to dict: {str(e)}")
        raise

async def get_embedding(text: str) -> Optional[List[float]]:
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

async def get_activities_by_text(conn, city_name: str, user_message: str) -> List[Dict[str, Any]]:
    """Get activities based on user message similarity."""
    try:
        embedding = await get_embedding(user_message)
        if not embedding:
            return []
            
        with conn.cursor() as cursor:
            cursor.execute(ACTIVITY_QUERY, (embedding, f'%{city_name.lower()}%'))
            return [convert_row_to_dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error in get_activities_by_text: {str(e)}")
        return []

async def get_activities_by_user_activities(conn, city_name: str, user_activities: List[str]) -> List[Dict[str, Any]]:
    """Get activities based on user preferred activities."""
    try:
        activities_list = []
        with conn.cursor() as cursor:
            for activity in user_activities:
                embedding = await get_embedding(activity)
                if not embedding:
                    continue
                    
                cursor.execute(ACTIVITY_QUERY, (embedding, f'%{city_name.lower()}%'))
                activities_list.extend(convert_row_to_dict(row) for row in cursor.fetchall())
                
        # Remove duplicates while preserving order
        return list({activity['id']: activity for activity in activities_list}.values())
    except Exception as e:
        logger.error(f"Error in get_activities_by_user_activities: {str(e)}")
        return []

@router.post("/recommend", response_model=Dict[str, List[ActivityResponse]])
async def get_activities(request: ActivityRequestByText):
    """
    Search for activities based on user message and preferred activities.
    
    Args:
        request: ActivityRequestByText containing city name, user message, and preferred activities
        
    Returns:
        Dictionary containing list of activities
    """
    try:
        async with get_db_connection() as conn:
            # Search for Activities by user message
            activities_by_message = await get_activities_by_text(conn, request.city_name, request.user_message)

            # Search for Activities by user activities
            activities_by_user_activities = []
            if request.preferred_activities:
                activities_by_user_activities = await get_activities_by_user_activities(
                    conn, request.city_name, request.preferred_activities
                )

            # Combine and deduplicate results
            activity_list = activities_by_message + activities_by_user_activities
            activity_list = list({activity['id']: activity for activity in activity_list}.values())
            
            # Sort by similarity score
            activity_list.sort(key=lambda x: x['score'], reverse=True)

            if not activity_list:
                raise HTTPException(
                    status_code=404,
                    detail=f"No activities found in {request.city_name}"
                )

            return {"activities": activity_list}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_activities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching for activities"
        )



