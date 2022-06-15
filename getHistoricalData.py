import pandas as pd
import numpy as np
import time
import datetime
from sendMessage import send_message
import os
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

alertEmail = os.environ.get("ALERT_EMAIL")

test=pd.read_table("raw_laarc_24_194001010000.txt",delim_whitespace=True,  skiprows=6)
#print(test)
df=DataFrame(test)
#print(df)

#print(np.mean('deg-C))
df['mm'].describe()


df['ddd'].describe()

df=df.replace('*',np.nan)
df2=df.dropna(thresh=8)

day_of_year = datetime.datetime.now().timetuple().tm_yday

dayTemp = np.array((df2.loc[(df2.ddd == day_of_year), 'deg-C']))
dayTempNums = pd.to_numeric(dayTemp)
tempConvFunc = lambda x:  x*9/5+32
convTemp = tempConvFunc(dayTempNums)
meanTemp = round(np.nanmean(convTemp),1)
maxTemp = np.nanmax(convTemp)
minTemp = np.nanmin(convTemp)

dayRain = np.array((df2.loc[(df2.ddd == day_of_year), 'in']))
dayRainNums = pd.to_numeric(dayRain)
meanRain = round(np.nanmean(dayRainNums),1)
stdRain = round(np.nanstd(dayRainNums),2)


print(test)

#send_message('test','woot',alertEmail)

