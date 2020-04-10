from bs4 import BeautifulSoup
import pickle
import ast
import pandas as pd
from ..util import cmd_url_cached, cmd_basic_cached, date_latest_daily

"""
Fetches COVID-19 data from a website that compiled data from multiple sources 
but the Korean data is pulled from the KCDC. Aside from the city level data, 
total country and testing data (Korean) is also included. There is 
also province level data, which isn't included but can be pulled out (
unsure of demand). Data includes the following fields:

* acc = accumulated, meaning the sum of all cases to the date
* if acc is not appended, it refers to daily counts

city and total country level data:
 - date
 - quarantine
 - confirmed_acc
 - death_acc
 - released_acc
 - confirmed
 - death
 - released

testing data (for the entire country):
 - date
 - confirm_rate
 - confirmed_acc
 - negative_acc
 - testing
 - confirmed
 - negative

"""

URL = 'https://coronaboard.kr/'
UPDATED = date_latest_daily('Asia/Seoul', hour=0)


def _url():
    return URL


_get_url_data, _ = cmd_url_cached(_url, last_update=UPDATED.add(seconds=-1))


def _save(file_out):
    """
    Saves dict with 3 fields (cities, total, testing):
        - cities: dict with pandas dataframe for each city
        - total: pandas dataframe for the aggregate nation level data
        - testing: pandas dataframe for the aggregate nation level testing data

    """
    # scrape website
    soup = BeautifulSoup(_get_url_data().decode('utf-8'), 'lxml')
    all_data = soup.find_all('script')

    search_str = 'chartForDomestic":'

    for data in all_data:
        # save str version (so that I don't redo this every time)
        data_str = str(data)
        if search_str in data_str:
            break

    # pull out the city level data
    city_data = data_str.split(search_str)[1]
    city_data = city_data.split(',"statByKrLocation')[0]
    city_data = ast.literal_eval(city_data)

    # relabel with English names
    labels = ['Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon',
              'Ulsan', 'Sejong', 'Gyeonggi', 'Gangwon', 'Chungbuk', 'Chungnam',
              'Jeonbuk', 'Jeonnam', 'Gyeongbuk', 'Gyeongnam', 'Jeju',
              'Quarantine']
    labels = list(zip(list(city_data.keys())[1:], labels))
    city_data = {eng: pd.DataFrame(city_data[kor]) for kor, eng in labels}

    # convert str dates to datetime
    for k in city_data.keys():
        temp = pd.DataFrame(city_data[k])
        temp['date'] = pd.to_datetime(
            temp['date'].apply(lambda x: (x + '.2020').replace('.', '/')))
        city_data[k] = temp

    # pull out the testing data
    testing = data_str.split('krTesting":')[1].split(',"age')[0]
    testing = ast.literal_eval(testing)
    testing = pd.DataFrame(testing)
    testing['date'] = pd.to_datetime(
        testing['date'].apply(lambda x: (x + '.2020').replace('.', '/')))

    # pull out the aggregated nation wide data
    kr_total = data_str.split('{"KR":')[1].split(',"global')[0]
    kr_total = ast.literal_eval(kr_total)
    kr_total = pd.DataFrame(kr_total)
    # convert str dates to datetime
    kr_total['date'] = pd.to_datetime(
        kr_total['date'].apply(lambda x: (x + '.2020').replace('.', '/')))

    kr_data = {'cities': city_data, 'total': kr_total, 'testing': testing}

    # convert from dict to dataframes
    # save dict of dataframes
    pickle.dump(kr_data, file_out)


def _load(file_in):
    return pickle.load(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)
