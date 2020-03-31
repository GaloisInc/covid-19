
from . import settings

import addfips
from dateutil import parser as dateutil_parser
import hashlib
import os
import pendulum
import requests
import threading
import us

_fips = addfips.AddFIPS()
_fip_state_reverse = {}
_fip_county_reverse = {}
def _fip_init():
    global _fip_state_reverse, _fip_county_reverse

    _fip_state_reverse = {v: k for k, v in _fips._states.items()
            if 'a' <= k[0] <= 'z' and len(k) == 2}
    for state_fip in _fip_state_reverse.keys():
        counties = _fips._counties[state_fip]
        _fip_county_reverse[state_fip] = {v: k for k, v in counties.items()}
_fip_init()


def cmd_basic_cached(save_fn, load_fn, last_update):
    """A means of getting the default `get()` and `update()` interface for
    datasets.  Handles caching automatically in get(), and handles redirecting
    file pointers for save/load.

    Args:
        save_fn: Function which takes a writeable, bytes-driven, file-like
                object.  Must serialize loaded data to this file.

        load_fn: Function which takes a readable, bytes-driven, file-like
                object.  Must deserialize data from this file.
        last_update: An e.g. `pendulum.datetime` representing the last time
                this data source was updated.  In other words, if the cached
                data is older than timestamp, then the cache will be updated.

    Return:
        `get_fn, update_fn`: A tuple with a getter and a force-updater.

                `update_fn` takes no arguments.

                `get_fn` takes one argument: `no_update`.  If set to True,
                        even out-of-date data will be loaded.
    """

    cache_name = save_fn.__module__ + '.' + save_fn.__name__
    # I suppose a hash would be more obtuse.
    #cache_name += hashlib.sha256(pdf_dir.encode('utf-8')).hexdigest()
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            '_cache')
    os.makedirs(cache_path, exist_ok=True)

    cache_path = os.path.join(cache_path, cache_name)
    # Temporary file used so that a fetch won't break existing data.
    cache_path_new = cache_path + '.new'

    # Loaded data.
    cache_loaded = None
    # May as well make this thread-safe.
    lock = threading.RLock()

    needs_update = True
    try:
        stats = os.stat(cache_path)
    except FileNotFoundError:
        pass
    else:
        needs_update = (
                pendulum.from_timestamp(stats.st_mtime) < last_update)


    def update():
        nonlocal cache_loaded, needs_update

        with lock:
            try:
                with open(cache_path_new, 'wb') as f:
                    save_fn(f)
            except:
                # Failed to load; don't keep file stub around.
                os.unlink(cache_path_new)
                raise

            # OK!  Overwrite old data.
            os.rename(cache_path_new, cache_path)

            # Invalidate prior get() calls
            cache_loaded = None
            needs_update = False


    def get(no_update=None):
        nonlocal cache_loaded

        if no_update is None:
            # Overwrite with package-wide flag.
            no_update = settings.no_update

        with lock:
            if not no_update:
                if needs_update:
                    update()
            if cache_loaded is None:
                with open(cache_path, 'rb') as f:
                    cache_loaded = load_fn(f)

        return cache_loaded

    return get, update


def resolve_county(county, state):
    """Resolve a county name to its unique FIPS number.

    Supports county of 'unknown' as well, which maps to FIPS 000.

    FIPS: https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
    """
    if county.lower() == 'unknown':
        return _fips.get_state_fips(state) + '000'

    # Other loopholes!
    if county.lower() == 'st. louis' and state == 'MO':
        # Shockingly, st. louis city is its own FIPS code.
        # http://www.msdis.missouri.edu/resources/fips.html
        return '29189'
    elif county.lower() == 'fairfax' and state == 'VA':
        # addfips is wrong
        return '51059'
    elif county.lower() == 'baltimore' and state == 'MD':
        # addfips is wrong
        return '24005'
    elif county.lower() == 'franklin' and state == 'VA':
        # addfips defaults to city FIPS; instead, we prefer county.
        return '51067'
    elif county.lower() == 'bedford' and state == 'VA':
        # addfips is just wrong?  A lot of VA...
        return '51019'
    elif county.lower() == 'roanoke' and state == 'VA':
        return '51161'
    elif county.lower() == 'lasalle' and state == 'LA':
        county = 'la salle'

    r = _fips.get_county_fips(county, state)
    if r is None:
        raise ValueError(f'county={county}, state={state}')
    return r


def resolve_county_name(fips):
    """Go from a fips code to a "county, state" label.
    """
    assert len(fips) == 5, repr(fips)
    state = _fip_state_reverse[fips[:2]].upper()
    if fips[2:] == '000':
        county = 'unknown'
    else:
        county = _fip_county_reverse[fips[:2]][fips[2:]].lower()
    return f'{county}, {state}'


def resolve_date(date, dayfirst=False, yearfirst=False):
    """Resolve a date into a consistent YYYY-MM-DD format.

    Defaults to US MM-DD-YY format.

    Args:
        dayfirst: For European data sources, specify this to load from
                DD-MM-YYYY formats.  Otherwise, MM-DD-YY will be assumed.

        yearfirst: For data sources with six digits, specify this if the
                format is YY-MM-DD.
    """
    d = dateutil_parser.parse(date, dayfirst=dayfirst, yearfirst=yearfirst)
    return d.strftime('%Y-%m-%d')


def resolve_state(name):
    """Resolve a state name to uppercase, two-letter code."""
    state = us.states.lookup(name)
    if state is None:
        raise ValueError(name)

    return state.abbr

