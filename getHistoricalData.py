import pandas as pd
import numpy as np
import datetime
from sendMessage import send_message
import os
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()


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

# Identify years corresponding to min/max temp
maxIndex = (np.argmin(abs(convTemp-maxTempF)))
yearTempMax = yearTemp[maxIndex]

minIndex = (np.argmin(abs(convTemp-minTempF)))
yearTempMin = yearTemp[minIndex]


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

# Now send the data in an email
subject = 'Weather Almanac for today'
to = alertEmail
body = "On this day in history:\n"\
        "-----------------------------------------------------------------\n"\
        "The mean temperature is: " + str(meanTemp) + "F \n"\
        "The max temperature was: " + str(maxTempF) + "F during " + str(yearTempMax)+"\n"\
        "The min temperature was: " + str(minTempF) + "F during " + str(yearTempMin)+"\n"\
        "-----------------------------------------------------------------\n"\
        "The max rainfall was: " + str(maxRain) + "in during " + str(yearRainMax)+"\n"\
        "-----------------------------------------------------------------\n"\
        "The max snowfall was: " + str(maxSnow) + "in during " + str(yearSnowMax)+"\n"

send_message(subject,body,to)

