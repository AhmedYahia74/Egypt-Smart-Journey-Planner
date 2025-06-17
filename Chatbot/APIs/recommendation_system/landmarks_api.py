import asyncio
import aiohttp
from config_helper import get_api_urls
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import time
import logging
from .db_manager import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

EMBEDDING_API_URL = get_api_urls().get('embedding')

LANDMARK_QUERY = """
    SELECT *, 1 - (L.embedding <=> %s::vector) AS similarity
    FROM landmarks L join states S on L.state_id = S.state_id
    WHERE lower(S.name) LIKE %s
    ORDER BY similarity desc
   """

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
    img: str or None = None

def convert_row_to_dict(row: tuple) -> Dict[str, Any]:
    """Convert database row to dictionary format."""
    try:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[5],
            "score": row[10],
            "price": row[7],
            "longitude": row[3],
            "latitude": row[4],
        }
    except Exception as e:
        logger.error(f"Error converting row to dict: {str(e)}")
        raise

async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using the embedding API."""
    start_time = time.time()
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
                    logger.info(f"Embedding generated in {time.time() - start_time:.2f}s")
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
async def get_landmarks(request: Request, landmarks_request: LandmarksRequestByText):
    """Search for landmarks based on a user message and preferred activities."""
    start_time = time.time()
    logger.info(f"Received landmarks request for city: {landmarks_request.city_name}")
    
    try:
        async with db_manager.get_connection() as conn:
            # Search for Landmarks by user message
            msg_start_time = time.time()
            landmarks_by_message = await get_landmark_by_text(conn, landmarks_request.city_name, landmarks_request.user_message)
            logger.info(f"Message-based search completed in {time.time() - msg_start_time:.2f}s with {len(landmarks_by_message)} results")

            # Search for Landmarks by user activities
            activities_start_time = time.time()
            landmarks_by_user_activities = []
            if landmarks_request.preferred_landmarks:
                landmarks_by_user_activities = await get_landmark_by_user_activities(
                    conn, landmarks_request.city_name, landmarks_request.preferred_landmarks
                )
                logger.info(f"Activities-based search completed in {time.time() - activities_start_time:.2f}s with {len(landmarks_by_user_activities)} results")

            # Combine and deduplicate results
            landmark_list = landmarks_by_message + landmarks_by_user_activities
            landmark_list = list({landmark['id']: landmark for landmark in landmark_list}.values())
            
            # Sort by similarity score
            landmark_list.sort(key=lambda x: x['score'], reverse=True)

            if not landmark_list:
                logger.warning(f"No landmarks found for city: {landmarks_request.city_name}")
                raise HTTPException(
                    status_code=404,
                    detail=f"No landmarks found for city: {landmarks_request.city_name}"
                )

            total_time = time.time() - start_time
            logger.info(f"Total request processing time: {total_time:.2f}s")
            return {"landmarks": landmark_list}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_landmarks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching for landmarks"
        )


