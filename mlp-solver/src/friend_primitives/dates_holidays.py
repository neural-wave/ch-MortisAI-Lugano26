"""Business days of Ticino: weekdays that are not a public holiday of the canton."""
import datetime as dt
from functools import cache
from dates_easter import easter

# Fixed holidays (month, day), checked against 30 years of collections: New Year, Epiphany,
# St Joseph, Labour Day, Sts Peter and Paul, Swiss National Day, Assumption, All Saints,
# Immaculate Conception, Christmas, St Stephen.
FIXED_HOLIDAYS = [(1, 1), (1, 6), (3, 19), (5, 1), (6, 29), (8, 1), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)]
# Movable holidays in days after Easter: Easter Monday, Ascension, Whit Monday, Corpus Christi.
EASTER_HOLIDAYS = (1, 39, 50, 60)


@cache  # following() asks for the year of every candidate collection day
def holidays(year):
    """All public holidays of a year, as a set of dates."""
    fixed = {dt.date(year, m, d) for m, d in FIXED_HOLIDAYS}
    return fixed | {easter(year) + dt.timedelta(days=n) for n in EASTER_HOLIDAYS}


def following(date):
    """The date itself if it is a business day, else the next business day: Saturdays, Sundays
    and the public holidays above are skipped."""
    while date.weekday() >= 5 or date in holidays(date.year):
        date += dt.timedelta(days=1)
    return date
