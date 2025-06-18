from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from Validation_Classes import Date_Parser, Duration_Parser, Budget_Parser

class ActionModifyPreference(Action):
    def name(self) -> Text:
        return "action_modify_preference"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Extract the preference to modify from the latest user message
            entities = tracker.latest_message.get('entities', [])
            modified_slots = {}
            list_slots = {}
            events = []
            modify_field = None

            # First pass: collect all entities
            for entity in entities:
                entity_name = entity.get('entity')
                entity_value = entity.get('value')

                if entity_name == "modify_field":
                    modify_field = entity_value
                    continue

                if entity_name == 'state':
                    if entity_value:
                        modified_slots[entity_name] = entity_value
                        # Update the slot in the tracker
                        events.append(SlotSet(entity_name, entity_value))
                elif entity_name == 'budget':
                    if entity_value:
                        try:
                            budget_parser = Budget_Parser()
                            budget = budget_parser.parse_flexible_budget(entity_value)
                            modified_slots[entity_name] = budget
                            # Update the slot in the tracker
                            events.append(SlotSet(entity_name, budget))
                        except ValueError as e:
                            dispatcher.utter_message(text=str(e))
                            return []
                elif entity_name == 'duration':
                    if entity_value:
                        try:
                            duration_parser = Duration_Parser()
                            duration = duration_parser.parse_flexible_duration(entity_value)
                            modified_slots[entity_name] = duration
                            # Update the slot in the tracker
                            events.append(SlotSet(entity_name, duration))
                        except ValueError as e:
                            dispatcher.utter_message(text=str(e))
                            return []
                elif entity_name == 'arrival_date':
                    if entity_value:
                        try:
                            date_parser = Date_Parser()
                            arrival_date = date_parser.parse_flexible_date(entity_value)
                            
                            if arrival_date:
                                # Handle both single date and date range
                                if isinstance(arrival_date, tuple):
                                    # Date range - use the start date
                                    start_date, end_date = arrival_date
                                    modified_slots[entity_name] = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
                                    events.append(SlotSet(entity_name, [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]))
                                else:
                                    # Single date
                                    modified_slots[entity_name] = [arrival_date.strftime('%Y-%m-%d')]
                                    events.append(SlotSet(entity_name, [arrival_date.strftime('%Y-%m-%d')]))
                            else:
                                dispatcher.utter_message(text="I couldn't understand the date format. Please try again with a valid date (e.g., 'next week', '15th October', 'summer').")
                                return []
                        except ValueError as e:
                            dispatcher.utter_message(text=str(e))
                            return []
                elif entity_name in ["landmarks_activities", "hotel_features"]:
                    if entity_name not in list_slots:
                        list_slots[entity_name] = []
                    # Handle both single values and lists
                    if isinstance(entity_value, list):
                        list_slots[entity_name].extend(entity_value)
                    else:
                        list_slots[entity_name].append(entity_value)

            # If only modify_field is provided without a value
            if modify_field and not modified_slots and not list_slots:
                field_name = modify_field.replace('_', ' ').title()
                dispatcher.utter_message(text=f"What would you like to change your {field_name} to?")
                return []

            # Handle regular slot updates
            if modified_slots:
                if len(modified_slots) > 1:
                    confirmation_message = "I've updated your preferences:\n\n"
                    for slot_name, value in modified_slots.items():
                        formatted_name = slot_name.replace('_', ' ').title()
                        if slot_name == 'arrival_date':
                            if isinstance(value, list) and len(value) == 2:
                                confirmation_message += f"• {formatted_name}: {value[0]} to {value[1]}\n"
                            else:
                                confirmation_message += f"• {formatted_name}: {value[0] if isinstance(value, list) else value}\n"
                        else:
                            confirmation_message += f"• {formatted_name}: {value}\n"
                    dispatcher.utter_message(text=confirmation_message)
                elif len(modified_slots) == 1:
                    slot_name, value = next(iter(modified_slots.items()))
                    formatted_name = slot_name.replace('_', ' ').title()
                    if slot_name == 'arrival_date':
                        if isinstance(value, list) and len(value) == 2:
                            dispatcher.utter_message(text=f"I've updated your {formatted_name} to {value[0]} to {value[1]}")
                        else:
                            dispatcher.utter_message(text=f"I've updated your {formatted_name} to {value[0] if isinstance(value, list) else value}")
                    else:
                        dispatcher.utter_message(text=f"I've updated your {formatted_name} to {value}")
                    events.append(FollowupAction("utter_ask_suggest_after_modify"))

            # Handle list slot updates
            if list_slots:
                list_message = "\nFor your list preferences:\n"
                for slot_name, values in list_slots.items():
                    formatted_name = slot_name.replace('_', ' ').title()
                    unique_values = list(dict.fromkeys(values))
                    values_str = ", ".join(unique_values)
                    list_message += f"• {formatted_name}:\n  - {values_str}\n"
                dispatcher.utter_message(text=list_message)
                events.append(SlotSet("update_list_slots", list_slots))
                dispatcher.utter_message(text="Would you like to add these values to your existing preferences or replace them?")

            return events

        except Exception as e:
            dispatcher.utter_message(text=f"Error modifying preference: {str(e)}")
            return []





