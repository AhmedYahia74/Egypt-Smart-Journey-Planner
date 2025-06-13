from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from config_helper import get_db_params
from APIs.recommendation_system.trip_recommender import TripRecommender
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize recommender with connection pool
try:
    recommender = TripRecommender(get_db_params())
except Exception as e:
    logger.error(f"Failed to initialize TripRecommender: {str(e)}")
    raise

class UserPreferences(BaseModel):
    budget: Optional[float] = None
    duration: Optional[int] = None
    state: Optional[str] = None
    arrival_date: Optional[str] = None

class UserMessages(BaseModel):
    request_trip: Optional[str] = None
    state: Optional[str] = None
    budget: Optional[str] = None
    duration: Optional[str] = None
    arrival_date: Optional[str] = None
    landmarks_activities: Optional[str] = None
    hotel_features: Optional[str] = None
    city_description: Optional[str] = None

class TripRecommendation(BaseModel):
    trip_id: int
    title: str
    description: str
    state: str
    price: float
    date: str
    available_seats: int
    duration: str
    match_score: float

@router.post("/recommend", response_model=List[TripRecommendation])
async def get_recommendations(
    preferences: UserPreferences, 
    user_messages: UserMessages, 
    top_n: int = Query(3, description="Number of recommendations to return")
):
    """
    Get trip recommendations based on user preferences and messages.
    
    Args:
        preferences: User's trip preferences
        user_messages: User's conversation messages
        top_n: Number of recommendations to return (defaults to 3)
        
    Returns:
        List of trip recommendations matching the criteria
    """
    try:
        # Log input data
        logger.info(f"Received preferences: {preferences.dict()}")
        logger.info(f"Received user messages: {user_messages.dict()}")
        
        # Convert Pydantic models to dicts
        preferences_dict = preferences.dict(exclude_none=True)
        messages_dict = user_messages.dict(exclude_none=True)
        
        # Validate required fields
        if not messages_dict.get('request_trip'):
            raise HTTPException(
                status_code=400, 
                detail="Trip request message is required"
            )
        
        # Get recommendations
        try:
            recommendations = await recommender.get_recommendations(
                preferences_dict, 
                messages_dict, 
                top_n
            )
        except Exception as e:
            logger.error(f"Error in recommender.get_recommendations: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error getting recommendations: {str(e)}"
            )
        
        if not recommendations:
            raise HTTPException(
                status_code=404, 
                detail="No matching trips found for the given criteria"
            )
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred while processing your request"
        )

