"""NOTE - must be run directly.  Running `pytest` in repo root will not run
this, as it would force a cache update and takes awhile.
"""

from . import get, update

def test_load():
    # Won't re-load URL; keeps cached version.
    update()
    df = get()