class ActionAskAddOrReplace(Action):
    def name(self) -> str:
        return "action_ask_add_or_replace"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Define which slots are list-type and need add/replace choice
        list_slots = ["landmarks_activities", "hotel_features"]

        # The slots that the user wants to modify, stored as a dict in a slot or passed from previous action
        slots_being_updated = tracker.get_slot("update_list_slots") or {}

        slots_to_confirm = {}

        for slot_name, new_values in slots_being_updated.items():
            # Only ask for add/replace if the slot is list type and new values exist
            if slot_name in list_slots and new_values:
                slots_to_confirm[slot_name] = new_values
            elif not new_values:
                dispatcher.utter_message(text=f"What are the new values for {slot_name.replace('_', ' ')}?")
                return []

        if not slots_to_confirm:
            # No list slots to confirm add/replace, so no question needed here
            return []

        # Save slots needing confirmation in a slot, so next action can access it
        events = [SlotSet("update_list_slots", slots_to_confirm)]

        # Ask add or replace question for all at once (you can customize this to ask per slot)
        slot_names_str = ", ".join([s.replace("_", " ") for s in slots_to_confirm.keys()])
        dispatcher.utter_message(
            text=f"You want to update the following list preferences: {slot_names_str}. "
                 "Do you want to add these values to your existing preferences or replace them?"
        )

        return events


class ActionConfirmUpdateListSlot(Action):
    def name(self) -> str:
        return "action_confirm_update_list_slot"

    def run(self, dispatcher, tracker, domain):
        slot = tracker.get_slot("update_list_slots")
        intent = tracker.get_intent_of_latest_message()
        message = ''
        events = []
        
        if not slot:
            dispatcher.utter_message(text="No slots to update.")
            return []
            
        for slot_name, slot_values in slot.items():
            current_values = tracker.get_slot(slot_name) or []
            if intent == "add":
                new_values = list(set(current_values + slot_values))
            elif intent == "replace":
                new_values = slot_values
            else:
                dispatcher.utter_message(text="Sorry, but I didn't understand. Add or replace?")
                return []
                
            if message:
                message += "\n"
                
            slot_msg_name = ''
            if slot_name == "landmarks_activities":
                slot_msg_name = "activities you want to do"
            elif slot_name == "hotel_features":
                slot_msg_name = "your hotel features"

            message += f"✅ {slot_msg_name} updated to: {', '.join(new_values)}\n"
            events.append(SlotSet(slot_name, new_values))
            
        dispatcher.utter_message(text=message)
        events.append(SlotSet("update_list_slots", None))  # Clear the update_list_slots
        return events

class ActionClearPlanSuggestedSlot(Action):
    def name(self) -> Text:
        return "action_clear_plan_suggested_slot"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [SlotSet("plan_suggested", None)]

