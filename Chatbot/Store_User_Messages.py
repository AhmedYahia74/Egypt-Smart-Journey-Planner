from rasa_sdk import Tracker
import psycopg2
from DB_config import *
import json


class Store_User_Messages:
    def __init__(self):
        self.user_messages = []

    def store_user_message(self, tracker: "Tracker"):
        print("Storing user message...")

        conversation_id = 123 #tracker.sender_id  # need to be changed in future
        print("Conversation ID: ", conversation_id)
        slot_values = {}
        for slot in tracker.slots:
            value = tracker.slots[slot]
            if value:
                # check if slot value is list or not
                if isinstance(value, list):
                    slot_values[slot] = value
                else:
                    slot_values[slot] = str(value)

        if not slot_values:
            return []
        # get the latest user message if any slot value is predicted
        user_msg = tracker.latest_message.get('text', '')

        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**db)
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
            #
            print("Before Saved Messages: ", saved_msgs)
            for key, value in slot_values.items():
                if key == "requested_slot":
                    continue
                # if the user message is not saved or the slot value is changed then update the user message
                if key not in saved_msgs or (key in saved_msgs and saved_values[key] != value):
                    saved_msgs[key] = str(user_msg)
                if isinstance(value, list):
                    saved_values[key] = value
                else:
                    saved_values[key] = str(value)

            print("Saved Messages: ", saved_msgs)
            print("Saved Values: ", saved_values)
            print("slot values: ", slot_values)
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
