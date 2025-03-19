from rasa_sdk import Tracker
import psycopg2
from DB_config import DB_Prams
import json
class Store_User_Messages:
    def __init__(self):
        self.user_messages = []

    def store_user_message(self,tracker: "Tracker"):
        print("Storing user message...")

        user_id = 1
        conversation_id = 1  # need to be changed in future

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
        # get the latest user message if any slot value is not predicted
        user_msgs = tracker.latest_message.get('text', '')

        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**DB_Prams)
            cur = conn.cursor()

            select_script = 'SELECT user_msgs, slot_values FROM conversation_data where user_id=%s and conversation_id=%s'
            select_values = (user_id, conversation_id)
            cur.execute(select_script, select_values)
            data = cur.fetchone()
            # if data is not empty then append the user message to the existing user messages\
            if data:
                saved_msgs = data[0]
                saved_msgs+=', '+ str(user_msgs) if saved_msgs else str(user_msgs) # append the new user message to the existing user messages
                print(saved_msgs)

                # update the slot values with the new slot values
                update_script = 'UPDATE conversation_data SET user_msgs=%s, slot_values=%s  WHERE user_id=%s and conversation_id=%s'
                update_values = (saved_msgs, json.dumps(slot_values), user_id, conversation_id)

                cur.execute(update_script, update_values)

            else:
                insert_script = 'INSERT INTO conversation_data (user_id, conversation_id, user_msgs, slot_values ) VALUES (%s,%s,%s,%s)'
                insert_values = (user_id, conversation_id, user_msgs, json.dumps(slot_values))
                cur.execute(insert_script, insert_values)

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