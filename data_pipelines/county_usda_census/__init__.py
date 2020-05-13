"""
Fetches county-level data from the USDA as described at:
https://www.ers.usda.gov/data-products/county-level-data-sets/download-data/

To see available data, run "python -m data_pipelines.county_usda_census".  This
will guide you to opening the raw Excel files, which contain information on
available variables, etc.  Requires "libreoffice" to be installed.

All files add columns "county" and "state", which were populated using the
`util.resolve_county` and `util.resolve_state` functions.

Note that NaN values indicate missing data.  This is a `pandas` thing.

Data types:
    <all> (every data type has these fields):
        state: name of state
        county: FIPS code for geographical region to which the data
            pertains.

    education:
        Less than a high school diploma_latest
        High school diploma only_latest
        Some college or associate's degree_latest
        Bachelor's degree or higher_latest
        Percent of adults with less than a high school diploma_latest
        Percent of adults with a high school diploma only_latest
        Percent of adults completing some college or associate's degree_latest
        Percent of adults with a bachelor's degree or higher_latest

    poverty:
        Rural-urban_Continuum_Code_2003: Rural-urban Continuum Code, 2003
        Urban_Influence_Code_2003: Urban Influence Code, 2003
        Rural-urban_Continuum_Code_2013: Rural-urban Continuum Code, 2013
        Urban_Influence_Code_2013: Urban Influence Code, 2013
        POVALL_latest: Estimate of people of all ages in poverty 2018
        CI90LBAll_latest: 90% confidence interval lower bound of estimate of people of all ages in poverty 2018
        CI90UBALL_latest: 90% confidence interval upper bound of estimate of people of all ages in poverty 2018
        PCTPOVALL_latest: Estimated percent of people of all ages in poverty 2018
        CI90LBALLP_latest: 90% confidence interval lower bound of estimate of percent of people of all ages in poverty 2018
        CI90UBALLP_latest: 90% confidence interval upper bound of estimate of percent of people of all ages in poverty 2018
        POV017_latest: Estimate of people age 0-17 in poverty 2018
        CI90LB017_latest: 90% confidence interval lower bound of estimate of people age 0-17 in poverty 2018
        CI90UB017_latest: 90% confidence interval upper bound of estimate of people age 0-17 in poverty 2018
        PCTPOV017_latest: Estimated percent of people age 0-17 in poverty 2018
        CI90LB017P_latest: 90% confidence interval lower bound of estimate of percent of people age 0-17 in poverty 2018
        CI90UB017P_latest: 90% confidence interval upper bound of estimate of percent of people age 0-17 in poverty 2018
        POV517_latest: Estimate of related children age 5-17 in families in poverty 2018
        CI90LB517_latest: 90% confidence interval lower bound of estimate of related children age 5-17 in families in poverty 2018
        CI90UB517_latest: 90% confidence interval upper bound of estimate of related children age 5-17 in families in poverty 2018
        PCTPOV517_latest: Estimated percent of related children age 5-17 in families in poverty 2018
        CI90LB517P_latest: 90% confidence interval lower bound of estimate of percent of related children age 5-17 in families in poverty 2018
        CI90UB517P_latest: 90% confidence interval upper bound of estimate of percent of related children age 5-17 in families in poverty 2018
        MEDHHINC_latest: Estimate of median household income 2018
        CI90LBINC_latest: 90% confidence interval lower bound of estimate of median household income 2018
        CI90UBINC_latest: 90% confidence interval upper bound of estimate of median household income 2018
        POV04_latest: Estimate of children ages 0 to 4 in poverty 2018 (available for the U.S. and State total only)
        CI90LB04_latest: 90% confidence interval lower bound of estimate of children ages 0 to 4 in poverty 2018
        CI90UB04_latest: 90% confidence interval upper bound of estimate of children ages 0 to 4 in poverty 2018
        PCTPOV04_latest: Estimated percent of children ages 0 to 4 in poverty 2018
        CI90LB04P_latest: 90% confidence interval lower bound of estimate of percent of children ages 0 to 4 in poverty 2018
        CI90UB04P_latest: 90% confidence interval upper bound of estimate of percent of children ages 0 to 4 in poverty 2018

    population (a lot of these have data 2010-2018; latest copied to "_latest" prefix):
        Rural-urban_Continuum Code_2003: Rural-urban Continuum Code, 2003
        Rural-urban_Continuum Code_2013: Rural-urban Continuum Code, 2013
        Urban_Influence_Code_2003: Urban Influence Code, 2003
        Urban_Influence_Code_2013: Urban Influence Code, 2013
        Economic_typology_2015: County economic types, 2015 edition
        CENSUS_2010_POP: 4/1/2010 resident Census 2010 population
        ESTIMATES_BASE_2010: 4/1/2010 resident total population estimates base
        POP_ESTIMATE_2010: 7/1/2010 resident total population estimate
        POP_ESTIMATE_2011: 7/1/2011 resident total population estimate
        POP_ESTIMATE_2012: 7/1/2012 resident total population estimate
        POP_ESTIMATE_2013: 7/1/2013 resident total population estimate
        POP_ESTIMATE_2014: 7/1/2014 resident total population estimate
        POP_ESTIMATE_2015: 7/1/2015 resident total population estimate
        POP_ESTIMATE_2016: 7/1/2016 resident total population estimate
        POP_ESTIMATE_2017: 7/1/2017 resident total population estimate
        POP_ESTIMATE_2018: 7/1/2018 resident total population estimate
        POP_ESTIMATE_latest: latest ****
        N_POP_CHG_2018: Numeric Change in resident total population 7/1/2017 to 7/1/2018
        Births_2018: Births in period 7/1/2017 to 6/30/2018
        Deaths_2018: Deaths in period 7/1/2017 to 6/30/2018
        NATURAL_INC_2018: Natural increase in period 7/1/2017 to 6/30/2018
        INTERNATIONAL_MIG_2018: Net international migration in period 7/1/2017 to 6/30/2018
        DOMESTIC_MIG_2018: Net domestic migration in period 7/1/2017 to 6/30/2018
        NET_MIG_2018: Net migration in period 7/1/2017 to 6/30/2018
        RESIDUAL_2018: Residual for period 7/1/2017 to 6/30/2018
        GQ_ESTIMATES_BASE_2010: 4/1/2010 Group Quarters total population estimates base
        GQ_ESTIMATES_2018: 7/1/2018 Group Quarters total population estimate
        R_birth_2018: Birth rate in period 7/1/2017 to 6/30/2018
        R_death_2018: Death rate in period 7/1/2017 to 6/30/2018
        R_NATURAL_INC_2018: Natural increase rate in period 7/1/2017 to 6/30/2018
        R_INTERNATIONAL_MIG_2018: Net international migration rate in period 7/1/2017 to 6/30/2018
        R_DOMESTIC_MIG_2018: Net domestic migration rate in period 7/1/2017 to 6/30/2018
        R_NET_MIG_2018: Net migration rate in period 7/1/2017 to 6/30/2018

    unemployment (likely 2007 up to 2018; latest copied to "_latest"):
        Rural_urban_continuum_code_2013: Rural-urban Continuum Code, 2013
        Urban_influence_code_2013: Urban Influence Code, 2013
        Metro_2013: Metro nonmetro dummy 0=Nonmetro 1=Metro (Based on 2013 OMB Metropolitan Area delineation)
        Civilian_labor_force_2018: Civilian labor force annual average, 2018
        Employed_2018: Number employed annual average, 2018
        Unemployed_2018: Number unemployed annual average, 2018
        Unemployment_rate_2018: Unemployment rate, 2018
        Median_Household_Income_2018: Estimate of Median household Income, 2018
        Med_HH_Income_Percent_of_State_Total_2018: County Household Median Income as a percent of the State Total Median Household Income, 2018

"""

