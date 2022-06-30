import pandas as pd
import numpy as np
import datetime
import identifyClouds
from sendMessage import send_message
import os
from dotenv import load_dotenv
from pandas import DataFrame
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import sqlite3
from sqlite3 import Error
import identifyClouds

load_dotenv()

def optFunction(x,a,b,c,d):
    return x**3*a+x**2*b+x*c+d

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

# Load alert email address and weather data
localDir = os.environ.get("LOCAL_DIR")
alertEmail = os.environ.get("ALERT_EMAIL")
os.chdir(localDir)

inputData = pd.read_table("raw_laarc_24_194001010000.txt",delim_whitespace=True,  skiprows=6)
df = DataFrame(inputData)


# Process data to clear out rows of all nans
df = df.replace('*',np.nan)
df2 = df.dropna(thresh=8)

# Determine day of year for weather calculation
day_of_year = datetime.datetime.now().timetuple().tm_yday

# Pull out temperature data and years from dataframe
dayTemp = np.array((df2.loc[(df2.ddd == day_of_year), 'deg-C']))
yearTemp = np.array((df2.loc[(df2.ddd == day_of_year), 'yyyy']))
dayTempNums = pd.to_numeric(dayTemp)

# Convert to Fahrenheit for us imperial noobs
tempConvFunc = lambda x:  x*9/5+32
convTemp = tempConvFunc(dayTempNums)
meanTemp = round(np.nanmean(convTemp),1)
maxTempF = round(np.nanmax(convTemp),1)
minTempF = round(np.nanmin(convTemp),1)

# Plot the temperature data
x=yearTemp
y=convTemp
fit, _ =curve_fit(optFunction,yearTemp,convTemp)
a,b,c,d=fit
# define a sequence of inputs between the smallest and largest known inputs
x_line = np.arange(min(x), max(x), 1)
# calculate the output for the range
y_line = optFunction(x_line, a, b,c,d)
# create a line plot for the mappi

plt.scatter(yearTemp,convTemp)
plt.plot(x_line,y_line,'--',color='red')
plt.title("Past temperature for today's date")
plt.xlabel("Year")
plt.ylabel("Temperature (F)")
plt.savefig('todayTemp.png')

# Identify years corresponding to min/max temp
maxIndex = (np.argmin(abs(convTemp-maxTempF)))
yearTempMax = yearTemp[maxIndex]

minIndex = (np.argmin(abs(convTemp-minTempF)))
yearTempMin = yearTemp[minIndex]

# Look at before and after 1980 to see if it has gotten warmer
compYear = np.argmin(abs(yearTemp - 1980))

earlyMeanTemp = round(np.nanmean(convTemp[0:compYear]),1)
lateMeanTemp = round(np.nanmean(convTemp[compYear:-1]),1)

earlyMaxTemp = round(np.nanmax(convTemp[0:compYear]),1)
lateMaxTemp = round(np.nanmax(convTemp[compYear:-1]),1)

# Pull out range of rain data
dayRain = np.array((df2.loc[(df2.ddd == day_of_year), 'in']))
for i in range(len(dayRain)):
    if float(dayRain[i]) < 0:
        dayRain[i] = float(0)

dayRainNums = pd.to_numeric(dayRain)
maxRain = round(np.nanmax(dayRainNums),1)
stdRain = round(np.nanstd(dayRainNums),2)

maxIndex = (np.argmin(abs(dayRainNums-maxRain)))
yearRainMax = yearTemp[maxIndex]


# Pull out range of snow data
daySnow = np.array((df2.loc[(df2.ddd == day_of_year), 'in.1']))
for i in range(len(daySnow)):
    if float(daySnow[i]) < 0:
        daySnow[i] = float(0)

daySnowNums = pd.to_numeric(daySnow)
maxSnow = round(np.nanmax(daySnowNums),1)

if maxSnow == 0:
    yearSnowMax = np.nan
else:
    maxIndex = (np.argmin(abs(daySnowNums-maxSnow)))
    yearSnowMax = yearTemp[maxIndex]

####################################
# Read yesterday's weather data to send
#Retrive database path
databasePath =  os.environ.get("SQL_PATH")
databasePath = str(databasePath)+"/mqtt.sqlite"
conn = connect_db()
#print(conn)
#select_all_tasks(conn)


# Read sqlite query results into a pandas DataFrame
weather_df = pd.read_sql_query("SELECT timedat, temperature, humidity, pressure, rain FROM weatherData order by id desc LIMIT 300", conn)
#print(weather_df)
weather_df['temperature'] = weather_df['temperature'].astype(float)
weather_df['humidity'] = weather_df['humidity'].astype(float)
weather_df['pressure'] = weather_df['pressure'].astype(float)
weather_df['rain'] = weather_df['rain'].astype(float)
weather_df['temperature'] = tempConvFunc(weather_df['temperature'])

meanMeasTemp = round(weather_df['temperature'].mean(),2)
maxMeasTemp = round(weather_df['temperature'].max(),2)
minMeasTemp = round(weather_df['temperature'].min(),2)

initRain = min(weather_df['rain'])
calibRain = weather_df['rain']-initRain
totalRain = round(sum(calibRain),2)

print(weather_df)
print('Collected weather data:')
print('Mean measured temperature (F): '+str(meanMeasTemp))
print('Total measured rainfall (in): '+str(totalRain))
####################################

# Run ML code
hostFile = identifyClouds.loadTimeStamp()
print(hostFile)

model, class_names = identifyClouds.trainModel()
classID = identifyClouds.identifyClouds(hostFile, model, class_names)
print(classID)

#####################################


# Now send the data in an email
subject = 'Weather Almanac for today'
to = alertEmail
# Format in html
body = "<strong> On this day in history:  </strong> <br>"\
        "<b> Temperature </b> <br>" \
        "The mean temperature is: " + str(meanTemp) + "F <br>"\
        "The max temperature was: " + str(maxTempF) + "F during " + str(yearTempMax)+"<br>"\
        "The min temperature was: " + str(minTempF) + "F during " + str(yearTempMin)+"<br>"\
        "<b> Separating temperature data above and below 1980 to see recent vs past local extremes: </b> <br>"\
        "<br>"\
        "Before 1980 the mean and max temperature were: " + str(earlyMeanTemp)+"F and " + str(earlyMaxTemp) + "F<br>"\
        "After 1980 the mean and max temperature were: " + str(lateMeanTemp)+"F and " + str(lateMaxTemp) + "F<br>"\
        "<br>"\
        "<b> Rain </b> <br>"\
        "The max rainfall was: " + str(maxRain) + "in during " + str(yearRainMax)+"<br>"\
        "<br>"\
        "<b> Snow </b> <br>"\
        "The  snowfall was: " + str(maxSnow) + "in during " + str(yearSnowMax)+"<br>"\
        "<br>"\
        "<strong> Here is what actually happened yesterday:  </strong> <br>"\
        "The mean temperature was: " + str(meanMeasTemp) + "F <br>"\
        "The max temperature was: " + str(maxMeasTemp) + "F" +"<br>"\
        "The min temperature was: " + str(minMeasTemp) + "F" +"<br>"\
        "The rainfall was: " + str(totalRain)+"<br>"\
        "It was "+classID+" yesterday."

send_message(subject,body,to)






