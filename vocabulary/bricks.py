"""The dictionary: the building blocks a legacy system may have used.

Each family lists its options from the simplest to the most special; the search prefers
the earlier option when two options explain the data equally well. A brick is a plain
function, so a new idea (from a person or an LLM) is added by writing one more function
and putting it in its family.

The families the solution chooses from live in my_solution/conventions*.py (one source for the
solution and the search); this module adds what only the search needs: rounding factories for the
generated families, era bricks of the dictionary, day counts, growth and date offsets.
"""
import datetime as dt
import sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'my_solution'))
import conventions_rounding  # noqa: E402
from conventions import PREMIUM_DATES, AGES, BIRTH_DATES, SHIFTS, GROWTH  # noqa: E402,F401
from conventions_rounding import five_rappen as swiss_5_rappen  # noqa: E402,F401
from conventions_holidays import FEDERAL as FIXED_HOLIDAYS_CH, TICINO as FIXED_HOLIDAYS_TI  # noqa: E402,F401
from conventions_holidays import EASTER_TICINO as EASTER_OFFSETS_TI  # noqa: E402
from conventions_age import (last_birthday as age_last_birthday, nearest_birthday as age_nearest_birthday,  # noqa: E402,F401
                             calendar_years as age_calendar_years, days_365 as age_days_365, days_36525 as age_days_36525)
from conventions_dates import add_months  # noqa: E402,F401
from dates_easter import easter  # noqa: E402,F401

CENT = D('0.01')
# A hypothesis of the dictionary, not a rule of the solution: the day of the 946 events 800 "system conversion".
# autosolve finds the cut-off of the solution (rules.py, ERA_CUTOFF) from the targets on its own.
CONVERSION = dt.date(2007, 8, 11)

# --- Rounding: (value, date) -> value. Date-aware so that era rules fit the same slot. ---


def rounding(mode, places=CENT):
    """A rounding brick with a fixed mode, independent of the date."""
    return lambda value, date=None, places=places: value.quantize(places, rounding=mode)


def by_era(before, after, cutoff=CONVERSION):
    """A brick that behaves like `before` until `cutoff` and like `after` from then on."""
    return lambda value, date: before(value, date) if date < cutoff else after(value, date)


ROUNDINGS = {**conventions_rounding.ROUNDINGS,
             'truncate before 2007-08-11, then half up': by_era(conventions_rounding.truncate, conventions_rounding.half_up)}

# --- Ages: (birth, date) -> int, from conventions_age ---


def age_by_era(before, after, cutoff=CONVERSION):
    """An age rule that depends on the system live on the reference date (third argument)."""
    return lambda birth, date, ref: before(birth, date) if ref < cutoff else after(birth, date)


# --- Calendar of Ticino and business-day shifts: SHIFTS from conventions_calendar ---


def holidays(fixed, easter_offsets=()):
    """A holiday calendar: date -> bool."""
    def is_holiday(date):
        return (date.month, date.day) in fixed or any(easter(date.year) + dt.timedelta(n) == date for n in easter_offsets)
    return is_holiday


# --- Day counts: (start, end) -> year fraction ---

DAY_COUNTS = {
    'a twelfth per month': lambda d1, d2: D(1) / 12,
    'ACT/360': lambda d1, d2: D((d2 - d1).days) / 360,
    'ACT/365': lambda d1, d2: D((d2 - d1).days) / 365,
}

# --- Growth per month from a yearly rate: GROWTH from conventions_growth ---


# --- Generated families: every precision and every offset, not only the usual ones. ---
# They cover conventions nobody thought of in advance (e.g. units to 4 decimals, a 3-day settlement lag).

MODES = {'half up': ROUND_HALF_UP, 'truncate': ROUND_DOWN, 'half even': ROUND_HALF_EVEN,
         'half down': ROUND_HALF_DOWN, 'up': ROUND_UP}


def roundings_any(max_places=6):
    """Every rounding mode at every precision from 0 to `max_places` decimals (5 x 7 = 35 bricks)."""
    return {f'{name}, {places} decimals': rounding(mode, D(1).scaleb(-places))
            for places in range(max_places + 1) for name, mode in MODES.items()}


def offsets_any(max_days=5):
    """A date moved by -max_days .. +max_days calendar days, and by 1 .. max_days business days of Ticino."""
    ticino = holidays(FIXED_HOLIDAYS_TI, EASTER_OFFSETS_TI)
    found = {f'{k:+d} days': (lambda d, k=k: d + dt.timedelta(k)) for k in range(-max_days, max_days + 1)}
    for k in range(1, max_days + 1):
        found[f'+{k} business days (Ticino)'] = lambda d, k=k: business_days_after(d, k, ticino)
    return found


def business_days_after(date, k, is_holiday):
    """The k-th business day after `date`."""
    while k:
        date += dt.timedelta(1)
        k -= date.weekday() < 5 and not is_holiday(date)
    return date
