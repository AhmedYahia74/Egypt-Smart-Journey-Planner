import aiohttp
from config_helper import get_api_urls
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from .db_manager import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

EMBEDDING_API_URL = get_api_urls().get('embedding')

ACTIVITY_QUERY = """
    SELECT activity_id, A.name, A.description, 1 - (A.embedding <=> %s::vector) AS similarity, 
           price, A.duration_in_hours, A.img,A.category, S.name as state_name
    FROM activities A 
    JOIN states S ON A.state_id = S.state_id
    WHERE lower(S.name) LIKE %s 
    ORDER BY similarity desc limit 50
"""

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
    img: str = None
    category: str

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
            "state": row[8],
            "img": row[6],
            "category": row[7]
        }
    except Exception as e:
        logger.error(f"Error converting row to dict: {str(e)}")
        raise

async def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for text using the embedding API."""
    if not text or not text.strip():
        return None
        
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                EMBEDDING_API_URL,
                json={"text": text},
                timeout=30  # Increased timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('embedding')
                return None
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
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
                
        return list({activity['id']: activity for activity in activities_list}.values())
    except Exception as e:
        logger.error(f"Error in get_activities_by_user_activities: {str(e)}")
        return []

@router.post("/recommend", response_model=Dict[str, List[ActivityResponse]])
async def get_activities(request: ActivityRequestByText):
    """Search for activities based on a user message and preferred activities."""
    try:
        async with db_manager.get_connection() as conn:
            # Get activities by message
            activities_by_message = await get_activities_by_text(conn, request.city_name, request.user_message)

            # Get activities by user preferences
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



