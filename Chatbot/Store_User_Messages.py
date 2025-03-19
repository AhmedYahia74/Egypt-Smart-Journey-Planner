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
            # if data is not empty then append the user message to the existing user messages
            if data:
                # Safely access tuple elements with proper error handling
                try:
                    if len(data) > 0:
                        saved_msgs = data[0] if data[0] is not None else []
                        if len(data) > 1:
                            saved_slots = json.loads(data[1]) if data[1] is not None else {}
                        else:
                            saved_slots = {}
                        saved_msgs.append(user_msgs)
                    else:
                        saved_msgs = [user_msgs]
                        saved_slots = {}
                except Exception as e:
                    print(f"Error processing database result: {e}")
                    saved_msgs = [user_msgs]
                    saved_slots = {}
                # update the slot values
                for slot, value in saved_slots.items():
                    if isinstance(value, list):
                        # user_intent= tracker.latest_message['intent'].get('name','')
                        # if user_intent == 'add_item':
                        #     saved_slots[slot]= list(set(saved_slots.get(slot,[])+value))
                        # else:
                        saved_slots[slot] = '{' + ','.join(map(str, value)) + '}'
                    else:
                        saved_slots[slot] = str(value)

                print(f"User ID: {user_id}, Conversation ID: {conversation_id}")
                print(f"User Messages: {user_msgs}")
                print(f"Slot Values: {slot_values}")

                # update the slot values with the new slot values
                print(f"Update Slot Values: {saved_slots}")

                update_script = 'UPDATE conversation_data SET user_msgs=%s, slot_values=%s  WHERE user_id=%s and conversation_id=%s'
                update_values = (saved_msgs, json.dumps(saved_slots), user_id, conversation_id)

                cur.execute(update_script, update_values)

            else:
                insert_script = 'INSERT INTO conversation_data (user_id, conversation_id, user_msgs, slot_values ) VALUES (%s,%s,%s,%s)'
                insert_values = (user_id, conversation_id, [user_msgs], json.dumps(slot_values))
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