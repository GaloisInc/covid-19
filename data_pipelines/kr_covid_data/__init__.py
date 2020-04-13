from bs4 import BeautifulSoup
import pickle
import ast
import pandas as pd
import re
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
 - active
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

    data_str = str(all_data)

    labels = {'서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju', '대전': 'Daejeon',
              '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi-do', '강원': 'Gangwon-do', '충북': 'Chungcheongbuk-do',
              '충남': 'Chungcheongnam-do', '전북': 'Jeollabuk-do', '전남': 'Jeollanam-do', '경북': 'Gyeongsangbuk-do',
              '경남': 'Gyeongsangnam-do', '제주': 'Jeju-do', '검역': 'Quarantine'}

    # search for each city/province ("광주":{...})
    regions = dict()
    for k, v in labels.items():
        pattern = '[\\\'\\\"]{}[\\\'\\\"]:(.*?)]}}'.format(k)
        string = re.search(pattern, data_str)
        if string:
            regions[v] = ast.literal_eval(string.group(1) + ']}')

    # turn into pandas DataFrame and merge each city on date
    all_regions = False
    for k, v in regions.items():
        temp = pd.DataFrame(v)
        temp['date'] = pd.to_datetime(temp['date'].apply(lambda x: (x + '.2020').replace('.', '/'))).dt.date
        temp = temp.set_index('date')
        if all_regions is False:
            all_regions = temp.add_suffix('_{}'.format(k))
        else:
            all_regions = all_regions.join(temp.add_suffix('_{}'.format(k)))

    # kr total ("KR":{...})
    total = re.search('[\'\"]KR[\'\"]:(.*?)]}', data_str)
    total = ast.literal_eval(total.group(1) + ']}')
    total = pd.DataFrame(total)
    total['date'] = pd.to_datetime(total['date'].apply(lambda x: (x + '.2020').replace('.', '/'))).dt.date
    total = total.set_index('date')

    # testing ("KR":{"chartTesting":{...})
    testing = re.search('KR[\'\"]:{[\'\"]chartTesting[\'\"]:(.*?)]}', data_str)
    testing = ast.literal_eval(testing.group(1) + ']}')
    testing = pd.DataFrame(testing)
    testing['date'] = pd.to_datetime(testing['date'].apply(lambda x: (x + '.2020').replace('.', '/'))).dt.date
    testing = testing.set_index('date')

    kr_data = {'regions': all_regions, 'total': total, 'testing': testing}

    # save dict of dataframes
    pickle.dump(kr_data, file_out)


def _load(file_in):
    return pickle.load(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)
