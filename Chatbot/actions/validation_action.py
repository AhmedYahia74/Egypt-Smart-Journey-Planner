import requests
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
from datetime import datetime
import logging
from contextlib import contextmanager
from config_helper import get_db_params, get_api_urls
import psycopg2
import sys
import os

# Add the parent directory to the path to import from Validation_Classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Validation_Classes.Budget_Parser import Budget_Parser
from Validation_Classes.Duration_Parser import Duration_Parser
from Validation_Classes.Date_Parser import Date_Parser

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
    # Fetch cities from a database
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
        try:
            required_slots = []

            # If we don't have specify_place yet, ask for it first
            if not tracker.get_slot("state"):
                if tracker.get_slot("specify_place") is None or tracker.get_slot("requested_slot") == "specify_place":
                    required_slots.append("specify_place")
                    return required_slots

                # If specify_place is True but no state, ask for state
                if tracker.get_slot("specify_place"):
                    required_slots.append("state")
                    return required_slots

                # If specify_place is False, ask for city description
                if not tracker.get_slot("specify_place") and not tracker.get_slot("city_description"):
                    required_slots.append("city_description")
                    return required_slots

                # If we have city description but no selected city, and we're awaiting city selection
                if (tracker.get_slot("city_description") and
                        not tracker.get_slot("selected_city") and
                        tracker.get_slot("awaiting_city_selection")):
                    required_slots.append("selected_city")
                    return required_slots
                if (tracker.get_slot("city_description") and
                        not tracker.get_slot("awaiting_city_selection")):
                    return ["city_description"]
            # After we have the state, check for other required slots
            else:
                # Check each required slot in order
                if not tracker.get_slot("budget") or tracker.get_slot("requested_slot") == "budget":
                    required_slots.append("budget")
                if not tracker.get_slot("duration") or tracker.get_slot("requested_slot") == "duration":
                    required_slots.append("duration")
                if not tracker.get_slot("arrival_date") or tracker.get_slot("requested_slot") == "arrival_date":
                    required_slots.append("arrival_date")
                if not tracker.get_slot("hotel_features") or tracker.get_slot("requested_slot") == "hotel_features":
                    required_slots.append("hotel_features")
                if not tracker.get_slot("landmarks_activities") or tracker.get_slot(
                        "requested_slot") == "landmarks_activities":
                    required_slots.append("landmarks_activities")

            return required_slots
        except Exception as e:
            logger.error(f"Error in required_slots: {str(e)}")
            dispatcher.utter_message("I'm having trouble processing your request. Please try again.")
            return []

    @staticmethod
    def validate_specify_place(slot_value: Any,
                               dispatcher: CollectingDispatcher,
                               tracker: Tracker,
                               domain: Dict[Text, Any]) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')
        text = tracker.latest_message.get('text', '').lower()

        # First check if there's a state entity
        entities = tracker.latest_message.get('entities', [])
        for entity in entities:
            if entity.get('entity') == 'state':
                state_value = entity.get('value')
                if state_value.lower() in [city.lower() for city in CITIES_NAMES]:
                    return {
                        "specify_place": True,
                        "state": state_value,
                        "requested_slot": "budget"
                    }

        # Handle other intents
        if intent == "affirm":
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

        return {"specify_place": None}

    def validate_city_description(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        try:
            api_url = get_api_urls()
            if not api_url:
                raise KeyError("'suggest_cities' key not found in API URLs configuration")

            if isinstance(slot_value, str):
                # Common non-Egyptian features to check for
                non_egyptian_features = {
                    'eiffel tower': 'Egypt doesn\'t have the Eiffel Tower, but we have the Great Pyramid of Giza',
                    'great wall': 'Egypt doesn\'t have the Great Wall, but we have the Sphinx and Pyramids',
                    'niagara falls': 'Egypt doesn\'t have Niagara Falls, but we have the Nile River',
                    'grand canyon': 'Egypt doesn\'t have the Grand Canyon, but we have the White Desert',
                    'ski slopes': 'Egypt doesn\'t have ski slopes, but we have beautiful desert landscapes',
                    'volcanoes': 'Egypt doesn\'t have volcanoes, but we have ancient pyramids and temples',
                    'rainforests': 'Egypt doesn\'t have rainforests, but we have the Nile Valley and oases',
                    'polar bears': 'Egypt doesn\'t have polar bears, but we have unique desert wildlife',
                    'northern lights': 'Egypt doesn\'t have northern lights, but we have amazing desert sunsets',
                    'ice hotels': 'Egypt doesn\'t have ice hotels, but we have luxury desert camps',
                    'fjords': 'Egypt doesn\'t have fjords, but we have the beautiful Red Sea coast',
                    'hot springs': 'Egypt doesn\'t have hot springs, but we have natural hot springs in Siwa Oasis',
                    'tulip fields': 'Egypt doesn\'t have tulip fields, but we have beautiful desert flowers',
                    'cherry blossoms': 'Egypt doesn\'t have cherry blossoms, but we have beautiful palm trees',
                    'kangaroos': 'Egypt doesn\'t have kangaroos, but we have unique desert wildlife',
                    'koalas': 'Egypt doesn\'t have koalas, but we have camels and desert animals',
                    'penguins': 'Egypt doesn\'t have penguins, but we have beautiful marine life in the Red Sea',
                    'glaciers': 'Egypt doesn\'t have glaciers, but we have the White Desert',
                    'rainbow mountains': 'Egypt doesn\'t have rainbow mountains, but we have the Colored Canyon',
                    'bamboo forests': 'Egypt doesn\'t have bamboo forests, but we have date palm groves',
                    'giant sequoia trees': 'Egypt doesn\'t have sequoia trees, but we have ancient palm trees',
                    'coral atolls': 'Egypt doesn\'t have coral atolls, but we have the Red Sea coral reefs',
                    'icebergs': 'Egypt doesn\'t have icebergs, but we have the White Desert formations',
                    'polar nights': 'Egypt doesn\'t have polar nights, but we have beautiful desert nights',
                    'midnight sun': 'Egypt doesn\'t have midnight sun, but we have amazing desert sunsets',
                    'geysers': 'Egypt doesn\'t have geysers, but we have natural hot springs',
                    'rainbow lakes': 'Egypt doesn\'t have rainbow lakes, but we have the Magic Lake in Fayoum'
                }

                # Check for non-Egyptian features and provide alternatives
                for feature, alternative in non_egyptian_features.items():
                    if feature.lower() in slot_value.lower():
                        dispatcher.utter_message(f"Note: {alternative}")

            cities_url = f"{api_url['base_url']}/cities/recommend"
            response = requests.post(
                cities_url,
                json={"city_description": slot_value}
            )

            if response.status_code == 200:
                data = response.json()
                suggested_cities = data.get("top_cities", [])

                if suggested_cities:
                    # Format the cities for display with their matched features
                    suggested_cities_msg = []
                    for i, city in enumerate(suggested_cities):
                        features_msg = ", ".join([f"{f['name']}" for f in city.get('matched_features', [])])
                        city_msg = f"{i + 1}. {city['name']} - {city['description']}"
                        if features_msg:
                            city_msg += f"\n   Matches your interests in: {features_msg}"
                        suggested_cities_msg.append(city_msg)
                    message = "Here are some suggested cities that may suit you: " + "\n".join(suggested_cities_msg)
                    print(f"Suggested cities: {message}")
                    dispatcher.utter_message(text=message)
                    dispatcher.utter_message(text="Please choose one of these cities for your trip.")

                    # Store just the city names in the suggested_cities slot
                    city_names = [city['name'] for city in suggested_cities]

                    # Store the city description and set awaiting_city_selection to true
                    return {
                        "city_description": slot_value,
                        "suggested_cities": city_names,
                        "awaiting_city_selection": True,
                        "requested_slot": "selected_city"
                    }
                else:
                    dispatcher.utter_message(
                        "I couldn't find any cities matching your description. Please try describing what you're looking for in terms of historical sites, beaches, desert experiences, or cultural attractions.")
                    return {"city_description": None}
            else:
                dispatcher.utter_message(
                    "Sorry, I couldn't process your city description. Please try again with a different description.")
                return {"city_description": None}

        except Exception as e:
            logger.error(f"Error in validate_city_description: {str(e)}")
            dispatcher.utter_message("I'm having trouble processing your city description. Could you please try again?")
            return {"city_description": None}

    def validate_selected_city(self,
                               slot_value: Any,
                               dispatcher: CollectingDispatcher,
                               tracker: Tracker,
                               domain: Dict[Text, Any]) -> Dict[Text, Any]:

        # Get the city from either the slot value or the latest message
        city = slot_value or tracker.latest_message.get('text', '').strip()

        # Get suggested cities
        suggested_cities = tracker.get_slot("suggested_cities") or []

        # Check if the user's input matches any of the suggested cities
        for suggested_city in suggested_cities:
            if city.lower() == suggested_city.lower():
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
        # Get the city from either the slot value or the latest message
        city = slot_value or tracker.latest_message.get('text', '').strip()

        # Check if we're awaiting city selection
        if tracker.get_slot("awaiting_city_selection"):
            suggested_cities = tracker.get_slot("suggested_cities") or []

            # Check if the user's input matches any of the suggested cities
            for suggested_city in suggested_cities:
                if city.lower() == suggested_city.lower():
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
            user_messages = tracker.get_slot("user_message") or {}
            user_messages["state"] = tracker.latest_message.get('text', '')
            return {
                "state": city,
                "user_message": user_messages,
                "requested_slot": "budget"
            }
        else:
            dispatcher.utter_message("Sorry, we don't have Trips in this city. Can you choose another destination?")
            return {"state": None}

    def validate_budget(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                        domain: Dict[Text, Any]) -> Dict[Text, Any]:
        print("=== validate_budget called ===")
        print(f"Slot value: {slot_value}")
        try:
            parser = Budget_Parser()
            budget = parser.parse_flexible_budget(slot_value)

            # Store the user message
            user_message = tracker.get_slot("user_message") or {}
            user_message["budget"] = tracker.latest_message.get('text', '')
            return {"budget": budget, "user_message": user_message}

        except ValueError as e:
            dispatcher.utter_message(str(e))
            return {"budget": None}
        except Exception as e:
            logger.error(f"Error validating budget: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing your budget. Please try again.")
            return {"budget": None}

    def validate_duration(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                          domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            parser = Duration_Parser()
            duration_days = parser.parse_flexible_duration(slot_value)

            # Store the user message
            user_message = tracker.get_slot("user_message") or {}
            user_message["duration"] = tracker.latest_message.get('text', '')

            return {
                "duration": duration_days,
                "user_message": user_message
            }

        except ValueError as e:
            dispatcher.utter_message(str(e))
            return {"duration": None}
        except Exception as e:
            logger.error(f"Error validating duration: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing the duration. Please try again.")
            return {"duration": None}

    # Validate the arrival date
    def validate_arrival_date(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                              domain: Dict[Text, Any]) -> Dict[Text, Any]:

        try:
            # If slot_value is already a list, it means it's already been processed
            if isinstance(slot_value, list):
                return {"arrival_date": slot_value}
            parser = Date_Parser()
            # If slot_value is a string, process it
            if isinstance(slot_value, str):
                date_or_range = parser.parse_flexible_date(slot_value)

                if not date_or_range:
                    dispatcher.utter_message(
                        "Please enter a valid date or time frame (e.g., 'next week', '15th October', 'summer').")
                    return {"arrival_date": None}

                if isinstance(date_or_range, datetime):
                    if date_or_range < datetime.now():
                        dispatcher.utter_message(
                            "The arrival date cannot be in the past. Please enter a future date or time frame.")
                        return {"arrival_date": None}
                    # Convert single date to a list with one date
                    unified_date = [date_or_range.strftime("%Y-%m-%d")]
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

            dispatcher.utter_message("Please enter a valid date or time frame.")
            return {"arrival_date": None}

        except Exception as e:
            logger.error(f"Error validating arrival date: {str(e)}")
            dispatcher.utter_message("Something went wrong while processing the date. Please try again.")
            return {"arrival_date": None}


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

    async def validate(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        try:
            events = await super().validate(dispatcher, tracker, domain)
            return events
        except Exception as e:
            logger.error(f"Error in validate: {str(e)}")
            dispatcher.utter_message("I'm having trouble processing your request. Please try again.")
            return []

    async def validate_slots(
            self,
            slot_dict: Dict[Text, Any],
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        try:
            return await super().validate_slots(slot_dict, dispatcher, tracker, domain)
        except Exception as e:
            logger.error(f"Error in validate_slots: {str(e)}")
            dispatcher.utter_message("I'm having trouble processing your request. Please try again.")
            return {}

    async def submit(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict]:
        # Your post-form action, e.g. trigger a plan suggestion

        return [
            SlotSet("requested_slot", None),
            ActiveLoop(None),
        ]




