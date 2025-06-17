import pandas as pd
import psycopg2
from config_helper import get_db_params

DB_Prams = get_db_params()

table_names = ['activities' , 'landmarks', 'states', 'trips']


try:
    conn = psycopg2.connect(**DB_Prams)
except Exception as e:
    print("Connection failed:", e)
    exit()

# Read data from each table and store in a list
all_data = []
for table in table_names:
    try:
        query = f"SELECT name, description FROM {table};"
        df = pd.read_sql_query(query, conn)
        df['source_table'] = table
        all_data.append(df)
    except Exception as e:
        print(f"Error reading from {table}: {e}")

# Collect all data into a single DataFrame
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv('training_data.csv', index=False)
    print("Data saved to merged_data.csv")
else:
    print("No data exported.")

# Close the connection
conn.close()
