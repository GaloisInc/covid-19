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

from ..util import (cmd_basic_cached, cmd_url_cached, date_latest_daily,
        resolve_state, resolve_county)

import io
import pandas as pd

URL = 'https://github.com/nytimes/covid-19-data/raw/master/us-counties.csv'
UPDATED = date_latest_daily('America/New_York', hour=5)

## URL updating code.
# We don't want to hammer URLs while we're testing, so wrap the web request
# in a separate cache.
def _url():
    return URL
_get_url_data, _ = cmd_url_cached(_url, last_update=UPDATED.add(seconds=-1))


## NYTimes data updating code.
def _save(file_out):
    """Update the dataset.  Should return some format which is saveable
    directly to file.
    """
    data = _get_url_data().decode('utf-8')
    df = pd.read_csv(io.StringIO(data))
    to_delete = []
    def update_row(rowdata):
        rowdata['state'] = rowstate = resolve_state(rowdata['state'])
        if pd.isna(rowdata['fips']):
            # NaN value

            if rowdata['county'].lower() == 'unknown':
                # resolve_county has a fix for this.
                rowcounty = resolve_county(rowdata['county'], state=rowstate)
            elif rowstate == 'NY':
                # The NYTimes dataset collapsed all New York City counties into a
                # single county, the New York county.
                #
                # This is a limitation of the dataset.  Collapse into
                # 'New York' county.
                assert rowdata['county'] == 'New York City', rowdata
                rowcounty = resolve_county('New York', state=rowstate)
            elif rowstate == 'MO':  #  and rowdata['county'] in ('Kansas City', 'Joplin'):
                # Special NYTimes entries
                to_delete.append(rowdata.name)
                return rowdata
            else:
                raise NotImplementedError(rowdata)
        else:
            if False:
                # Developer debugging -- otherwise, trust the FIPS number provided.
                rowcounty = resolve_county(rowdata['county'], state=rowstate)
                assert float(rowcounty) == rowdata['fips'], \
                        f'{rowdata["county"]} / {rowcounty} / {rowdata}'
            else:
                rowcounty = rowdata['fips']
                if not isinstance(rowcounty, str):
                    rowcounty = f'{int(rowcounty):05d}'

        assert isinstance(rowcounty, str), rowcounty
        assert len(rowcounty) == 5, rowcounty

        rowdata['county'] = rowcounty
        return rowdata

    df = df.apply(update_row, axis=1)
    del df['fips']
    df.drop(to_delete, inplace=True)
    df.to_pickle(file_out)


def _load(file_in):
    return pd.read_pickle(file_in)


get, update = cmd_basic_cached(_save, _load, last_update=UPDATED)

