import heapq
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class PlanRequest(BaseModel):
    city_name: str
    budget: float
    duration: int
    suggested_hotels: List[dict]
    suggested_activities: List[dict]
    suggested_landmarks: List[dict]

class PlanResponse(BaseModel):
    hotel: Dict[str, Any] 
    activities: List[Dict[str, Any]] 
    landmarks: List[Dict[str, Any]] 
    total_plan_cost: float

def search_optimal_items(budget: float, activity_landmark_options: List[Dict[str, Any]]) -> tuple:
    """Search for optimal combination of activities and landmarks within budget."""
    try:
        scale = 100
        max_b = int(budget * scale) + 1
        dp = [0] * max_b
        selected_options = [[] for _ in range(max_b)]
        
        for option in activity_landmark_options:
            price = int(option.get('price', 0) * scale)
            if price <= 0:
                continue
            for b in range(max_b - 1, price - 1, -1):
                new_value = dp[b - price] + option.get('score', 0)
                if new_value > dp[b]:
                    dp[b] = new_value
                    selected_options[b] = selected_options[b - price] + [option]
        
        max_value = max(dp)
        max_index = dp.index(max_value)
        return max_value, selected_options[max_index]
    except Exception as e:
        logger.error(f"Error in search_optimal_items: {str(e)}")
        raise

def separate_activities_landmarks(
    selected_options: List[Dict[str, Any]],
    activities: List[Dict[str, Any]],
    landmarks: List[Dict[str, Any]]
) -> tuple:
    """Separate selected options into activities and landmarks, ensuring category diversity."""
    try:
        # Group activities by category
        activities_by_category = {}
        for item in selected_options:
            if item in activities:
                category = item.get('category', 'Uncategorized')
                if category not in activities_by_category:
                    activities_by_category[category] = []
                activities_by_category[category].append(item)
        
        # Sort activities within each category by score
        for category in activities_by_category:
            activities_by_category[category].sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Select activities ensuring diversity
        activities_options = []
        max_activities_per_category = 2  # Allow up to 2 activities per category
        
        # First, take the top activity from each category
        for category_activities in activities_by_category.values():
            if category_activities:
                activities_options.append(category_activities[0])
        
        # Then, if we have space, add more activities from each category
        remaining_slots = 5 - len(activities_options)
        if remaining_slots > 0:
            for category_activities in activities_by_category.values():
                if len(category_activities) > 1:
                    activities_options.append(category_activities[1])
                    remaining_slots -= 1
                    if remaining_slots == 0:
                        break
        
        # Sort final activities by score
        activities_options.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Get landmarks
        landmarks_options = [item for item in selected_options if item in landmarks][:5]
        
        return activities_options, landmarks_options
    except Exception as e:
        logger.error(f"Error in separate_activities_landmarks: {str(e)}")
        raise

def calculate_similarity(comb1: Dict[str, Any], comb2: Dict[str, Any]) -> int:
    """Calculate similarity between two plan combinations."""
    try:
        hotel_overlap = int(comb1['hotel']['hotel_id'] == comb2['hotel']['hotel_id'])
        activity_overlap = len(set(a['id'] for a in comb1['activities']) & set(a['id'] for a in comb2['activities']))
        landmark_overlap = len(set(l['id'] for l in comb1['landmarks']) & set(l['id'] for l in comb2['landmarks']))
        return hotel_overlap + activity_overlap + landmark_overlap
    except Exception as e:
        logger.error(f"Error in calculate_similarity: {str(e)}")
        raise

async def find_best_plan_options(
    hotels: List[Dict[str, Any]],
    activities: List[Dict[str, Any]],
    landmarks: List[Dict[str, Any]],
    budget: float,
    duration: int
) -> List[Dict[str, Any]]:
    """Find best plan options based on budget and duration."""
    try:
        activity_landmark_options = activities + landmarks
        for item in activity_landmark_options:
            if item.get('price') is None:
                item['price'] = 0.0
            if 'category' not in item and item in activities:
                item['category'] = 'Uncategorized'
        
        best_options = []
        activity_landmark_options.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        for hotel in hotels:
            hotel['price_per_night'] = hotel.get('price_per_night', 0) * duration
            remaining_budget = budget - hotel['price_per_night']
            
            if remaining_budget <= 0:
                continue
                
            options_score, selected_options = search_optimal_items(remaining_budget, activity_landmark_options)
            options_cost = sum(a.get('price', 0) for a in selected_options)
            total_cost = options_cost + hotel['price_per_night']
            total_score = options_score + hotel.get('score', 0)
            
            activities_options, landmarks_options = separate_activities_landmarks(
                selected_options, activities, landmarks
            )

            plan_combination = {
                "hotel": hotel,
                "activities": activities_options,
                "landmarks": landmarks_options,
                "total_score": total_score,
                "total_plan_cost": total_cost
            }
            
            if len(best_options) < 3:
                heapq.heappush(best_options, (total_score, plan_combination))
            elif total_score > best_options[0][0]:
                heapq.heappushpop(best_options, (total_score, plan_combination))

        return [item[1] for item in sorted(best_options, key=lambda x: x[0], reverse=True)]
    except Exception as e:
        logger.error(f"Error in find_best_plan_options: {str(e)}")
        raise

@router.post("/recommend", response_model=Dict[str, List[PlanResponse]])
async def create_plan(request: PlanRequest):
    """Create travel plan based on user preferences."""
    try:
        # Validate input
        if not request.suggested_hotels:
            raise HTTPException(status_code=400, detail="No hotels provided")
        if not request.suggested_activities and not request.suggested_landmarks:
            raise HTTPException(status_code=400, detail="No activities or landmarks provided")
        
        # Get plan combinations
        plan_combinations = await find_best_plan_options(
            request.suggested_hotels,
            request.suggested_activities,
            request.suggested_landmarks,
            request.budget,
            request.duration
        )
        
        if not plan_combinations:
            raise HTTPException(
                status_code=404,
                detail="No valid plan combinations found for the given budget and duration"
            )
        
        # Format response
        displayed_plan_combinations = []
        for plan_combination in plan_combinations:
            temp = {
                'hotel': plan_combination['hotel'],
                'activities': plan_combination['activities'],
                'landmarks': plan_combination['landmarks'],
                'total_plan_cost': plan_combination['total_plan_cost']
            }
            displayed_plan_combinations.append(temp)
            
        return {"plan_combinations": displayed_plan_combinations}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the plan"
        )

