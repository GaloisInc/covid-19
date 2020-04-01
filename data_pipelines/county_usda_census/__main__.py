"""
Run as:

    python -m data_pipelines.county_usda_census
"""

from . import _get_urls_data

import click
import subprocess
import tempfile

@click.command()
@click.argument('data_type', default=None, type=str, required=False)
def main(data_type):
    """Command to read cached excel worksheets.  Useful for exploring data
    / documentation.
    """
    data = _get_urls_data()

    if data_type is None or data_type not in data.keys():
        raise ValueError(list(data.keys()))

    data = data[data_type]
    with tempfile.NamedTemporaryFile(suffix='.xls') as f:
        f.write(data)
        f.flush()

        subprocess.call(['libreoffice', '--view', f.name], shell=False)


main()

