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
        pass


    def validate_duration(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        duration = re.findall(r'(\d+)[\s|\-]([a-z]+)', slot_value)
        if not duration:
            dispatcher.utter_message("Please enter a valid duration")
            return {"duration": None}
        duration = duration[0]
        print(duration)
        if duration[1] in ["day", "days","night","nights",'d']:
            return {"duration": int(duration[0])}
        elif duration[1] in ["week", "weeks", "w"]:
            return {"duration": int(duration[0]) * 7}
        elif duration[1] in ["month", "months", "m"]:
            return {"duration": int(duration[0]) * 30}
        else:
            dispatcher.utter_message("Please enter a valid duration")
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
