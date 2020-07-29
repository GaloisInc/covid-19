"""Fetches state-level data from the covidtracking.com API at
https://covidtracking.com/api

Fields include:
    * state -- two-letter code for state.
    * date
    * positive -- positive tests, I believe cumulative
    * negative -- negative tests
    * pending -- pending tests
    * hospitalized -- number of hospitalized cases
    * death -- number o deaths
    * total -- ???
    * fips -- 2-digit fips, dropped in favor of state.

"""

from ..util import (cmd_basic_cached, cmd_url_cached, date_latest_daily,
        resolve_date, resolve_state)

import io
import pandas as pd
import requests

URL = 'http://covidtracking.com/api/states/daily.csv'
UPDATED = date_latest_daily('America/Los_Angeles', hour=13)

def _url():
    return URL
_get_url_data, _ = cmd_url_cached(_url, last_update=UPDATED.add(seconds=-1))

def _save(file_out):
    data = _get_url_data().decode('utf-8')
    df = pd.read_csv(io.StringIO(data), dtype={'date': 'str'})
    def update_row(rowdata):
        rowdata['date'] = resolve_date(rowdata['date'], yearfirst=True,
                nodashes=True)
        rowdata['state'] = resolve_state(rowdata['state'])
        return rowdata
    df = df.apply(update_row, axis=1)
    df = df.drop('fips', axis=1)
    df.to_pickle(file_out)


def _load(file_in):
    return pd.read_pickle(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)

