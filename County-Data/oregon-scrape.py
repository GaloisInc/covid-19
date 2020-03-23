
import requests
import pandas as pd
import os, errno
from datetime import datetime

today = datetime.date(datetime.now()).strftime("%Y-%m-%d")
directoryName = 'oregon_county_scrapes'
fileName = directoryName + "/" + directoryName + "_" + today + ".csv"

URL = "https://govstatus.egov.com/OR-OHA-COVID-19"
r = requests.get(URL) 

pd.read_html(r.content)[1]


oregonCleanDF = pd.read_html(r.content)[1].iloc[0:36]
oregonCleanDF.columns = ["County", "Confirmed", "Deaths", "Negative Test Results"]
oregonCleanDF['Date'] = today
try:
	os.mkdir(directoryName)
except OSError as e:
       if e.errno != errno.EEXIST:
       	  raise
oregonCleanDF.to_csv(fileName)