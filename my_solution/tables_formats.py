"""Neuron's legacy date format (SCHEMA.md, "Conventions"); numbers with implied decimals are in tables_numbers.

Dates (`D` columns) are integers CYYMMDD, C = 0 for 19xx and 1 for 20xx: 1250131 is 2025-01-31. The leading 0
of a 19xx date is lost (970630 is 1997-06-30; 430 of the 5,566 PH_VLDFR values), which integer arithmetic handles.
"""
import datetime as dt
from functools import cache

# Two `D` values are markers, not days: 0 is "no date", 9999999 "open end".
MARKERS = {0: dt.date.min, 9999999: dt.date.max}


@cache
def day(value):
    """A `D` column as a date: CYYMMDD split from the right into day, month and years since 1900 (125 -> 2025).
    The MARKERS become date.min and date.max, so a missing start sorts before every real date and an open-ended
    validity period never ends. Cached because a few thousand distinct dates recur in every table."""
    n = int(value)
    if n in MARKERS:
        return MARKERS[n]
    rest, mday = divmod(n, 100)
    years, month = divmod(rest, 100)
    return dt.date(1900 + years, month, mday)


def legacy(date):
    """A date back in the CYYMMDD format, to compare it with raw columns such as `..._VLDFR` as integers."""
    return (date.year - 1900) * 10000 + date.month * 100 + date.day
