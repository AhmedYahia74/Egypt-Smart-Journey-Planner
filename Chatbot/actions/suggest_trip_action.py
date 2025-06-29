from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, ActionExecuted
from config_helper import get_api_urls
import requests
import logging
import json

logger = logging.getLogger(__name__)


class ActionSuggestTrips(Action):
    def name(self) -> Text:
        return "action_suggest_trips"

    def _extract_conversation_context(self, tracker: Tracker) -> Dict[str, Any]:
        try:
            # Extract relevant context from the conversation history.
            context = {}

            # Get all events from the conversation
            events = tracker.events

            # Extract user messages and their intents
            for event in events:
                if event.get('event') == 'user':
                    # Get the intent
                    intent = event.get('parse_data', {}).get('intent', {}).get('name')

                    # Get the text
                    text = event.get('text', '')

                    # Store based on intent
                    if intent == 'request_trip':
                        context['request_trip'] = text
                    elif intent == 'share_state':
                        context['state'] = text
                    elif intent == 'share_budget':
                        context['budget'] = text
                    elif intent == 'describe_city':
                        context['city_description'] = text
                    elif intent == 'share_duration':
                        context['duration'] = text
                    elif intent == 'share_arrival_date':
                        context['arrival_date'] = text
                    elif intent == 'share_landmarks_activities':
                        context['landmarks_activities'] = text
                    elif intent == 'share_hotel_features':
                        context['hotel_features'] = text
            return context
        except Exception as e:
            logger.error(f"Error extracting conversation context: {str(e)}")
            return {}

    def _format_preferences(self, tracker: Tracker) -> Dict[str, Any]:
        # Format explicit preferences from slots.
        preferences = {
            "budget": tracker.get_slot("budget"),
            "duration": tracker.get_slot("duration"),
            "state": tracker.get_slot("state"),
            "arrival_date": tracker.get_slot("arrival_date")
        }

        # Remove Null values
        return {k: v for k, v in preferences.items() if v is not None}

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get explicit preferences from slots
            preferences = {
                "budget": tracker.get_slot("budget"),
                "duration": tracker.get_slot("duration"),
                "state": tracker.get_slot("state"),
                "arrival_date": tracker.get_slot("arrival_date")
            }

            # Get user messages from conversation context
            user_messages = self._extract_conversation_context(tracker)

            try:
                url = f"{get_api_urls()['base_url']}/trips/recommend"
                response = requests.post(
                    url,
                    json={
                        "preferences": preferences,
                        "user_messages": user_messages
                    },
                    timeout=30  # Add a 30-second timeout
                )

                if response.status_code == 200:
                    recommendations = response.json()
                    if not recommendations:
                        dispatcher.utter_message(
                            text="I couldn't find any trips matching your preferences")
                    else:
                        # Format recommendations as custom data
                        for trip in recommendations:
                            custom_data = {
                                'type': 'trip',
                                'data': trip
                            }
                            dispatcher.utter_message(json_message=custom_data)
                elif response.status_code == 404:
                    dispatcher.utter_message(
                        text="I couldn't find any trips matching your preferences")
                else:
                    dispatcher.utter_message(
                        text=f"I'm having trouble finding trip recommendations right now. Error: {response.status_code}")
            except requests.Timeout:
                logger.error("Request timed out while getting trip recommendations")
                dispatcher.utter_message(
                    text="I'm taking longer than expected to find trip recommendations. Please try again in a moment.")
            except requests.RequestException as e:
                logger.error(f"Request error while getting trip recommendations: {str(e)}")
                dispatcher.utter_message(
                    text="I'm having trouble connecting to our trip database. Please try again in a moment.")
            except Exception as e:
                logger.error(f"Unexpected error while getting trip recommendations: {str(e)}")
                dispatcher.utter_message(
                    text="Something went wrong while getting trip recommendations. Please try again.")
        except Exception as e:
            logger.error(f"Error in ActionSuggestTrips: {str(e)}")
            dispatcher.utter_message(text="I'm having trouble processing your request. Please try again.")
        
        return [
            FollowupAction("utter_anything_else"),

        ]