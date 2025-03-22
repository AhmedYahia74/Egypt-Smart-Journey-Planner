from rasa_sdk import Tracker
import psycopg2
from DB_config import *
import json


class Store_User_Messages:
    def __init__(self):
        self.user_messages = []

    def store_user_message(self, slot_key,slot_value, user_message,conversation_id):
        print("Storing user message...")


        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**DB_Prams)
            cur = conn.cursor()

            select_script = 'SELECT user_msgs, slot_values FROM conversation_data where conversation_id=%s'
            select_values = (conversation_id,)
            cur.execute(select_script, select_values)
            data = cur.fetchone()

            # get the saved messages and values
            saved_msgs = {}
            saved_values = {}
            if data:
                saved_msgs = data[0] if data[0] is not None else {}
                saved_values = data[1] if data[1] is not None else {}

            # if the user message is not saved or the slot value is changed then update the user message
            if slot_key not in saved_msgs or (slot_key in saved_msgs and saved_values[slot_key] != slot_value):
                saved_msgs[slot_key] = str(user_message)
            if isinstance(slot_value, list):
                saved_values[slot_key] = slot_value
            else:
                saved_values[slot_key] = str(slot_value)
            print("saved_msgs",saved_msgs)
            print("saved_values",saved_values)

            # update the slot values with the new slot values
            update_script = 'UPDATE conversation_data SET user_msgs=%s, slot_values=%s  WHERE  conversation_id=%s'
            update_values = (json.dumps(saved_msgs), json.dumps(saved_values), conversation_id)

            cur.execute(update_script, update_values)
            conn.commit()

        except Exception as e:
            print(f"Error in storing user message: {e}")
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                conn.close()
        return []

    def get_user_messages(self):
        return self.user_messages
