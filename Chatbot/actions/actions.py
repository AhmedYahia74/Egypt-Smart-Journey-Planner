from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, Restarted
from typing import Any, Text, Dict, List
from datetime import datetime
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
        elif tracker.get_slot("specify_place") is True:
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
        country = tracker.get_slot("state")
        if country.lower() in [city.lower() for city in CITIES_NAMES]:
            return {"state": country}
        else:
            dispatcher.utter_message("Sorry, we don't have Trips in this city, Can you choose another destination?")
            return {"state": None}


    def validate_budget(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        pass

    def validate_duration(self,
                          slot_value: Any,
                          dispatcher: CollectingDispatcher,
                          tracker: Tracker,
                          domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if not isinstance(slot_value, str):
            dispatcher.utter_message(text="Please enter a valid duration like '5 days' or '1 week'.")
            return {"duration": None}

        duration = re.findall(r'(\d+)[\s|\-]([a-z]+)', slot_value.lower())
        if not duration:
            dispatcher.utter_message("Please specify your trip duration in a format like '7 days' or '2 weeks'.")
            return {"duration": None}

        duration = duration[0]
        print(f"Parsed duration: {duration}")

        # Convert to days
        try:
            amount = int(duration[0])
            unit = duration[1]

            if unit in ["day", "days", "night", "nights", 'd']:
                days = amount
            elif unit in ["week", "weeks", "w"]:
                days = amount * 7
            elif unit in ["month", "months", "m"]:
                days = amount * 30
            else:
                dispatcher.utter_message("Please use days, weeks, or months for your trip duration.")
                return {"duration": None}

            # Some basic validation
            if days < 1:
                dispatcher.utter_message("Trip duration must be at least 1 day.")
                return {"duration": None}
            elif days > 365:  # Arbitrary upper limit
                dispatcher.utter_message("That's quite a long trip! Please confirm your duration.")

            return {"duration": days}
        except (ValueError, IndexError):
            dispatcher.utter_message("I couldn't understand the duration. Please try again.")
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
