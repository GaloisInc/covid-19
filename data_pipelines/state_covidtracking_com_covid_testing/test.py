"""Must be run directly."""

from . import get, update

def test_covid_testing():
    update()
    df = get()
    print(df)
    print(list(df.columns))

