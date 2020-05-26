#! /usr/bin/env python3

import data_pipelines.util

import click
import contextlib
import importlib
import json
import os
import pandas as pd
import shutil
import sys

TARGET = 'website/public/d'

@click.command()
def main():
    """Run this script to re-build the website/public/d directory, which
    contains up-to-date information from `data_pipelines`.
    """
    _clean_target()
    counties_with_data = _county_data()
    _county_list(counties_with_data)
    _data_export()


def _clean_target():
    """Reset target directory.
    """
    print('Resetting target directory if present...')
    if os.path.lexists(TARGET):
        shutil.rmtree(TARGET)
    os.makedirs(TARGET)
    with open(os.path.join(TARGET, 'README.md'), 'w') as f:
        f.write('This folder generated by website-data.py -- any changes '
                'will automatically be overwritten.')


def _county_data():
    """Build per-county data.

    Returns list of counties which have data
    """
    print('Building per-county data...')
    counties_with_data = set()

    import data_pipelines.county_nytimes_covid_stats as covid_stats
    import data_pipelines.state_covidtracking_com_covid_testing as testing
    import data_pipelines.county_usda_census as usda_census
    import data_pipelines.county_descarteslabs_mobility as mobility

    print('Fetching Covid stats...')
    cs = covid_stats.get()
    print('Fetching testing stats...')
    st = testing.get()
    print('Fetching census data...')
    census = usda_census.get()
    print('Fetching mobility data...')
    m = mobility.get()

    # Join county information
    county_date_data = [
            cs[['county', 'date', 'state', 'cases', 'deaths']],
            m[['county', 'date', 'm50', 'm50_index', 'samples']].rename(
                columns=dict(m50='mobility_m50', m50_index='mobility_m50_index',
                    samples='mobility_samples')),
    ]
    county_data = [
            census['education'][['county']],
            census['population'][['county', 'POP_ESTIMATE_latest']].rename(
                columns=dict(POP_ESTIMATE_latest='population')),
            census['unemployment'][['county']],
    ]
    state_data = [
            st[['state', 'date', 'positive', 'negative', 'pending']].rename(
                columns=dict(positive='state_test_positive',
                    negative='state_test_negative',
                    pending='state_test_pending')),
    ]

    def rollup(data, idx):
        df = None
        for d in data:
            for i in idx:
                d = d[~pd.isna(d[i])]

            if df is None:
                df = d
            else:
                df = df.merge(d, on=idx, how='left')
        return df

    county_df = rollup(county_date_data, ['county', 'date'])
    county_df = rollup([county_df] + county_data, ['county'])
    county_df = rollup([county_df] + state_data, ['state', 'date'])

    # Data layout is {county: {key: [values in date ascending order]}}
    bucket = None
    bucket_seen = set()
    bucket_data = None
    def save_bucket():
        nonlocal bucket, bucket_data
        if bucket is None:
            return

        with open(os.path.join(TARGET, 'county_date_' + bucket + '.json'), 'w') as f:
            json.dump(bucket_data, f)
        bucket = None
        bucket_data = None

    for row_idx, row in county_df.sort_values(['county', 'date']).iterrows():
        b = row['county'][:4]
        if b != bucket:
            save_bucket()
            if b in bucket_seen:
                raise ValueError(f'Duplicate bucket {b}')
            bucket = b
            bucket_seen.add(b)
            bucket_data = {}

        county = bucket_data.setdefault(row['county'], {})
        counties_with_data.add(row['county'])
        data = dict(row)
        data.pop('county')
        for k, v in data.items():
            all_v = county.setdefault(k, [])
            # Pandas' NaN values do not translate well to browser-compatible
            # JSON.
            v = v if not pd.isna(v) else None
            all_v.append(v)

    save_bucket()
    return counties_with_data


def _county_list(counties_with_data):
    """Builds a list of all available counties.  Used for search.
    """
    print('Building a list of all available counties for use by search...')

    fips = data_pipelines.util.fips

    entries = {}

    for state_fips, counties in fips._counties.items():
        for _, county_fips in counties.items():
            f = state_fips + county_fips
            if f.startswith('00') or county_fips == '000':
                # Skip full US / full county data at the moment, until
                # it's better supported.
                continue
            if f not in counties_with_data:
                # Don't list this on the website, as there's no data.
                continue
            entries[f] = data_pipelines.util.resolve_county_name_full(f)

    entries = [[k, v] for k, v in entries.items()]
    entries.sort(key=lambda x: x[0].lower())
    with open(os.path.join(TARGET, 'counties.tsv'), 'w') as f:
        f.write('\n'.join(['\t'.join(v) for v in entries]))


def _data_export():
    """Generates d/data.xlsx.
    """
    print('Generate Excel spreadsheet of data...')

    out_path = os.path.join(TARGET, 'data.xlsx')
    indent = 0
    def dbg(msg):
        print(' ' * indent + msg, file=sys.stderr)
    @contextlib.contextmanager
    def dbg_level(name):
        nonlocal indent
        dbg(f'{name}:')
        indent += 2
        yield
        indent -= 2

    with pd.ExcelWriter(out_path) as writer, \
            dbg_level(f'Building {out_path}...'):

        sheets = []  # (name, df)
        provenance_info = []  # [name, source]

        for f in os.listdir('data_pipelines'):
            if f.startswith('kr_'):
                # TODO FIXME
                continue
            path = os.path.join('data_pipelines', f)
            if f in ['test']:
                continue
            if not os.path.isdir(path):
                continue

            if not os.path.lexists(os.path.join(path, '__init__.py')):
                continue

            with dbg_level(f'Pulling {f}'):
                mod = importlib.import_module(f'data_pipelines.{f}')

                dfs = mod.get()
                dfs_out = []  # (name, source, df)
                if isinstance(dfs, pd.DataFrame):
                    dfs_out = [(f, getattr(mod, 'URL', None), dfs)]
                elif isinstance(dfs, dict):
                    for k, v in dfs.items():
                        dfs_out.append((
                                f'{f}.{k}',
                                getattr(mod, 'URLS', {}).get(k),
                                v))
                else:
                    raise NotImplementedError(dfs)

                for df_name, df_source, df in dfs_out:
                    provenance_info.append((df_name, df_source))
                    sheets.append((df_name, df))

        # Build provenance info, write sheets.
        sheets.insert(0, ('Provenance', pd.DataFrame(provenance_info,
                columns=['Dataset', 'Source'])))
        for s_name, s_df in sheets:
            s_df.to_excel(writer, sheet_name=s_name, index=False)



if __name__ == '__main__':
    main()

