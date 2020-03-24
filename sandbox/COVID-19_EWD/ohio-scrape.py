import requests
import pandas as pd
import os, errno
from datetime import datetime
from bs4 import BeautifulSoup
import re

today = datetime.date(datetime.now()).strftime("%Y-%m-%d")
directoryName = 'ohio_county_scrapes'
fileName = directoryName + "/" + directoryName + "_" + today + ".csv"

URL = "https://coronavirus.ohio.gov/wps/portal/gov/covid-19/"
r = requests.get(URL) 

r.content

soup = BeautifulSoup(r.content, 'html.parser')
infectedDiv = soup.findAll("div", {"class": "odh-ads__super-script-item"})[0]
deathDiv = soup.findAll("div", {"class": "odh-ads__super-script-item"})[1]
infectedCounties = infectedDiv.text.split(":")[1].strip().split(',')
deathCounties = deathDiv.text.split("**")[1].strip().split(',')

ohioCounties = pd.read_csv('ohio_county_list.csv')
ohioCounties.columns = ['County', 'Coordinates', 'Population']
ohioCounties['County'] = ohioCounties['County'].apply(lambda x: x.split()[0].strip())

confirmedCases = dict()
for county in infectedCounties:
    info = county.split()
    info[0] = info[0].strip()
    info[1] = int(re.match("\((\d+)\)", info[1])[1])
    confirmedCases[info[0]] = info[1]

confirmedDF = pd.DataFrame.from_dict(confirmedCases, orient='index').reset_index()
confirmedDF.columns = ["County", "Confirmed"]

deaths = dict()
for county in deathCounties:
    info = county.split()
    info[0] = info[0].strip()
    info[1] = int(re.match("\((\d+)\)", info[1])[1])
    deaths[info[0]] = info[1]

deathDF = pd.DataFrame.from_dict(deaths, orient='index').reset_index()
deathDF.columns = ["County", "Deaths"]

ohioCounties = ohioCounties.join(confirmedDF.set_index('County'), on='County')
ohioCounties = ohioCounties.join(deathDF.set_index('County'), on='County')
ohioCounties['Latitude'] = ohioCounties['Coordinates'].apply(lambda x: (re.match('Point\(([^()]+)\)', x)[1].split())[1])
ohioCounties['Longitude'] = ohioCounties['Coordinates'].apply(lambda x: (re.match('Point\(([^()]+)\)', x)[1].split())[0])
ohioCounties = ohioCounties.drop(['Coordinates'], axis=1)
ohioCounties = ohioCounties.fillna(0.0)

ohioCounties['Date'] = today
try:
	os.mkdir(directoryName)
except OSError as e:
       if e.errno != errno.EEXIST:
       	  raise
ohioCounties.to_csv(fileName)
