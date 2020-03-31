"""
Provides a standardized interface to all data.

# What that means

Field value standardization (see util.py):
* State codes should be standardized through `util.resolve_state`.
* County names should be standardized through `util.resolve_county`.
* Dates should be standardized as `util.resolve_date`.

# Example API

Data sources shall be encoded as e.g. `granularity_provenance_description`.

    from data_pipelines import county_nytimes_covid_stats as covid_stats
    # Fetch an up-to-date as of 8-am-daily version of the data.  Use this
    # wherever possible, to use locally cached data.
    covid_stats.get()
    # Force a cache bust.
    covid_stats.update()

No internet connection, so updates are failing, but want to run on cached data?
No problem:

    import data_pipelines
    data_pipelines.settings.no_update = True
    # ...rest of script

# Implementation guidelines

Please use the `util` module liberally.  For an example, see
`county_nytimes_covid_stats/__init__.py`.

"""

from . import settings

