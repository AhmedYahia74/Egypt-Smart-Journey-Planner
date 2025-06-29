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
from rasa_sdk.events import SlotSet, FollowupAction, ActionExecuted

# Configure logging
logger = logging.getLogger(__name__)

# Custom exception classes
class APIError(Exception):
    """Base exception for API-related errors"""
    pass

class APITimeoutError(APIError):
    """Exception raised when API request times out"""
    pass

class APIConnectionError(APIError):
    """Exception raised when API connection fails"""
    pass

class Hotel(BaseModel):
    hotel_id: Optional[int] = None
    hotel_name: str
    longitude: float
    latitude: float
    facilities: List[str]
    score: Optional[float] = None
    price_per_night: Optional[float] = None
    img: Optional[str] = None


class Activity(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    score: Optional[float] = None
    price: float
    duration: float
    img: Optional[str] = None
    category: Optional[str] = None


class Landmark(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    score: Optional[float] = None
    price: float
    longitude: float
    latitude: float
    img: Optional[str] = None


class GeneratedPlan(BaseModel):
    hotel: Hotel
    activities: List[Activity]
    landmarks: List[Landmark]
    total_plan_cost: float


class PlanResponse(BaseModel):
    plan: GeneratedPlan
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
                dispatcher.utter_message(
                    "I need some more information to create your travel plan. Please provide the city name, budget, and duration of your stay.")
                return []

            # Initialize API clients
            hotels_client = APIClient(self.api_configs["hotels"])
            activities_client = APIClient(self.api_configs["activities"])
            landmarks_client = APIClient(self.api_configs["landmarks"])
            plans_client = APIClient(self.api_configs["plans"])

            # Get recommendations
            recommended_hotels = self._get_recommended_hotels(hotels_client, city_name, duration, budget,
                                                              hotel_features)
            if not recommended_hotels:
                dispatcher.utter_message(
                    f"I couldn't find any hotels in {city_name} that match your preferences. Try adjusting your budget or hotel features.")
                return []

            recommended_activities = self._get_recommended_activities(activities_client, city_name,
                                                                      landmarks_activities_msg, landmarks_activities)
            recommended_landmarks = self._get_recommended_landmarks(landmarks_client, city_name,
                                                                    landmarks_activities_msg, landmarks_activities)

            if not recommended_activities and not recommended_landmarks:
                dispatcher.utter_message(
                    f"I couldn't find any activities or landmarks in {city_name} that match your preferences. Try adjusting your preferences.")
                return []

            # Generate plan
            plan = self._generate_plan(plans_client, city_name, budget, duration, recommended_hotels,
                                       recommended_activities, recommended_landmarks)

            events = []
            if plan and plan.plan:
                self._format_and_send_plans(dispatcher, plan.plan)
                events.extend([
                    SlotSet("plan_suggested", True)
                ])
            else:
                dispatcher.utter_message(
                    "I'm having trouble creating a plan that matches your preferences. This could be because:\n"
                    "1. The budget might be too low for the duration\n"
                    "2. The selected city might not have enough options\n"
                    "3. The preferences might be too specific\n\n"
                    "Would you like to try adjusting your preferences?"
                )

        except APIError as e:
            logger.error(f"API Error: {str(e)}")
            dispatcher.utter_message(
                "I'm having trouble connecting to our services right now. "
                "Please try again in a few minutes."
            )
        except Exception as e:
            logger.error(f"Unexpected error in SuggestPlan: {str(e)}")
            dispatcher.utter_message(
                "I encountered an unexpected error while creating your plan. "
                "Please try again or contact support if the problem persists."
            )
        return events

    def _get_recommended_hotels(self, client: APIClient, city_name: str, duration: int, budget: float,
                                hotel_features: List[str]) -> List[Hotel]:
        try:
            response = client._make_request(
                "POST",
                "/hotels/recommend",
                json={
                    "city_name": city_name,
                    "duration": duration,
                    "budget": budget,
                    "facilities": hotel_features or [],
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

    def _get_recommended_activities(self, client: APIClient, city_name: str, user_message: str,
                                    preferred_activities: List[str]) -> List[Activity]:
        try:
            response = client._make_request(
                "POST",
                "/activities/recommend",
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

    def _get_recommended_landmarks(self, client: APIClient, city_name: str, user_message: str,
                                   preferred_activities: List[str]) -> List[Landmark]:
        try:
            response = client._make_request(
                "POST",
                "/landmarks/recommend",
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
                       hotels: List[Hotel], activities: List[Activity], landmarks: List[Landmark]) -> Optional[
        PlanResponse]:
        try:
            request_payload = {
                "city_name": city_name,
                "budget": budget,
                "duration": duration,
                "suggested_hotels": [hotel.dict() for hotel in hotels],
                "suggested_activities": [activity.dict() for activity in activities],
                "suggested_landmarks": [landmark.dict() for landmark in landmarks]
            }

            response = client._make_request("POST", "/plans/recommend", json=request_payload)



            if not response or "plan" not in response:
                logger.error("Invalid response from plans API")
                return None

            plan_data = response["plan"]

            # Log the plan data
            logger.info(f"Plan data: {json.dumps(plan_data, indent=2)}")

            # Create the plan response
            plan_response = PlanResponse(
                plan=GeneratedPlan(
                    hotel=Hotel(**plan_data["hotel"]),
                    activities=[Activity(**activity) for activity in plan_data["activities"]],
                    landmarks=[Landmark(**landmark) for landmark in plan_data["landmarks"]],
                    total_plan_cost=plan_data["total_plan_cost"]
                )
            )

            # Log the created plan response
            logger.info(f"Created plan response: {json.dumps(plan_response.dict(), indent=2)}")

            return plan_response

        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            return None

    def _format_and_send_plans(self, dispatcher: CollectingDispatcher, plan: GeneratedPlan) -> None:
        # Convert a Plan object to dictionary for JSON serialization
        plan_dict = {
            "hotel": plan.hotel.dict(),
            "activities": [activity.dict() for activity in plan.activities],
            "landmarks": [landmark.dict() for landmark in plan.landmarks],
            "total_plan_cost": plan.total_plan_cost,
        }

        # Ensure all data is JSON serializable
        plan_dict = json.loads(json.dumps(plan_dict))
        custom_data = {
            'type': 'plan',
            'data': plan_dict
        }
        dispatcher.utter_message(
            json_message=custom_data
        )

