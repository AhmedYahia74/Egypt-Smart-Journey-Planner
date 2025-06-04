from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import json
import time
from typing import Any, Dict, List, Text
from requests.exceptions import RequestException, Timeout
from config_helper import get_api_urls
import logging
logger = logging.getLogger(__name__)


class SuggestPlan(Action):
    def name(self) -> Text:
        return "action_suggest_plan"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get all required slots
            city_name = tracker.get_slot("state")
            budget = tracker.get_slot("budget")
            duration = tracker.get_slot("duration")
            hotel_features = tracker.get_slot("hotel_features")
            landmarks_activities = tracker.get_slot("landmarks_activities")

            # Safely get landmarks_activities_msg from user_message
            user_message = tracker.get_slot("user_message") or {}
            landmarks_activities_msg = user_message.get('landmarks_activities', '')

            arrival_date = tracker.get_slot("arrival_date")

            # Validate required slots
            if not all([city_name, budget, duration, arrival_date]):
                dispatcher.utter_message("Missing required information. Please provide all necessary details.")
                return []

            # Get API URLs
            api_urls = get_api_urls()
            if not api_urls:
                logger.error("API URLs configuration not found")
                dispatcher.utter_message("Configuration error. Please try again later.")
                return []

            # Get recommended hotels with timeout and retry
            recommended_hotels = self._get_recommended_hotels(
                api_urls.get("suggest_hotels"),
                city_name, duration, budget, hotel_features, arrival_date
            )

            # Get recommended landmarks and activities
            recommended_activities, recommended_landmarks = self._get_recommended_activities_landmarks(
                api_urls.get("suggest_landmarks_activities"),
                city_name, landmarks_activities_msg, landmarks_activities
            )

            # Generate the final plan
            plan = self._generate_plan(
                api_urls.get("suggest_plan"),
                city_name, budget, duration,
                recommended_hotels, recommended_activities, recommended_landmarks
            )

            if plan:
                dispatcher.utter_message(
                    f"Here is a suggested plan for your trip to {city_name}",
                    json_message=json.dumps(plan, indent=2)
                )
            else:
                dispatcher.utter_message(
                    "Sorry, we couldn't find any plans matching your preferences. Try to adjust your budget or duration."
                )

        except Exception as e:
            logger.error(f"Error in SuggestPlan: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing your plan request. Please try again.")
        return []

    def _get_recommended_hotels(self, api_url, city_name, duration, budget, hotel_features, arrival_date):
        if not api_url:
            raise KeyError("'suggest_hotels' key not found in API URLs configuration")

        try:
            response = requests.post(
                api_url,
                json={
                    "city_name": city_name,
                    "duration": duration,
                    "budget": budget,
                    "user_facilities": hotel_features or [],  # Handle None case
                    "arrival_date": arrival_date
                },
                timeout=10  # Add timeout
            )
            response.raise_for_status()
            
            # Validate response data
            data = response.json()
            if not isinstance(data, dict):
                logger.error("Invalid response format: expected dictionary")
                return []
                
            hotels = data.get("hotels", [])
            if not isinstance(hotels, list):
                logger.error("Invalid hotels data: expected list")
                return []
                
            return hotels
        except (RequestException, Timeout) as e:
            logger.error(f"Error fetching hotels: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in _get_recommended_hotels: {str(e)}")
            return []
        

    def _get_recommended_activities_landmarks(self, api_url, city_name, landmarks_activities_msg, landmarks_activities):
        if not api_url:
            raise KeyError("'suggest_landmarks_activities' key not found in API URLs configuration")

        try:
            # Increase timeout to 30 seconds and add retry logic
            max_retries = 3
            retry_delay = 2  # seconds

            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        api_url,
                        json={
                            "city_name": city_name,
                            "user_message": landmarks_activities_msg or "",
                            "preferred_activities": landmarks_activities or []
                        },
                        timeout=30  # Increased timeout
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Validate response data
                    if not isinstance(data, dict):
                        logger.error("Invalid response format: expected dictionary")
                        return [], []
                        
                    activities = data.get("activities", [])
                    landmarks = data.get("landmarks", [])
                    
                    if not isinstance(activities, list) or not isinstance(landmarks, list):
                        logger.error("Invalid activities or landmarks data: expected lists")
                        return [], []
                        
                    return activities, landmarks
                except (RequestException, Timeout) as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"Error fetching activities and landmarks after {max_retries} attempts: {str(e)}")
                        return [], []
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    return [], []

        except Exception as e:
            logger.error(f"Unexpected error in _get_recommended_activities_landmarks: {str(e)}")
            return [], []

    def _generate_plan(self, api_url, city_name, budget, duration, hotels, activities, landmarks):
        if not api_url:
            raise KeyError("'suggest_plan' key not found in API URLs configuration")

        try:
            # Validate input data
            if not isinstance(hotels, list) or not isinstance(activities, list) or not isinstance(landmarks, list):
                logger.error("Invalid input data: hotels, activities, and landmarks must be lists")
                return None

            # Log the request payload for debugging
            request_payload = {
                "city_name": city_name,
                "budget": budget,
                "duration": duration,
                "suggested_hotels": hotels,
                "suggested_activities": activities,
                "suggested_landmarks": landmarks
            }
            logger.info(f"Sending plan generation request with payload: {json.dumps(request_payload, indent=2)}")

            response = requests.post(
                api_url,
                json=request_payload,
                timeout=10
            )
            response.raise_for_status()
            
            # Log the response for debugging
            logger.info(f"Plan generation response status: {response.status_code}")
            logger.info(f"Plan generation response body: {response.text}")
            
            # Validate response data
            data = response.json()
            if not isinstance(data, dict):
                logger.error("Invalid response format: expected dictionary")
                return None
                
            # Ensure the plan contains required fields
            required_fields = ["itinerary", "total_cost", "summary"]
            if not all(field in data for field in required_fields):
                logger.error("Missing required fields in plan response")
                return None
                
            return data
        except (RequestException, Timeout) as e:
            logger.error(f"Error generating plan: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in _generate_plan: {str(e)}")
            return None


