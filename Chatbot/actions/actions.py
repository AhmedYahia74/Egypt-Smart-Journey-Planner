from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
from datetime import datetime


def fetch_cities_from_database() -> List[Text]:
    # Replace with database fetching logic
    return [
        "luxor",
        "cairo",
        "alexandria",
        "aswan",
        "aurghada",
        "aharm el eheikh",
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

    def validate_state(self,
                       slot_value: Any,
                       dispatcher: CollectingDispatcher,
                       tracker: Tracker,
                       domain: Dict[Text, Any]) -> Dict[Text, Any]:

        if slot_value.lower() in [city.lower() for city in CITIES_NAMES]:
            return {"state": slot_value}
        else:
            dispatcher.utter_message("Sorry, we don't have a trip to this city")
            return {"state": None}



    def validate_family_status(self,
                                slot_value: Any,
                                dispatcher: CollectingDispatcher,
                                tracker: Tracker,
                                domain: Dict[Text, Any]) -> Dict[Text, Any]:
        for key, value in FAMILY_STATUS.items():
            if slot_value.lower() in value:
                return {"family_status": key}
        return {"family_status": 'General'}



