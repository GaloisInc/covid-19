"""
Fetches roughly county-level mobility data on US citizens, from
https://github.com/descarteslabs/DL-COVID-19.

Data:
    date: Date of measurement.
    county: FIPS code of county.
    state: Two-letter state code.
    samples: Sample set size.
    m50: The median of the max-distance mobility for all samples in the specified region.
    m50_index: The percent of normal m50 in the region, with normal m50 defined during 2020-02-17 to 2020-03-07.
"""

from ..util import (cmd_basic_cached, date_latest_daily,
        resolve_date, resolve_state_name)

import io
import pandas as pd
import requests

URL = 'https://github.com/descarteslabs/DL-COVID-19/raw/master/DL-us-mobility-daterow.csv'
UPDATED = date_latest_daily('America/Los_Angeles', hour=18)

## Remote resource code
def _save_url(file_out):
    data = requests.get(URL).text
    file_out.write(data.encode('utf-8'))


def _load_url(file_in):
    return file_in.read().decode('utf-8')


_get_url_data, _update_url_data = cmd_basic_cached(_save_url, _load_url,
        last_update=UPDATED.add(seconds=-1))


## Dataset processing
def _save(file_out):
    data = _get_url_data()
    df = pd.read_csv(io.StringIO(data),
            dtype={'fips': str})
    def update_row(rowdata):
        rowdata['date'] = resolve_date(rowdata['date'])
        fips = rowdata['fips']
        del rowdata['fips']
        if pd.isna(fips):
            fips = None
        else:
            if len(fips) == 2:
                fips = fips + '000'
        rowdata['county'] = fips
        rowdata['state'] = resolve_state_name(rowdata['county'])
        return rowdata
    df = df.apply(update_row, axis=1)
    df.to_pickle(file_out)


def _load(file_in):
    return pd.read_pickle(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)

