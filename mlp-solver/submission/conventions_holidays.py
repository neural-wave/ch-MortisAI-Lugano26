"""Public holidays and business days of a Swiss calendar: weekdays that are not a holiday of the canton.

FEDERAL is the Swiss minimum (New Year, National Day, Christmas, St Stephen); TICINO adds Epiphany,
St Joseph, Labour Day, Sts Peter and Paul, Assumption, All Saints and the Immaculate Conception. The movable
holidays are days after Easter Sunday: Easter Monday, Ascension, Whit Monday, Corpus Christi (+1, +39, +50,
+60); Good Friday (-2) is a holiday in most cantons, but not in Ticino. Checked on 30 years of collections (t1).
"""
import datetime as dt
from functools import cache
from dates_easter import easter

FEDERAL = ((1, 1), (8, 1), (12, 25), (12, 26))
TICINO = ((1, 1), (1, 6), (3, 19), (5, 1), (6, 29), (8, 1), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26))
EASTER_TICINO = (1, 39, 50, 60)


@cache  # every candidate day asks for the holidays of its year
def holidays(year, fixed, movable):
    """The holidays of `year`: fixed (month, day) pairs and days after Easter Sunday."""
    return frozenset({dt.date(year, m, d) for m, d in fixed} | {easter(year) + dt.timedelta(n) for n in movable})


def business_day(date, fixed=(), movable=(), step=1):
    """The date itself if it is a business day, else the next one (step -1: the previous one)."""
    while date.weekday() >= 5 or date in holidays(date.year, fixed, movable):
        date += dt.timedelta(days=step)
    return date
