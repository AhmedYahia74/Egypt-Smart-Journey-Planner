import requests
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted
from typing import Any, Text, Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Store_User_Messages import Store_User_Messages
from word2number import w2n
from config_helper import get_db_params, get_api_urls
import psycopg2
import re
import logging

logging.basicConfig(level=logging.DEBUG)
print("✅ Custom Action Server is running...")  # Debugging message

DB_Prams=get_db_params()
store_msgs=Store_User_Messages()

def fetch_cities_from_database():
    conn=None
    cur=None
    cities_names = []
    try:
        conn=psycopg2.connect(**DB_Prams)
        cur=conn.cursor()
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
        required_slots=[]


        if tracker.get_slot("state") is None and tracker.get_slot("specify_place") is None:
            required_slots.append("specify_place")
        if tracker.get_slot("specify_place") is True:
            required_slots.append("state")
        elif tracker.get_slot("specify_place") is False :
            required_slots.append( "city_description")

        required_slots.extend([ "budget", "duration", "arrival_date", "hotel_features", "landmarks_activities"])

        return required_slots



    def validate_specify_place(self,
                            slot_value: Any,
                            dispatcher: CollectingDispatcher,
                            tracker: Tracker,
                            domain: Dict[Text, Any]) -> Dict[Text, Any]:

        intent=tracker.latest_message['intent'].get('name')
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
        country = tracker.get_slot("state")
        if country.lower() in [city.lower() for city in CITIES_NAMES]:
            return {"state": country}
        else:
            dispatcher.utter_message("Sorry, we don't have Trips in this city, Can you choose another destination?")
            return {"state": None}

    def validate_weather_preference(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                    domain: Dict[Text, Any]) -> Dict[Text, Any]:
        store_msgs.store_user_message("weather_preference", slot_value, tracker.latest_message.get('text', ''),
                                      tracker.sender_id)
        return {"weather_preference": slot_value}

    def validate_city_description(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker,
                                      domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            response = requests.get(get_api_urls()["suggest_city"], params={"user_msgs": slot_value})
            if response.status_code == 200:
                buttons = [{"title": city['name'], "payload": f"/inform{{\"state\": \"{city['name']}\"}}"} for city in
                           response.json()["top_cities"]]
                dispatcher.utter_message(text="Here are some suggested cities that may suit you", buttons=buttons)
                store_msgs.store_user_message("city_description", slot_value, tracker.latest_message.get('text', ''),
                                              tracker.sender_id)
                return {"city_description": slot_value}
            else:
                dispatcher.utter_message("Sorry, I couldn't process your city description. Please try again.")
                return {"city_description": None}
        except Exception as e:
            dispatcher.utter_message(
                f"Something went wrong while processing your city description. Please try again. Error: {str(e)}")
            return {"city_description": None}

    def validate_budget(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
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
                dispatcher.utter_message("Sorry, we don't have any trips available within your budget. Please try a higher budget.")
                return {"budget": None}
            store_msgs.store_user_message("budget", budget, tracker.latest_message.get('text', ''), tracker.sender_id)

            return {"budget": budget}

        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing the budget. Please try again.")
            return {"budget": None}

    def is_trip_available_within_budget(self, budget: float) -> bool:

        # Replace this with actual logic to check if there are trips within the budget

        return budget >= 100

    def validate_duration(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
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
            store_msgs.store_user_message("duration", duration_days, tracker.latest_message.get('text', ''), tracker.sender_id)

            return {"duration": duration_days}

        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing the duration. Please try again.")
            return {"duration": None}

    # Validate the arrival date
    def validate_arrival_date(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:

        try:
            date_or_range = self.parse_flexible_date(slot_value)

            if not date_or_range:
                dispatcher.utter_message("Please enter a valid date or time frame (e.g., 'next week', '15th October', 'summer').")
                return {"arrival_date": None}

            if isinstance(date_or_range, datetime):
                if date_or_range < datetime.now():
                    dispatcher.utter_message("The arrival date cannot be in the past. Please enter a future date or time frame.")
                    return {"arrival_date": None}
                unified_date = date_or_range.strftime("%Y-%m-%d")
            else:
                start_date, end_date = date_or_range
                if start_date < datetime.now():
                    dispatcher.utter_message("The arrival date cannot be in the past. Please enter a future date or time frame.")
                    return {"arrival_date": None}
                unified_date = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]

            if not self.is_trip_available_on_date(unified_date):

                dispatcher.utter_message("Sorry, there are no trips available for this date or time frame. Please choose another.")
                return {"arrival_date": None}

            store_msgs.store_user_message("arrival_date", unified_date, tracker.latest_message.get('text', ''), tracker.sender_id)

            return {"arrival_date": unified_date}

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
                "%d %B",     # 15 October (assumes current year)
                "%d %b",     # 15 Oct (assumes current year)
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

    def is_trip_available_on_date(self, date_or_range: Union[str, Tuple[datetime, datetime]]) -> bool:
        """
        Checks if a trip is available on the given date or within the date range.
        Replace this with actual logic to check trip availability.
        """
        return True

    def validate_hotel_features(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        store_msgs.store_user_message("hotel_features", slot_value, tracker.latest_message.get('text', ''), tracker.sender_id)

        return {"hotel_features": slot_value}
    def validate_landmarks_activities(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        store_msgs.store_user_message("landmarks_activities", slot_value, tracker.latest_message.get('text', ''), tracker.sender_id)

        return {"landmarks_activities": slot_value}





class ActionClearChat(Action):
    def name(self) -> Text:
        return "action_clear_chat"

    async def run(self, dispatcher, tracker: Tracker, domain):
        conn=None
        cur=None
        try:
            conn=psycopg2.connect(**DB_Prams)
            cur=conn.cursor()
            cur.execute("UPDATE conversation_data SET user_msgs= %s, slot_values= %s  WHERE conversation_id=%s",(None,None,tracker.sender_id,))
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
                store_msgs.store_user_message(key, tracker.get_slot(key), tracker.latest_message.get('text', ''), tracker.sender_id)