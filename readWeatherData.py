import sqlite3
from dotenv import load_dotenv
from sqlite3 import Error
load_dotenv()
import pandas as pd
import os
from pandas import DataFrame


def connect_db():
    """Set up the database for storing the data sent by mqtt"""
    databasePath =  os.environ.get("SQL_PATH")
    databasePath = str(databasePath)+"/mqtt.sqlite"
    
    conn = None
    try:
        conn = sqlite3.connect(databasePath)
    except Error as e:
        print(e)

    return conn



#Retrive database path
databasePath =  os.environ.get("SQL_PATH")
databasePath = str(databasePath)+"/mqtt.sqlite"
conn = connect_db()
#print(conn)
#select_all_tasks(conn)


# Read sqlite query results into a pandas DataFrame
weather_df = pd.read_sql_query("SELECT timedat, temperature, humidity, pressure, rain FROM weatherData order by id desc LIMIT 150", conn)
#print(weather_df)
weather_df['temperature'] = weather_df['temperature'].astype(float)
weather_df['humidity'] = weather_df['humidity'].astype(float)
weather_df['pressure'] = weather_df['pressure'].astype(float)
weather_df['rain'] = weather_df['rain'].astype(float)

print(round(weather_df['temperature'].mean(),2))
print(round(sum(weather_df['rain']),2))
