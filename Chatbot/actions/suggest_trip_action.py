from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from config_helper import get_api_urls
import requests

class ActionSuggestTrips(Action):
    def name(self) -> Text:
        return "action_suggest_trips"

    def _extract_conversation_context(self, tracker: Tracker) -> Dict[str, Any]:
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
                if intent =='request_trip':
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
        
        # Get explicit preferences from slots
        preferences = self._format_preferences(tracker)
        
        # Get conversation context
        user_messages = self._extract_conversation_context(tracker)
        
        try:
            url= f"{get_api_urls()['base_url']}/recommend" # Get the base URL from config
            response = requests.post(
                url,  # Updated port and path
                json={
                    "preferences": preferences,
                    "user_messages": user_messages
                }
            )
            
            if response.status_code == 200:
                recommendations = response.json()
                
                if recommendations:
                    # Format and send recommendations
                    message = "Based on your preferences and our conversation, here are some trip suggestions:\n\n"
                    
                    for i, trip in enumerate(recommendations, 1):
                        message += f"{i}. {trip['title']}:\n"
                        message += f"   • Location: {trip['state']}\n"
                        message += f"   • Duration: {trip['duration']}\n"
                        message += f"   • Price: ${trip['price']:.2f}\n"  
                        message += f"   • Available Seats: {trip['available_seats']}\n"
                        message += f"   • Date: {trip['date']}\n"
                        message += f"   • Description: {trip['description']}\n"
                        message += f"   • Match Score: {trip['match_score']}%\n\n"
                    dispatcher.utter_message(text=message)
                else:
                    dispatcher.utter_message(text="I couldn't find any trips matching your preferences. Would you like to try different preferences?")
            elif response.status_code == 404:
                dispatcher.utter_message(text="I couldn't find any trips matching your preferences. Would you like to try different preferences?")
            else:
                dispatcher.utter_message(text=f"I'm having trouble finding trip recommendations right now. Error: {response.status_code}")
                
        except requests.Timeout:
            dispatcher.utter_message(text="The request timed out. Please try again.")
        except requests.RequestException as e:
            dispatcher.utter_message(text=f"I encountered an error while searching for trips: {str(e)}")
        except Exception as e:
            dispatcher.utter_message(text="I encountered an unexpected error. Please try again later.")
        
        return [] 