import requests
from config_helper import *
import psycopg2

DB_Prams=get_db_params()

conn=psycopg2.connect(**DB_Prams)
cur=conn.cursor()
EMBEDDING_API_URL = get_api_urls().get('embedding')

table_names = [ 'landmarks', 'states', 'trips']
id_names= [ 'landmark_id', 'state_id', 'trip_id']

for i in range(len(table_names)):
    cur.execute(f"select {id_names[i]},description,embedding from {table_names[i]}")
    data = cur.fetchall()

    text_embedding = {}
    j=0
    for raw in data:
        user_msgs_json = {"text": raw[1]}
        response = requests.post(EMBEDDING_API_URL, json=user_msgs_json)
        if raw[2]:
            print(table_names[i]," -> ",raw[0],": raw", j,": done")
            continue
        if response.status_code == 200:
            text_embedding = response.json()
            print(table_names[i]," -> ",raw[0],": raw", j,": ",raw)
            j+=1

            cur.execute(f"update {table_names[i]} set embedding = %s where {id_names[i]} = %s", (text_embedding['embedding'], raw[0]))
            conn.commit()

        else:
            print("Error in embedding API")
            print(response.status_code)
            print(response.text)

            text_embedding = "Error in embedding API"

cur.close()
conn.close()
print("Done")