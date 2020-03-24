
import requests
import pandas as pd
import os, errno
from datetime import datetime
import re

today = datetime.date(datetime.now()).strftime("%Y-%m-%d")
directoryName = 'oregon_county_scrapes'
fileName = directoryName + "/" + directoryName + "_" + today + ".csv"

URL = "https://govstatus.egov.com/OR-OHA-COVID-19"
r = requests.get(URL) 

pd.read_html(r.content)[1]

oregonCounties = pd.read_csv('oregon_county_list.csv')
oregonCounties.columns = ['County', 'Coordinates', 'Population']
oregonCounties['County'] = oregonCounties['County'].apply(lambda x: " ".join(x.split()[0:-1]).strip())
oregonCounties['Latitude'] = oregonCounties['Coordinates'].apply(lambda x: (re.match('Point\(([^()]+)\)', x)[1].split())[1])
oregonCounties['Longitude'] = oregonCounties['Coordinates'].apply(lambda x: (re.match('Point\(([^()]+)\)', x)[1].split())[0])
oregonCounties = oregonCounties.drop(['Coordinates'], axis=1)

oregonCleanDF = pd.read_html(r.content)[1].iloc[0:36]
oregonCleanDF['County'] = oregonCleanDF['County'].apply(lambda x: x.strip())
oregonCleanDF.columns = ["County", "Confirmed", "Deaths", "Negative Test Results"]
oregonCleanDF = oregonCleanDF.join(oregonCounties.set_index("County"), on="County")
oregonCleanDF.fillna(0.0)

oregonCleanDF['Date'] = today
try:
	os.mkdir(directoryName)
except OSError as e:
       if e.errno != errno.EEXIST:
       	  raise
oregonCleanDF.to_csv(fileName)
