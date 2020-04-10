
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
_fip_state_full_reverse = {}
_fip_county_reverse = {}
# Patches to the 'addfips' library, for counties
_fip_patches = {
        # Added everywhere.
        '_global': {
            'all': '000',
            'unknown': '999',
        },

        'AK': {
            # There are technically two codes; this is used for ambiguous
            # entries.
            'aleutian islands': '010',
            # These show up in the USDA census data.  They're to be trusted.
            'anchorage borough': '020',
            'juneau borough': '110',
            'kuskokwim division': '160',
            'prince of wales-outer ketchikan census area': '201',
            'skagway-yakutat-angoon census area': '231',
            'skagway-hoonah-angoon census area': '232',
            'sitka borough': '220',
            'upper yukon division': '250',
            'wrangell borough': '275',
            'wrangell-petersburg census area': '280',
            'yakutat borough': '282',
        },

        'IL': {
            # typo
            'la salle county': '099',
        },

        'IN': {
            'de kalb county': '033',
            'la porte county': '091',
        },

        'LA': {
            # Support a typo
            'lasalle': '283',
            # Separate region
            'lasalle parish': '059',
        },

        'MD': {
            # addfips is wrong
            'baltimore': '005',
        },

        'MO': {
            # Shockingly, st. louis city is its own FIPS code.
            # http://www.msdis.missouri.edu/resources/fips.html
            'st. louis': '189',
        },

        'MT': {
            # Alias
            'yellowstone national park': '113',
        },

        'NM': {
                'debaca county': '011',
        },

        'PA': {
                'mc kean county': '083',
        },

        'VA': {
            # Add fips is wrong or defaults to city FIPS, but we prefer
            # county on all of these.
            'clifton forge city': '560',
            'fairfax': '059',
            'franklin': '067',
            'bedford': '019',
            'roanoke': '161',
        },
}

def _fip_init():
    global _fip_state_reverse, _fip_state_full_reverse, _fip_county_reverse

    # Patch states
    _fips._states['us'] = '00'
    _fips._states['um'] = '74'  # US Minor Outlying Islands
    _fips._counties['00'] = {}
    _fip_state_reverse = {v: k for k, v in _fips._states.items()
            if 'a' <= k[0] <= 'z' and len(k) == 2}
    _fip_state_full_reverse = {v: k for k, v in _fips._states.items()
            if len(k) != 2 and not ('0' <= k[0] <= '9')}
    _fip_state_full_reverse['00'] = 'United States'
    _fip_state_full_reverse['74'] = 'United States Minor Outlying Islands'

    # Patch counties
    for state_fips, counties in _fips._counties.items():
        counties.update(_fip_patches['_global'])
        name = _fip_state_reverse[state_fips].upper()
        counties.update(_fip_patches.get(name, {}))

    for state_fip in _fip_state_reverse.keys():
        counties = _fips._counties[state_fip]
        _fip_county_reverse[state_fip] = {v: k for k, v in counties.items()}
_fip_init()
# Public assignment
fips = _fips


def cmd_basic_cached(save_fn, load_fn, last_update, cache_name_fn=None):
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
        cache_name_fn: Default None.  If specified, use the given function
                object instead of `save_fn` to generate the cache name.

    Return:
        `get_fn, update_fn`: A tuple with a getter and a force-updater.

                `update_fn` takes no arguments.

                `get_fn` takes one argument: `no_update`.  If set to True,
                        even out-of-date data will be loaded.
    """

    if cache_name_fn is None:
        cache_name_fn = save_fn

    cache_name = cache_name_fn.__module__ + '.' + cache_name_fn.__name__
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


def cmd_url_cached(url_fn, last_update):
    """Special case for caching a URL.  We don't want to hammer URLs,
    particularly while testing, so best to cache URLs separately from
    our parsed datasets.

    Arguments:
        url_fn: Function which takes no parameters and returns the URL
                to load.

        last_update: The last time this resource was updated.
    """
    def save(file_out):
        data = requests.get(url_fn()).content
        file_out.write(data)
    def load(file_in):
        return file_in.read()
    return cmd_basic_cached(save, load, last_update=last_update,
            cache_name_fn=url_fn)


def date_latest_daily(tz, hour, minute=0):
    """Returns the most recent (before current moment) instance of hour:minute
    on a day.
    """
    day = pendulum.now(tz)
    current = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if day < current:
        current = current.add(days=-1)
    return current


def date_latest_monthly(tz, day_of_month=1, hour=0, minute=0):
    """Returns the most recent (before current moment) instance of the given
    day_of_month.
    """
    day = pendulum.now(tz)
    current = day.replace(day=day_of_month, hour=hour, minute=minute,
            second=0, microsecond=0)
    if day < current:
        current = current.add(months=-1)
    return current


def resolve_county(county, state):
    """Resolve a county name to its unique FIPS number.

    Supports county of 'unknown' as well, which maps to FIPS 000.

    FIPS: https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
    """
    r = _fips.get_county_fips(county, state)
    if r is None:
        raise ValueError(f'county={county}, state={state}')
    return r


def resolve_county_name(fips):
    """Go from a fips code to a "county, state" label.
    """
    assert len(fips) == 5, repr(fips)
    state = _fip_state_reverse[fips[:2]].upper()
    county = _fip_county_reverse[fips[:2]][fips[2:]].lower()
    return f'{county}, {state}'


def resolve_county_name_full(fips):
    """Go from a fips code to a "county, state full name" label.
    """
    assert len(fips) == 5, repr(fips)
    state = _fip_state_full_reverse[fips[:2]]
    county = _fip_county_reverse[fips[:2]][fips[2:]].lower()
    return f'{county}, {state}'.title()


def resolve_date(date, dayfirst=False, yearfirst=False, nodashes=False):
    """Resolve a date into a consistent YYYY-MM-DD format.

    Defaults to US MM-DD-YY format.

    Args:
        dayfirst: For European data sources, specify this to load from
                DD-MM-YYYY formats.  Otherwise, MM-DD-YY will be assumed.

        yearfirst: For data sources with six digits, specify this if the
                format is YY-MM-DD.

        nodashes: Some data sources don't use dashes.  This puts them in
                based on the value of `dayfirst` and `yearfirst`.
    """

    if nodashes:
        assert len(date) == 8, date
        if yearfirst:
            assert not dayfirst
            date = f'{date[:4]}-{date[4:6]}-{date[6:]}'
        else:
            date = f'{date[:2]}-{date[2:4]}-{date[4:]}'

    d = dateutil_parser.parse(date, dayfirst=dayfirst, yearfirst=yearfirst)
    return d.strftime('%Y-%m-%d')


def resolve_state(name):
    """Resolve a state name to uppercase, two-letter code."""
    if name.lower() == 'us':
        return 'US'

    state = us.states.lookup(name)
    if state is None:
        raise ValueError(name)

    return state.abbr


def resolve_state_name(fips):
    """Resolve a FIPS code to the state in which it resides.
    """
    if fips is None:
        return "MISSING"
    state = _fip_state_reverse[fips[:2]].upper()
    return state


def resolve_state_name_full(fips):
    """Resolve a FIPS code to the full state name in which it resides.
    """
    if fips is None:
        return "MISSING"
    state = _fip_state_reverse_full[fips[:2]].lower()
    return state

