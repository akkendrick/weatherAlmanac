import paho.mqtt.client as mqtt
from prometheus_client import start_http_server, Summary, Gauge
import time
import datetime
import sqlite3
import os
import numpy as np
from dotenv import load_dotenv
from sqlite3 import Error
load_dotenv()

############ modify this for your prometheus variables #############
# There are different types of variables accepted by prometheus,
# since these are all point measurements in time, Gauge is the right choice

tempOut = Gauge('outdoor_temperature', 'Weather Station Temperature')
humOut = Gauge('outdoor_humidity', 'Weather Station Humidity')
altOut = Gauge('outdoor_altitude', 'Weather Station Altitude')
presOut = Gauge('outdoor_pressure', 'Weather Station Pressure')
distOut = Gauge('outdoor_distance', 'Weather Station Distance')
rainOut = Gauge('outdoor_rain', 'Weather Station Rain')
windOut = Gauge('outdoor_wind', 'Weather Station Wind')


tempIn = Gauge('indoor_temperature', 'Internal Room Temperature')
humIn = Gauge('indoor_humidity', 'Internal Room Humidity')
presIn = Gauge('indoor_pressure', 'Internal Room Pressure')
distIn = Gauge('indoor_distance', 'Internal Room Distance')
altIn = Gauge('indoor_altitude', 'Internal Room Altitude')
lightIn = Gauge('indoor_light', 'Internal Room Light')
#####################################################################

############ modify this for your mqtt config ##############
MQTT_ADDRESS = os.environ.get("MQTT_ADDRESS")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")
MQTT_TOPIC = 'outdoor/weather/temperature'
MQTT_REGEX = 'home/([^/]+)/([^/]+)'
MQTT_CLIENT_ID = 'Zeus'
########################################################



def on_connect(client, userdata, flags, rc):
    """ Run the following when a client connects"""
    # There are various mqtt connect codes, only needed if debugging
    print('Connected with result code ' + str(rc))
    # Subscribe mqtt to the following variables
    client.subscribe([('outdoor/weather/temperature',1),('outdoor/weather/humidity',1),
                      ('outdoor/weather/altitude',1),('outdoor/weather/pressure',1),
                      ('outdoor/weather/distance',1),('outdoor/weather/rain',1),
                      ('outdoor/weather/wind',1), ('indoor/conditions/temperature',1),('indoor/conditions/humidity',1),
                      ('indoor/conditions/altitude',1),
                      ('indoor/conditions/light',1),('indoor/conditions/pressure',1),
                      ('indoor/conditions/distance',1)])

def process_request(msg):
    """A function to read the published data over mqtt."""

    global sqlToPublish 
    timeVal = datetime.datetime.now()
    # Print the timestep to make sure it is working now 
    print("Current Time:",datetime.datetime.now())
    # Print the message 
    msgStr = str(msg.payload)
    goodMsg = msgStr[2:-1]

    print(msg.topic + ' ' + goodMsg)
    
    try:
        sqlToPublish
    except NameError:
        print('Making SQL message template')
        sqlToPublish = [str(timeVal),'','','','','']

    # Make sure we associate prometheus logs with the correct mqtt variable
    # This publishes the mqtt variables to a prometheus gauge  
    # Also insert the data into the SQLite table 
    if msg.topic ==  'outdoor/weather/temperature':
        tempOut.set(msg.payload)
        sqlToPublish[1] = str(goodMsg)
    elif msg.topic == 'outdoor/weather/humidity':
        humOut.set(msg.payload)
        sqlToPublish[2] = str(goodMsg)
    elif msg.topic == 'outdoor/weather/altitude':
        altOut.set(msg.payload)
        sqlToPublish[4] = str(goodMsg)
    elif msg.topic == 'outdoor/weather/pressure':
        presOut.set(msg.payload)
        sqlToPublish[3] = str(goodMsg)
    elif msg.topic == 'outdoor/weather/distance':
        distOut.set(msg.payload)
    elif msg.topic == 'outdoor/weather/rain':
        sqlToPublish[5] = str(goodMsg)
    elif msg.topic == 'outdoor/weather/wind':
        windOut.set(msg.payload)
    elif msg.topic == 'indoor/conditions/temperature':
        tempIn.set(msg.payload)
    elif msg.topic == 'indoor/conditions/humidity':
        humIn.set(msg.payload)
    elif msg.topic == 'indoor/conditions/pressure':
        presIn.set(msg.payload)
    elif msg.topic == 'indoor/conditions/light':
        lightIn.set(msg.payload)
    else:
        print('Incorrect topic')
    if sqlToPublish[5] != '':
        insert_database(sqlToPublish)
        sqlToPublish = [str(timeVal),'','','','','']

    


def on_message(client, userdata, msg):
    """ Run the following command when a MQTT message is received""" 
    process_request(msg)


def setup_database():
    """Set up the database for storing the data sent by mqtt"""
    databasePath =  os.environ.get("SQL_PATH")
    databasePath = str(databasePath)+"/mqtt.sqlite"
    
    conn = None
    try:
        conn = sqlite3.connect(databasePath)
    except Error as e:
        print(e)

    return conn


def createTable(databasePath):
    """Make the SQLite table if it doesn't exist"""
    # Temp C 
    sql_create_weatherData_table = 'CREATE TABLE IF NOT EXISTS weatherData (id integer PRIMARY KEY,timedat text NOT NULL, temperature text, humidity text, pressure text, altitude text, rain text);'
    conn = setup_database()

    
    # create table
    if conn is not None:
        c = conn.cursor()
        c.execute(sql_create_weatherData_table)
    else:
        print("Error! cannot create the database connection.")


def insert_database(sqlMsg):
    """Save the weather data into a database"""

    databasePath =  os.environ.get("SQL_PATH")
    databasePath = str(databasePath)+"/mqtt.sqlite"
    
    conn = sqlite3.connect(databasePath)
    
    
    sql  ='INSERT INTO weatherData (timedat, temperature, humidity, pressure, altitude, rain) values(?,?,?,?,?,?)'

    cur = conn.cursor()
    cur.execute(sql, sqlMsg) 
    conn.commit()

    



def main():
    # Start the Prometheus server
    start_http_server(8000)
    # Setup the SQLlite database
    databasePath = setup_database()
    createTable(databasePath)

    # Start mqtt client
    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    # Specify what programs to call when mqtt conditions are met
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    # Setup mqtt on a port
    mqtt_client.connect(MQTT_ADDRESS, 1883)
    # Keep running forever
    mqtt_client.loop_forever()


if __name__ == '__main__':
    main()
