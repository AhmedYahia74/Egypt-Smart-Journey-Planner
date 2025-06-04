import requests
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted, FollowupAction
from typing import Any, Text, Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging
from requests.exceptions import RequestException, Timeout
from contextlib import contextmanager
import time
from word2number import w2n
from config_helper import get_db_params, get_api_urls
import psycopg2
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_Prams = get_db_params()

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_Prams)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def fetch_cities_from_database():
    # Fetch cities from database
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM states")
                return [row[1] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching cities: {str(e)}")
        return []

CITIES_NAMES = fetch_cities_from_database()


class ValidateTripForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_trip_form"

    async def required_slots(
            self,
            domain_slots: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: Dict[Text, Any],
    ) -> List[Text]:
        print("=== required_slots called ===")  # Debug print
        print(f"Current slots: {tracker.slots}")  # Debug print
        
        required_slots = []

        # If we don't have specify_place yet, ask for it first
        if tracker.get_slot("specify_place") is None and not tracker.get_slot("state"):
            print("specify_place is None, adding to required_slots")  # Debug print
            required_slots.append("specify_place")
            return required_slots

        # If specify_place is True but no state, ask for state
        if tracker.get_slot("specify_place") and not tracker.get_slot("state"):
            print("specify_place is True but no state, adding state to required_slots")  # Debug print
            required_slots.append("state")
            return required_slots

        # If specify_place is False, ask for city description
        if not tracker.get_slot("specify_place") and not tracker.get_slot("city_description"):
            print("specify_place is False and no city_description, adding city_description to required_slots")  # Debug print
            required_slots.append("city_description")
            return required_slots

        # If we have city description but no selected city, and we're awaiting city selection
        if (tracker.get_slot("city_description") and 
            not tracker.get_slot("selected_city") and
            not tracker.get_slot("state") and
            tracker.get_slot("awaiting_city_selection")):
            print("Have city_description but no selected_city, adding selected_city to required_slots")  # Debug print
            required_slots.append("selected_city")
            return required_slots

        # If we have city description but no state, and we're not awaiting city selection
        if (tracker.get_slot("city_description") and 
            not tracker.get_slot("state") and 
            not tracker.get_slot("awaiting_city_selection")):
            print("Have city_description but no state, validating city_description first")  # Debug print
            return ["city_description"]

        # After we have the state, check for other required slots
        if tracker.get_slot("state"):
            print("State is set, checking other required slots")  # Debug print
            
            # Check each required slot in order
            if not tracker.get_slot("budget"):
                print("Adding budget to required_slots")  # Debug print
                required_slots.append("budget")
            elif not tracker.get_slot("duration"):
                print("Adding duration to required_slots")  # Debug print
                required_slots.append("duration")
            elif not tracker.get_slot("arrival_date"):
                print("Adding arrival_date to required_slots")  # Debug print
                required_slots.append("arrival_date")
            elif not tracker.get_slot("hotel_features"):
                print("Adding hotel_features to required_slots")  # Debug print
                required_slots.append("hotel_features")
            elif not tracker.get_slot("landmarks_activities"):
                print("Adding landmarks_activities to required_slots")  # Debug print
                required_slots.append("landmarks_activities")

        print(f"Final required_slots: {required_slots}")  # Debug print
        return required_slots

    def validate_specify_place(self,
                               slot_value: Any,
                               dispatcher: CollectingDispatcher,
                               tracker: Tracker,
                               domain: Dict[Text, Any]) -> Dict[Text, Any]:
        print("=== validate_specify_place called ===")  # Debug print
        intent = tracker.latest_message['intent'].get('name')
        text = tracker.latest_message.get('text', '').lower()
        print(f"Intent: {intent}, Text: {text}")  # Debug print
        print(f"Entities: {tracker.latest_message.get('entities', [])}")  # Debug print
        print(f"Current slots: {tracker.slots}")  # Debug print

        # First check if there's a state entity
        entities = tracker.latest_message.get('entities', [])
        for entity in entities:
            if entity.get('entity') == 'state':
                state_value = entity.get('value')
                print(f"Found state entity: {state_value}")  # Debug print
                if state_value.lower() in [city.lower() for city in CITIES_NAMES]:
                    print(f"State {state_value} is valid")  # Debug print
                    return {
                        "specify_place": True,
                        "state": state_value,
                        "requested_slot": "budget"
                    }
        
        # Handle other intents
        if intent == "affirm":
            print("Handling affirm intent")  # Debug print
            # Check if there's a city mentioned in the text
            for city in CITIES_NAMES:
                if city.lower() in text:
                    return {
                        "specify_place": True,
                        "state": city,
                        "requested_slot": "budget"
                    }
            # If no city was mentioned, just set specify_place to True
            return {
                "specify_place": True,
                "requested_slot": "state"
            }
        elif intent == "deny":
            print("Handling deny intent")  # Debug print
            return {
                "specify_place": False,
                "requested_slot": "city_description"
            }
        
        # If we get here, check if there's a city in the text
        for city in CITIES_NAMES:
            if city.lower() in text:
                return {
                    "specify_place": True,
                    "state": city,
                    "requested_slot": "budget"
                }
        
        print("No valid conditions met, returning None")  # Debug print
        return {"specify_place": None}

    def validate_city_description(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                  domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            print("=== validate_city_description called ===")  # Debug print
            print(f"City description: {slot_value}")  # Debug print
            print(f"Current slots: {tracker.slots}")  # Debug print
            
            suggest_cities_url = get_api_urls().get("suggest_city")
            print(f"API URL: {suggest_cities_url}")  # Debug print
            
            if not suggest_cities_url:
                print("No API URL found for suggest_city")  # Debug print
                raise KeyError("'suggest_cities' key not found in API URLs configuration")
            
            print("Making API request...")  # Debug print
            response = requests.post(
                suggest_cities_url,
                json={
                    "city_description": slot_value
                }
            )
            print(f"API Response status: {response.status_code}")  # Debug print
            print(f"API Response content: {response.text}")  # Debug print
            
            if response.status_code == 200:
                suggested_cities = response.json().get("top_cities", [])
                print(f"Suggested cities: {suggested_cities}")  # Debug print
                
                if suggested_cities:
                    # Format the cities for display
                    suggested_cities_msg = "\n".join(
                        [f"{i+1}. {city['name']} - {city['description']}" for i, city in enumerate(suggested_cities)]
                    )
                    print(f"Formatted message: {suggested_cities_msg}")  # Debug print
                    
                    dispatcher.utter_message(text=f"Here are some suggested cities that may suit you:\n{suggested_cities_msg}")
                    dispatcher.utter_message(text="Please choose one of these cities for your trip.")
                    
                    # Store just the city names in the suggested_cities slot
                    city_names = [city['name'] for city in suggested_cities]
                    
                    # Store the city description and set awaiting_city_selection to true
                    return {
                        "city_description": slot_value,
                        "suggested_cities": city_names,
                        "awaiting_city_selection": True,
                        "requested_slot": "selected_city"  # Request the selected_city slot
                    }
                else:
                    print("No cities found in response")  # Debug print
                    dispatcher.utter_message("Sorry, I couldn't find any cities matching your description. Please try again.")
                    return {"city_description": None}
            else:
                print(f"API request failed with status {response.status_code}")  # Debug print
                dispatcher.utter_message("Sorry, I couldn't process your city description. Please try again.")
                return {"city_description": None}
        except Exception as e:
            print(f"Error in validate_city_description: {str(e)}")  # Debug print
            dispatcher.utter_message(
                f"Something went wrong while processing your city description. Please try again. Error: {str(e)}")
            return {"city_description": None}

    def validate_selected_city(self,
                       slot_value: Any,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any]) -> Dict[Text, Any]:
        print("=== validate_selected_city called ===")  # Debug print
        print(f"Slot value: {slot_value}")  # Debug print
        print(f"Current slots: {tracker.slots}")  # Debug print
        
        # Get the city from either the slot value or the latest message
        city = slot_value or tracker.latest_message.get('text', '').strip()
        print(f"Processing city: {city}")  # Debug print
        
        # Get suggested cities
        suggested_cities = tracker.get_slot("suggested_cities") or []
        print(f"Suggested cities: {suggested_cities}")  # Debug print
        
        # Check if the user's input matches any of the suggested cities
        for suggested_city in suggested_cities:
            if city.lower() == suggested_city.lower():
                print(f"Valid city found: {city}")  # Debug print
                user_messages = tracker.get_slot("user_message") or {}
                user_messages["state"] = tracker.latest_message.get('text', '')
                return {
                    "selected_city": suggested_city,  # Use the exact city name from suggestions
                    "state": suggested_city,  # Also set the state slot
                    "user_message": user_messages,
                    "awaiting_city_selection": False,
                    "requested_slot": "budget"
                }
        
        # If no match found, ask the user to choose from the suggested cities
        dispatcher.utter_message("Please choose one of the suggested cities.")
        return {"selected_city": None}

    def validate_state(self,
                       slot_value: Any,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any]) -> Dict[Text, Any]:
        print("=== validate_state called ===")  # Debug print
        print(f"Slot value: {slot_value}")  # Debug print
        print(f"Current slots: {tracker.slots}")  # Debug print
        
        # Get the city from either the slot value or the latest message
        city = slot_value or tracker.latest_message.get('text', '').strip()
        print(f"Processing city: {city}")  # Debug print
        
        # Check if we're awaiting city selection
        if tracker.get_slot("awaiting_city_selection"):
            suggested_cities = tracker.get_slot("suggested_cities") or []
            print(f"Suggested cities: {suggested_cities}")  # Debug print
            
            # Check if the user's input matches any of the suggested cities
            for suggested_city in suggested_cities:
                if city.lower() == suggested_city.lower():
                    print(f"Valid city found: {city}")  # Debug print
                    user_messages = tracker.get_slot("user_message") or {}
                    user_messages["state"] = tracker.latest_message.get('text', '')
                    return {
                        "state": suggested_city,  # Use the exact city name from suggestions
                        "user_message": user_messages,
                        "awaiting_city_selection": False,
                        "requested_slot": "budget"
                    }
            
            # If no match found, ask the user to choose from the suggested cities
            dispatcher.utter_message("Please choose one of the suggested cities.")
            return {"state": None}
        
        # If not awaiting selection, check if the city is in our list of valid cities
        if city.lower() in [city.lower() for city in CITIES_NAMES]:
            print(f"Valid city found: {city}")  # Debug print
            user_messages = tracker.get_slot("user_message") or {}
            user_messages["state"] = tracker.latest_message.get('text', '')
            return {
                "state": city,
                "user_message": user_messages,
                "requested_slot": "budget"
            }
        else:
            print(f"Invalid city: {city}")  # Debug print
            dispatcher.utter_message("Sorry, we don't have Trips in this city. Can you choose another destination?")
            return {"state": None}

    def validate_budget(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                        domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            # Convert slot_value to string if it's not already
            if not isinstance(slot_value, str):
                slot_value = str(slot_value)

            match = re.match(r'(\$?\d+|[\w\s-]+\$?)\s*(dollar|dollars|usd)?', slot_value, re.IGNORECASE)
            if not match:
                dispatcher.utter_message("Please enter a valid budget (e.g., '500 dollars', 'one hundred USD').")
                return {"budget": None}

            number_part, currency = match.groups()

            if number_part.startswith('$'):
                number_part = number_part[1:]
            elif number_part.endswith('$'):
                number_part = number_part[:-1]

            try:
                # First try to convert directly to int
                budget = int(number_part)
            except ValueError:
                try:
                    # If direct conversion fails, try word to number conversion
                    budget = w2n.word_to_num(number_part)
                except ValueError:
                    dispatcher.utter_message("Please enter a valid number for the budget.")
                    return {"budget": None}

            if budget <= 0:
                dispatcher.utter_message("Please enter a valid positive budget.")
                return {"budget": None}

            # Add reasonable budget limits
            if budget > 1000000:  # Example upper limit
                dispatcher.utter_message("Please enter a more reasonable budget amount.")
                return {"budget": None}

            if not self.is_trip_available_within_budget(budget):
                dispatcher.utter_message(
                    "Sorry, we don't have any trips available within your budget. Please try a higher budget.")
                return {"budget": None}

            # Store the user message
            user_message = tracker.get_slot("user_message") or {}
            user_message["budget"] = tracker.latest_message.get('text', '')
            return {"budget": budget, "user_message": user_message}

        except Exception as e:
            logger.error(f"Error validating budget: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing your budget. Please try again.")
            return {"budget": None}

    def is_trip_available_within_budget(self, budget: float) -> bool:

        # Replace this with actual logic to check if there are trips within the budget

        return budget >= 100

    def validate_duration(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                          domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            match = re.match(r'(\d+|[\w\s-]+)\s*(day|week|month|days|weeks|months)', slot_value, re.IGNORECASE)
            if not match:
                dispatcher.utter_message("Please enter a valid duration (e.g., '7 days', 'two weeks', '1 month').")
                return {"duration": None}

            number_part, unit = match.groups()

            try:
                number = int(number_part)
            except ValueError:
                try:
                    number = w2n.word_to_num(number_part)
                except ValueError:
                    dispatcher.utter_message("Please enter a valid number for the duration.")
                    return {"duration": None}

            if unit.lower() in ["day", "days"]:
                duration_days = number
            elif unit.lower() in ["week", "weeks"]:
                duration_days = number * 7
            elif unit.lower() in ["month", "months"]:
                duration_days = number * 30
            else:
                dispatcher.utter_message("Please specify a valid unit (e.g., days, weeks, months).")
                return {"duration": None}

            if duration_days <= 0:
                dispatcher.utter_message("Please enter a valid duration,the duration should be greater than zero.")
                return {"duration": None}
            user_message = tracker.get_slot("user_message") or {}
            user_message["duration"] = tracker.latest_message.get('text', '')
            return {"duration": duration_days, "user_message": user_message}

        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing the duration. Please try again.")
            return {"duration": None}

    # Validate the arrival date
    def validate_arrival_date(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                              domain: Dict[Text, Any]) -> Dict[Text, Any]:

        try:
            date_or_range = self.parse_flexible_date(slot_value)

            if not date_or_range:
                dispatcher.utter_message(
                    "Please enter a valid date or time frame (e.g., 'next week', '15th October', 'summer').")
                return {"arrival_date": None}

            if isinstance(date_or_range, datetime):
                if date_or_range < datetime.now():
                    dispatcher.utter_message(
                        "The arrival date cannot be in the past. Please enter a future date or time frame.")
                    return {"arrival_date": None}
                unified_date = date_or_range.strftime("%Y-%m-%d")
            else:
                start_date, end_date = date_or_range
                if start_date < datetime.now():
                    dispatcher.utter_message(
                        "The arrival date cannot be in the past. Please enter a future date or time frame.")
                    return {"arrival_date": None}
                unified_date = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

            # Store the user message in the slot
            user_messages = tracker.get_slot("user_message") or {}
            user_messages["arrival_date"] = tracker.latest_message.get('text', '')
            return {"arrival_date": unified_date, "user_message": user_messages}

        except Exception as e:

            dispatcher.utter_message("Something went wrong while processing the date. Please try again.")
            return {"arrival_date": None}

    def parse_flexible_date(self, date_input: str) -> Optional[Union[datetime, Tuple[datetime, datetime]]]:
        """
        Parses flexible date inputs like "next week", "15th October", "summer", etc.
        Returns a datetime object (for absolute dates) or a tuple of datetime objects (for date ranges).
        """
        date_input = date_input.lower()
        today = datetime.now()
        # Handle relative dates
        if "next week" in date_input:
            start_date = today + timedelta(weeks=1)
            end_date = start_date + timedelta(days=6)
            return (start_date, end_date)
        elif "next month" in date_input:
            start_date = today + relativedelta(months=1, day=1)
            end_date = start_date + relativedelta(day=31)
            return (start_date, end_date)
        elif "next year" in date_input:
            start_date = today + relativedelta(years=1, month=1, day=1)
            end_date = start_date + relativedelta(month=12, day=31)
            return (start_date, end_date)
        elif "next season" in date_input:
            return self.get_next_season_range(today)
        elif "next quarter" in date_input:
            return self.get_next_quarter_range(today)

        # Handle seasons
        if "summer" in date_input:
            return self.get_season_range(today.year, "summer")
        elif "autumn" in date_input or "fall" in date_input:
            return self.get_season_range(today.year, "autumn")
        elif "winter" in date_input:
            return self.get_season_range(today.year, "winter")
        elif "spring" in date_input:
            return self.get_season_range(today.year, "spring")

        # Handle absolute dates
        absolute_date = self.parse_absolute_date(date_input)
        if absolute_date:
            return absolute_date

        # Handle months
        month_range = self.parse_month_range(date_input)
        if month_range:
            return month_range

        return None

    def parse_absolute_date(self, date_input: str) -> Optional[datetime]:
        """
        Parses absolute dates like "15th October", "1st January", etc.
        Returns a datetime object or None if parsing fails.
        """
        try:
            date_input = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_input)

            # Try parsing with common date formats
            date_formats = [
                "%d %B %Y",  # 15 October 2023
                "%d %b %Y",  # 15 Oct 2023
                "%d %B",  # 15 October (assumes current year)
                "%d %b",  # 15 Oct (assumes current year)
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def parse_month_range(self, date_input: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Parses month names like "March", "June", etc.
        Returns a tuple of datetime objects representing the start and end of the month.
        """
        try:
            month_names = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12,
            }

            for month_name, month_num in month_names.items():
                if month_name in date_input:
                    year = datetime.now().year
                    start_date = datetime(year, month_num, 1)
                    end_date = start_date + relativedelta(day=31)
                    return (start_date, end_date)
            return None
        except Exception:
            return None

    def get_season_range(self, year: int, season: str) -> Tuple[datetime, datetime]:
        """
        Returns the start and end dates of a season for a given year.
        """
        if season == "spring":
            return (datetime(year, 3, 1), datetime(year, 5, 31))
        elif season == "summer":
            return (datetime(year, 6, 1), datetime(year, 8, 31))
        elif season == "autumn":
            return (datetime(year, 9, 1), datetime(year, 11, 30))
        elif season == "winter":
            return (datetime(year, 12, 1), datetime(year + 1, 2, 28))
        else:
            # Default to spring if season is invalid
            return (datetime(year, 3, 1), datetime(year, 5, 31))

    def get_next_season_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """
        Returns the start and end dates of the next season.
        """
        current_month = today.month
        if current_month < 3:
            return (datetime(today.year, 3, 1), datetime(today.year, 5, 31))  # Spring
        elif current_month < 6:
            return (datetime(today.year, 6, 1), datetime(today.year, 8, 31))  # Summer
        elif current_month < 9:
            return (datetime(today.year, 9, 1), datetime(today.year, 11, 30))  # Autumn
        elif current_month < 12:
            return (datetime(today.year, 12, 1), datetime(today.year + 1, 2, 28))  # Winter
        else:
            return (datetime(today.year + 1, 3, 1), datetime(today.year + 1, 5, 31))  # Next spring

    def get_next_quarter_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """
        Returns the start and end dates of the next quarter.
        """
        current_month = today.month
        if current_month < 4:
            return (datetime(today.year, 4, 1), datetime(today.year, 6, 30))
        elif current_month < 7:
            return (datetime(today.year, 7, 1), datetime(today.year, 9, 30))
        elif current_month < 10:
            return (datetime(today.year, 10, 1), datetime(today.year, 12, 31))
        else:
            return (datetime(today.year + 1, 1, 1), datetime(today.year + 1, 3, 31))

    def validate_hotel_features(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                domain: Dict[Text, Any]) -> Dict[Text, Any]:
        user_message = tracker.get_slot("user_message") or {}
        user_message["hotel_features"] = tracker.latest_message.get('text', '')
        return {"hotel_features": slot_value, "user_message": user_message}

    def validate_landmarks_activities(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                      domain: Dict[Text, Any]) -> Dict[Text, Any]:
        user_message = tracker.get_slot("user_message") or {}
        user_message["landmarks_activities"] = tracker.latest_message.get('text', '')
        return {"landmarks_activities": slot_value, "user_message": user_message}







