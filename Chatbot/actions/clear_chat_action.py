from typing import Text, Dict, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, Restarted
import psycopg2
from config_helper import get_db_params

DB_Prams = get_db_params()
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