from ..util import cmd_basic_cached, date_latest_monthly, resolve_state, resolve_county

import io
import pandas as pd
import pendulum
import pickle
import re
import requests
import shutil

URLS = {
        'education': 'https://www.ers.usda.gov/webdocs/DataFiles/48747/Education.xls',
        'unemployment': 'https://www.ers.usda.gov/webdocs/DataFiles/48747/Unemployment.xls',
        'poverty': 'https://www.ers.usda.gov/webdocs/DataFiles/48747/PovertyEstimates.xls',
        'population': 'https://www.ers.usda.gov/webdocs/DataFiles/48747/PopulationEstimates.xls',
}
# Seems to update by the 10th of each month.
UPDATED = date_latest_monthly('utc', 10)

def _save_urls(file_out):
    data = {}
    for u, v in URLS.items():
        r = requests.get(v)
        if r.status_code != 200:
            raise ValueError(r)
        data[u] = r.content
    pickle.dump(data, file_out, protocol=pickle.HIGHEST_PROTOCOL)


def _load_urls(file_in):
    return pickle.load(file_in)


_get_urls_data, _ = cmd_basic_cached(_save_urls, _load_urls,
        last_update=UPDATED.add(seconds=-1))


def _save(file_out):
    excel_data = _get_urls_data()

    each_default = {
            'county': 'Area_Name',
            'state': 'State',
            'fips': 'FIPS',
    }
    each_info = {
            'education': {
                'fips': 'FIPS Code',
                'county': 'Area name',
                'header': 4,
            },
            'unemployment': {
                'fips': 'FIPStxt',
                'state': 'Stabr',
                'county': 'area_name',
                'header': 7,
                'county_strip_state': True,
            },
            'poverty': {
                'fips': 'FIPStxt',
                'state': 'Stabr',
                'county': 'Area_name',
                'header': 4,
            },
            'population': {
                'fips': 'FIPStxt',
                'county': 'Area_Name',
                'header': 2,
            },
    }

    result = {}
    for k, v in excel_data.items():
        try:
            info = each_default.copy()
            info.update(each_info[k])
            df = None
            df = pd.read_excel(io.BytesIO(v),
                    header=info['header'])

            # Patch out 'WN'... from May 2020 update
            if k == 'unemployment':
                df = df[df[info['state']] != 'WN']

            def update_row(rowdata):
                # Standardize!
                county_val = rowdata[info['county']]
                state_val = rowdata[info['state']]
                fips_val = rowdata[info['fips']]
                del rowdata[info['county']]
                del rowdata[info['state']]
                del rowdata[info['fips']]

                if info.get('county_strip_state'):
                    # Entries look like "Autauga County, AL"
                    if re.search(r', [A-Z][A-Z]$', county_val):
                        county_val = county_val.rsplit(',', 1)[0]

                for e in ['/city', '/town', '/municipality', ', puerto rico']:
                    if county_val.lower().endswith(e):
                        county_val = county_val[:-len(e)]

                county_val_old = county_val
                state_val_old = state_val
                rowdata['state'] = state_val = resolve_state(state_val)
                if f'{fips_val:05d}'.endswith('000'):
                    # State or country code.
                    county_val = 'all'
                rowdata['county'] = county_val = resolve_county(county_val,
                        state=state_val)

                # Weird bug in May 2020 update
                if f'{fips_val:05d}' == '56000' and state_val_old == 'WI' and county_val_old == 'Wyoming':
                    # Actually Wyoming.
                    rowdata['county'] = '56000'
                    rowdata['state'] = 'WY'

                assert float(rowdata['county']) == fips_val, \
                        f'{rowdata["county"]} != {fips_val} // {state_val_old} // {county_val_old} // {rowdata}'

                return rowdata
            df = df.apply(update_row, axis=1)

            # Alias any year-suffixed fields as their latest version
            latest = {}
            # Note that e.g. education has dates formatted ", 2014-18",
            # hence the slightly more complicated regex.
            r = re.compile(r'^(?P<label>.*)(, ?|_)(?P<year>[0-9][0-9][0-9][0-9])(-[0-9][0-9])?$')
            for c in df.columns:
                m = r.search(c)
                if m is None:
                    continue

                rec = int(m.group('year'))
                if latest.get(m.group('label'), (0, 0))[0] < rec:
                    latest[m.group('label')] = (rec, m.group(0))

            for kk, vv in latest.items():
                df[kk + '_latest'] = df[vv[1]]

            result[k] = df
        except:
            raise Exception(f'While handling {k}, with columns {df is not None and df.columns}')

    pd.to_pickle(result, file_out)


def _load(file_in):
    return pd.read_pickle(file_in)


get, update = cmd_basic_cached(_save, _load,
        last_update=UPDATED)

