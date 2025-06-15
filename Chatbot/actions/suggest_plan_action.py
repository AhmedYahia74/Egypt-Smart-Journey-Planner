from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests
import json
import time
from typing import Any, Dict, List, Text, Optional
from requests.exceptions import RequestException, Timeout
from config_helper import get_api_urls
import logging
from pydantic import BaseModel
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class APIError(Exception):
    # Base exception for API related errors
    pass

class APIResponseError(APIError):
    # Exception for invalid API responses
    pass

class APITimeoutError(APIError):
    # Exception for API timeout errors
    pass

class APIConnectionError(APIError):
    # Exception for API connection errors
    pass

class Hotel(BaseModel):
    hotel_id: Optional[int] = None
    hotel_name: str
    longitude: float
    latitude: float
    facilities: List[str]
    score: Optional[float] = None
    price_per_night: Optional[float] = None

class Activity(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    score: Optional[float] = None
    price: float
    duration: float

class Landmark(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    score: Optional[float] = None
    price: float
    longitude: float
    latitude: float

class Plan(BaseModel):
    hotel: Hotel
    activities: List[Activity]
    landmarks: List[Landmark]
    total_score: Optional[float] = None
    total_plan_cost: float

class PlanResponse(BaseModel):
    plan_combinations: List[Plan]
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class APIConfig:
    base_url: str
    timeout: int = 50
    max_retries: int = 3
    retry_delay: int = 2

class APIClient:
    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.config.base_url}{endpoint}"
        retry_delay = self.config.retry_delay

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except Timeout:
                if attempt == self.config.max_retries - 1:
                    raise APITimeoutError(f"Request timed out after {self.config.max_retries} attempts")
                logger.warning(f"Attempt {attempt + 1} timed out, retrying in {retry_delay} seconds...")
            except RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise APIConnectionError(f"Failed to connect to API: {str(e)}")
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            retry_delay *= 2

        raise APIError("Max retries exceeded")

class SuggestPlan(Action):
    def name(self) -> Text:
        return "action_suggest_plan"

    def __init__(self):
        super().__init__()
        self.api_configs = self._initialize_api_configs()

    def _initialize_api_configs(self) -> Dict[str, APIConfig]:
        api_urls = get_api_urls()
        if not api_urls:
            raise ValueError("API URLs configuration not found")

        return {
            "hotels": APIConfig(base_url=api_urls["base_url"]),
            "activities": APIConfig(base_url=api_urls["base_url"]),
            "landmarks": APIConfig(base_url=api_urls["base_url"]),
            "plans": APIConfig(base_url=api_urls["base_url"])
        }

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get all required slots
            city_name = tracker.get_slot("state")
            budget = tracker.get_slot("budget")
            duration = tracker.get_slot("duration")
            hotel_features = tracker.get_slot("hotel_features")
            landmarks_activities = tracker.get_slot("landmarks_activities")
            user_message = tracker.get_slot("user_message") or {}
            landmarks_activities_msg = user_message.get('landmarks_activities', '')

            # Validate required slots
            if not all([city_name, budget, duration]):
                dispatcher.utter_message("Missing required information. Please provide all necessary details.")
                return []

            # Initialize API clients
            hotels_client = APIClient(self.api_configs["hotels"])
            activities_client = APIClient(self.api_configs["activities"])
            landmarks_client = APIClient(self.api_configs["landmarks"])
            plans_client = APIClient(self.api_configs["plans"])

            # Get recommendations
            recommended_hotels = self._get_recommended_hotels(hotels_client, city_name, duration, budget, hotel_features)
            recommended_activities = self._get_recommended_activities(activities_client, city_name, landmarks_activities_msg, landmarks_activities)
            recommended_landmarks = self._get_recommended_landmarks(landmarks_client, city_name, landmarks_activities_msg, landmarks_activities)

            # Generate plan
            plan = self._generate_plan(plans_client, city_name, budget, duration, recommended_hotels, recommended_activities, recommended_landmarks)

            if plan and plan.plan_combinations:
                self._format_and_send_plans(dispatcher, plan.plan_combinations)
            else:
                dispatcher.utter_message(
                    "Sorry, we couldn't find any plans matching your preferences. Try to adjust your budget or duration."
                )

        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            dispatcher.utter_message("Sorry, there was an error communicating with our services. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected error in SuggestPlan: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing your plan request. Please try again.")
        return []

    def _get_recommended_hotels(self, client: APIClient, city_name: str, duration: int, budget: float, hotel_features: List[str]) -> List[Hotel]:
        try:
            response = client._make_request(
                "POST",
                "/hotels/search",
                json={
                    "city_name": city_name,
                    "duration": duration,
                    "budget": budget,
                    "user_facilities": hotel_features or [],
                }
            )
            hotels = []
            for hotel_data in response.get("hotels", []):
                try:
                    # Convert facilities_ids to a facility list if needed
                    if "facilities_ids" in hotel_data:
                        hotel_data["facilities"] = hotel_data.get("facilities", [])
                    hotels.append(Hotel(**hotel_data))
                except Exception as e:
                    logger.error(f"Error parsing hotel data: {str(e)}")
                    continue
            return hotels
        except Exception as e:
            logger.error(f"Error fetching hotels: {str(e)}")
            return []

    def _get_recommended_activities(self, client: APIClient, city_name: str, user_message: str, preferred_activities: List[str]) -> List[Activity]:
        try:
            response = client._make_request(
                "POST",
                "/activities/search",
                json={
                    "city_name": city_name,
                    "user_message": user_message or "",
                    "preferred_activities": preferred_activities or []
                }
            )
            activities = []
            for activity_data in response.get("activities", []):
                try:
                    activities.append(Activity(**activity_data))
                except Exception as e:
                    logger.error(f"Error parsing activity data: {str(e)}")
                    continue
            return activities
        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            return []

    def _get_recommended_landmarks(self, client: APIClient, city_name: str, user_message: str, preferred_activities: List[str]) -> List[Landmark]:
        try:
            response = client._make_request(
                "POST",
                "/landmarks/search",
                json={
                    "city_name": city_name,
                    "user_message": user_message or "",
                    "preferred_landmarks": preferred_activities or []
                }
            )
            landmarks = []
            for landmark_data in response.get("landmarks", []):
                try:
                    landmarks.append(Landmark(**landmark_data))
                except Exception as e:
                    logger.error(f"Error parsing landmark data: {str(e)}")
                    continue
            return landmarks
        except Exception as e:
            logger.error(f"Error fetching landmarks: {str(e)}")
            return []

    def _generate_plan(self, client: APIClient, city_name: str, budget: float, duration: int, 
                      hotels: List[Hotel], activities: List[Activity], landmarks: List[Landmark]) -> Optional[PlanResponse]:
        try:
            request_payload = {
                "city_name": city_name,
                "budget": budget,
                "duration": duration,
                "suggested_hotels": [hotel.dict() for hotel in hotels],
                "suggested_activities": [activity.dict() for activity in activities],
                "suggested_landmarks": [landmark.dict() for landmark in landmarks]
            }
            
            response = client._make_request("POST", "/plans/create", json=request_payload)

            
            # Log the first plan combination if available
            if response.get("plan_combinations"):
                first_plan = response["plan_combinations"][0]
                logger.info(f"First plan hotel: {json.dumps(first_plan.get('hotel', {}), indent=2)}")
                logger.info(f"First plan activities: {json.dumps(first_plan.get('activities', []), indent=2)}")
                logger.info(f"First plan landmarks: {json.dumps(first_plan.get('landmarks', []), indent=2)}")
            
            return PlanResponse(plan_combinations=response.get("plan_combinations", []))
        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            return None

    def _format_and_send_plans(self, dispatcher: CollectingDispatcher, plans: List[Plan]) -> None:
        for i, plan in enumerate(plans, 1):
            message = f"Plan {i}:\n\n"
            
            # Hotel information
            message += f"🏨 Hotel: {plan.hotel.hotel_name}\n"
            message += f"   Price per night: ${plan.hotel.price_per_night}\n"
            message += f"   Facilities: {', '.join(plan.hotel.facilities)}\n\n"
            
            # Activities
            if plan.activities:
                message += "🎯 Activities:\n"
                for activity in plan.activities:
                    message += f"   • {activity.name}\n"
                    message += f"     Duration: {activity.duration} hours\n"
                    message += f"     Price: ${activity.price}\n"
                    message += f"     Description: {activity.description}\n"
            else:
                message += "No activities included in this plan.\n"
            
            # Landmarks
            if plan.landmarks:
                message += "\n🏛️ Landmarks:\n"
                for landmark in plan.landmarks:
                    message += f"   • {landmark.name}\n"
                    message += f"     Price: ${landmark.price}\n"
                    message += f"     Description: {landmark.description}\n"
            else:
                message += "\nNo landmarks included in this plan.\n"
            
            message += f"\n💰 Total Cost: ${plan.total_plan_cost}\n"
            message += "─" * 50 + "\n"
            
            # Convert a Plan object to dictionary for JSON serialization
            plan_dict = {
                "hotel": plan.hotel.dict(),
                "activities": [activity.dict() for activity in plan.activities],
                "landmarks": [landmark.dict() for landmark in plan.landmarks],
                "total_plan_cost": plan.total_plan_cost,
            }
            
            dispatcher.utter_message(message, json_message=json.dumps(plan_dict, indent=2))


