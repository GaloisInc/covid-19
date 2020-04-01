
from .. import util

def test_resolve_county():
    assert util.resolve_county('multNOMAH', 'or') == '41051'
    assert util.resolve_county_name('41051') == 'multnomah, OR'

    # 'Unknown' is a special county name which we allow.
    assert util.resolve_county('unknown', 'or') == '41999'
    # 'all' is also a special county name
    assert util.resolve_county('all', 'or') == '41000'


def test_resolve_date():
    assert util.resolve_date('2020-01-22') == '2020-01-22'
    assert util.resolve_date('01-22-2020') == '2020-01-22'
    assert util.resolve_date('01-22-20') == '2020-01-22'
    assert util.resolve_date('22-01-20', dayfirst=True) == '2020-01-22'


def test_resolve_state():
    assert util.resolve_state('or') == 'OR'
    assert util.resolve_state('orEGON') == 'OR'

