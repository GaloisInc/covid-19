"""
Fetches county-level data from the NYTimes repo at
https://github.com/nytimes/covid-19-data/blob/master/us-counties.csv

Fields include:
    * date
    * county (encoded as fips)
    * state
    * cases
    * deaths

Seems to be updated daily by 8am PST.
"""

from ..util import cmd_basic_cached, resolve_state, resolve_county

import io
import pandas as pd
import pendulum
import requests

URL = 'https://github.com/nytimes/covid-19-data/raw/master/us-counties.csv'
UPDATED = pendulum.today('America/New_York').add(hours=5)


## URL updating code.
def _save_url(file_out):
    """We don't want to hammer GitHub when we're testing.  So, also wrap
    the web request in a cacher.
    """
    data = requests.get(URL).text
    file_out.write(data.encode('utf-8'))


def _load_url(file_in):
    return file_in.read().decode('utf-8')


_get_url_data, _ = cmd_basic_cached(_save_url, _load_url,
        last_update=UPDATED.add(seconds=-1))


## NYTimes data updating code.
def _save(file_out):
    """Update the dataset.  Should return some format which is saveable
    directly to file.
    """
    data = _get_url_data()
    df = pd.read_csv(io.StringIO(data))
    to_delete = []
    def update_row(rowdata):
        rowdata['state'] = rowstate = resolve_state(rowdata['state'])
        if rowdata['fips'] != rowdata['fips']:
            # NaN value

            if rowstate == 'NY':
                # The NYTimes dataset collapsed all New York City counties into a
                # single county, the New York county.
                #
                # This is a limitation of the dataset.  Collapse into
                # 'New York' county.
                assert rowdata['county'] == 'New York City', rowdata
                rowcounty = resolve_county('New York', state=rowstate)
            elif rowstate == 'MO' and rowdata['county'] == 'Kansas City':
                # Special NYTimes entry.
                to_delete.append(rowdata.name)
                return rowdata
            else:
                assert rowdata['county'] == 'Unknown', rowdata
                # resolve_county has a fix for this.
                rowcounty = resolve_county(rowdata['county'], state=rowstate)
        else:
            rowcounty = resolve_county(rowdata['county'], state=rowstate)
            assert float(rowcounty) == rowdata['fips'], \
                    f'{rowdata["county"]} / {rowdata["fips"]} / {rowdata}'

        rowdata['county'] = rowcounty
        return rowdata

    df = df.apply(update_row, axis=1)
    del df['fips']
    df.drop(to_delete, inplace=True)
    df.to_pickle(file_out)


def _load(file_in):
    return pd.read_pickle(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)

