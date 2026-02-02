"""Unit tests for pykms_Filetimes (filetime_to_dt, dt_to_filetime)."""
import doctest
from datetime import datetime

import pykms_Filetimes as m


def test_filetime_to_dt_epoch():
    """Unix epoch maps to 1970-01-01 00:00."""
    dt = m.filetime_to_dt(116444736000000000)
    assert dt == datetime(1970, 1, 1, 0, 0)


def test_filetime_to_dt_with_micros():
    """Filetime with sub-second part."""
    dt = m.filetime_to_dt(128930364000001000)
    assert dt == datetime(2009, 7, 25, 23, 0, 0, 100)


def test_dt_to_filetime_roundtrip():
    """dt -> filetime -> dt roundtrip."""
    dt = datetime(2009, 7, 25, 23, 0, 0, 100)
    ft = m.dt_to_filetime(dt)
    back = m.filetime_to_dt(ft)
    assert back == dt


def test_dt_to_filetime_epoch():
    """1970-01-01 00:00 -> known filetime."""
    ft = m.dt_to_filetime(datetime(1970, 1, 1, 0, 0))
    assert ft == 116444736000000000


def test_filetimes_doctest():
    """Run doctests in pykms_Filetimes."""
    result = doctest.testmod(m, verbose=False)
    assert result.failed == 0, f"{result.failed} doctest(s) failed"
