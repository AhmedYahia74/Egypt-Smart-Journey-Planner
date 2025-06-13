from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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

class TripRequest(BaseModel):
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences including budget, duration, state, and arrival_date"
    )
    user_messages: Dict[str, Any] = Field(
        default_factory=dict,
        description="User conversation messages including request_trip and other context"
    )

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
async def get_recommendations(request: TripRequest):
    """
    Get trip recommendations based on user preferences and messages.
    
    Args:
        request: TripRequest containing preferences and user messages
        
    Returns:
        List of trip recommendations matching the criteria
    """
    try:
        # Log input data
        logger.info(f"Received request: {request.dict()}")
        
        # Validate required fields
        if not request.user_messages.get('request_trip'):
            raise HTTPException(
                status_code=400, 
                detail="Trip request message is required"
            )
        
        # Get recommendations
        try:
            recommendations = await recommender.get_recommendations(
                request.preferences, 
                request.user_messages, 
                top_n=3  # Default to 3 recommendations
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

