import requests
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted
from typing import Any, Text, Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from APIs.suggest_cities_api import suggest_cities
from APIs.suggest_landmarks_activities_api import user_message
from Store_User_Messages import Store_User_Messages
from word2number import w2n
from config_helper import get_db_params, get_api_urls
import psycopg2
import re
import logging

logging.basicConfig(level=logging.DEBUG)
print("✅ Custom Action Server is running...")  # Debugging message

DB_Prams = get_db_params()
store_msgs = Store_User_Messages()


def fetch_cities_from_database():
    conn = None
    cur = None
    cities_names = []
    try:
        conn = psycopg2.connect(**DB_Prams)
        cur = conn.cursor()
        cur.execute("SELECT * FROM states")
        for row in cur:
            cities_names.append(row[1])
        return cities_names
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return cities_names


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
        required_slots = []

        if tracker.get_slot("state") is None and tracker.get_slot("specify_place") is None:
            required_slots.append("specify_place")
        if tracker.get_slot("specify_place") is True:
            required_slots.append("state")
        elif tracker.get_slot("specify_place") is False:
            required_slots.append("city_description")

        required_slots.extend(["budget", "duration", "arrival_date", "hotel_features", "landmarks_activities"])

        return required_slots

    def validate_specify_place(self,
                               slot_value: Any,
                               dispatcher: CollectingDispatcher,
                               tracker: Tracker,
                               domain: Dict[Text, Any]) -> Dict[Text, Any]:

        intent = tracker.latest_message['intent'].get('name')
        if intent == "deny":
            return {"specify_place": False}
        elif intent == "affirm":
            return {"specify_place": True}
        return {"specify_place": None}

    def validate_state(self,
                       slot_value: Any,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any]) -> Dict[Text, Any]:
        city = tracker.get_slot("state") or slot_value
        user_messages = tracker.get_slot("user_message")
        if city.lower() in [city.lower() for city in CITIES_NAMES]:
            user_messages["state"] = tracker.latest_message.get('text', '')
            return {"state": city, "user_message": [user_messages]}
        else:
            dispatcher.utter_message("Sorry, we don't have Trips in this city, Can you choose another destination?")
            return {"state": None}

    def validate_city_description(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                  domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            suggest_cities_url = get_api_urls().get("suggest_city")
            if not suggest_cities_url:
                raise KeyError("'suggest_cities' key not found in API URLs configuration")
            response = requests.post(
                suggest_cities_url,
                json={
                    "city_description": slot_value
                }
            )
            if response.status_code == 200:
                buttons = [{"title": city['name'], "payload": f"/inform{{\"state\": \"{city['name']}\"}}"} for city in
                           response.json()["top_cities"]]
                dispatcher.utter_message(text="Here are some suggested cities that may suit you", buttons=buttons)
                user_messages = tracker.get_slot("user_message") or {}
                user_messages["city_description"] = tracker.latest_message.get('text', '')
                return {"city_description": slot_value, "user_message": user_messages}
            else:
                dispatcher.utter_message("Sorry, I couldn't process your city description. Please try again.")
                return {"city_description": None}
        except Exception as e:
            dispatcher.utter_message(
                f"Something went wrong while processing your city description. Please try again. Error: {str(e)}")
            return {"city_description": None}

    def validate_budget(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                        domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            match = re.match(r'(\$?\d+|[\w\s-]+)\s*(dollar|dollars|usd)?', slot_value, re.IGNORECASE)
            if not match:
                dispatcher.utter_message("Please enter a valid budget (e.g., '500 dollars', 'one hundred USD').")
                return {"budget": None}

            number_part, currency = match.groups()

            if number_part.startswith('$'):
                number_part = number_part[1:]

            try:
                budget = int(number_part)
            except ValueError:
                try:
                    budget = w2n.word_to_num(number_part)
                except ValueError:
                    dispatcher.utter_message("Please enter a valid number for the budget.")
                    return {"budget": None}

            if budget <= 0:
                dispatcher.utter_message("Please enter a valid positive budget.")
                return {"budget": None}

            if not self.is_trip_available_within_budget(budget):
                dispatcher.utter_message(
                    "Sorry, we don't have any trips available within your budget. Please try a higher budget.")
                return {"budget": None}

            user_message = tracker.get_slot("user_message") or {}
            user_message["budget"] = tracker.latest_message.get('text', '')
            return {"budget": budget, "user_message": user_message}

        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing the budget. Please try again.")
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
        return None

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


class ActionClearChat(Action):
    def name(self) -> Text:
        return "action_clear_chat"

    async def run(self, dispatcher, tracker: Tracker, domain):
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**DB_Prams)
            cur = conn.cursor()
            cur.execute("UPDATE conversation_data SET user_msgs= %s, slot_values= %s  WHERE conversation_id=%s",
                        (None, None, tracker.sender_id,))
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
        return [SlotSet(slot, None) for slot in tracker.slots.keys()] + [Restarted()]


class StoreUserMessages(Action):
    def name(self) -> Text:
        return "action_store_user_messages"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        for key in tracker.slots.keys():
            if tracker.slots[key]:
                store_msgs.store_user_message(key, tracker.get_slot(key), tracker.latest_message.get('text', ''),
                                              tracker.sender_id)


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
            arrival_date = tracker.get_slot("arrival_date")

            # Get API URLs
            api_urls = get_api_urls()

            # Get recommended hotels
            recommended_hotels = []
            hotel_api_url = api_urls.get("suggest_hotels")
            if not hotel_api_url:
                raise KeyError("'suggest_hotels' key not found in API URLs configuration")

            response = requests.post(
                hotel_api_url,
                json={
                    "city_name": city_name,
                    "duration": duration,
                    "budget": budget,
                    "user_facilities": hotel_features,
                    "arrival_date": arrival_date
                }
            )

            if response.status_code == 200:
                hotels_data = response.json()
                if hotels_data:
                    recommended_hotels = hotels_data.get("hotels", [])
                else:
                    dispatcher.utter_message("Sorry, we couldn't find any hotels matching your preferences.")

            # Get recommended landmarks and activities
            recommended_activities = []
            recommended_landmarks = []
            landmarks_activities_api_url = api_urls.get("suggest_landmarks_activities")

            if not landmarks_activities_api_url:
                raise KeyError("'suggest_landmarks_activities' key not found in API URLs configuration")

            user_messages = tracker.get_slot("user_message")
            landmarks_message = ""

            if user_messages:
                # Handle different data structures that might be stored in user_message slot
                if isinstance(user_messages, dict) and 'landmarks_activities' in user_messages:
                    landmarks_message = user_messages['landmarks_activities']
                elif isinstance(user_messages, list) and len(user_messages) > 0:
                    # If it's a list of dictionaries
                    for msg in user_messages:
                        if isinstance(msg, dict) and 'landmarks_activities' in msg:
                            landmarks_message = msg['landmarks_activities']
                            break

            response = requests.post(
                landmarks_activities_api_url,
                json={
                    "city_name": city_name,
                    "user_message": landmarks_message,
                    "preferred_activities": landmarks_activities
                }
            )

            if response.status_code == 200:
                data = response.json()
                recommended_activities = data.get("activities", [])
                recommended_landmarks = data.get("landmarks", [])

                # Use proper string formatting for logging
                print(f"Activities: {recommended_activities}")

                if not recommended_activities and not recommended_landmarks:
                    dispatcher.utter_message(
                        "Sorry, we couldn't find any activities or landmarks matching your preferences.")

            # Generate the final plan
            plan_api_url = api_urls.get("suggest_plan")
            if not plan_api_url:
                raise KeyError("'suggest_plan' key not found in API URLs configuration")

            response = requests.post(
                plan_api_url,
                json={
                    "city_name": city_name,
                    "budget": budget,
                    "duration": duration,
                    "arrival_date": arrival_date,
                    "suggested_hotels": recommended_hotels,
                    "suggested_activities": recommended_activities,
                    "suggested_landmarks": recommended_landmarks
                }
            )

            if response.status_code == 200:
                plan = response.json()
                if plan:
                    print("plan: ", plan)
                    dispatcher.utter_message(f"Here is a suggested plan for your trip to {city_name}:{plan}")

                else:
                    dispatcher.utter_message(
                        "Sorry, we couldn't find any plans matching your preferences. Try to adjust your budget or duration.")
            else:
                dispatcher.utter_message(
                    f"Sorry, I couldn't process your plan request. Status code: {response.status_code}")

        except KeyError as ke:
            dispatcher.utter_message(f"Configuration error: {str(ke)}")
            logging.error(f"API URL configuration error: {str(ke)}")
        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing your plan request. Please try again.")
            logging.error(f"Error in SuggestPlan: {str(e)}")

        return []


