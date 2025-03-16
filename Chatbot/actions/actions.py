from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted
from typing import Any, Text, Dict, List
from datetime import datetime
from word2number import w2n
import re

print("✅ Custom Action Server is running...")  # Debugging message

def fetch_cities_from_database() -> List[Text]:
    # Replace with database fetching logic
    return [
        "luxor",
        "cairo",
        "alexandria",
        "aswan",
        "hurghada",
        "sharm el eheikh",
        "dahab",
        "marsa alam",
        "el gouna",
        "siwa oasis"
    ]


CITIES_NAMES = fetch_cities_from_database()
FAMILY_STATUS = {
    'solo': ["solo traveler", "single traveler"],
    'romantic': ["couple", "honeymoon", "partner"],
    'family': ["family", "kids", "parents", "siblings", "relatives"],
    'group trip': ["group", "friends", "colleagues"],
    'business': ["business", "work", "conference"],
    'pet-friendly trip': ["pet", "dog", "cat", "animal"]
}

class ValidateTripForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_trip_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Text]:
        required_slots=[]


        if tracker.get_slot("state") is None:
            required_slots.append("specify_place")

        if tracker.get_slot("specify_place") is True:
            required_slots.append("state")
        elif tracker.get_slot("specify_place") is False:
            required_slots.append("weather_preference")

        required_slots.extend([ "budget", "duration", "arrival_date", "hotel_features", "landmarks_activities",
                          "family_status"])

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

        if slot_value.lower() in [city.lower() for city in CITIES_NAMES]:
            return {"state": slot_value}
        else:
            dispatcher.utter_message("Sorry, we don't have Trips in this city, Can you choose another destination?")
            return {"state": None}


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
                dispatcher.utter_message("Please enter a valid positive duration.")
                return {"duration": None}

            return {"duration": duration_days}

        except Exception as e:
            dispatcher.utter_message("Something went wrong while processing the duration. Please try again.")
            return {"duration": None}



    # Validate the arrival date
    def validate_arrival_date(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        pass


    def validate_family_status(self,
                                slot_value: Any,
                                dispatcher: CollectingDispatcher,
                                tracker: Tracker,
                                domain: Dict[Text, Any]) -> Dict[Text, Any]:
        for key, value in FAMILY_STATUS.items():
            if slot_value.lower() in value:
                return {"family_status": key}
        return {"family_status": None}

class ActionClearChat(Action):
    def name(self) -> Text:
        return "action_clear_chat"

    async def run(self, dispatcher, tracker: Tracker, domain):
        return [SlotSet(slot, None) for slot in tracker.slots.keys()] + [Restarted()]
