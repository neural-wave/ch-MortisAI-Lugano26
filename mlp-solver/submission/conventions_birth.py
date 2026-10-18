"""Reading a birth date that does not exist, CYYMMDD text -> date (10 persons of the export: 31 November, ...).

A system either clamps such a day to the month end or rolls it over into the next month; the data hardly
tells which (8 train policies, see docs/holes.md). Clamping is how every schedule of Neuron treats month ends
(dates.add_months), so it is the option consistent with the rest of the rules.

Completed policy years, the same in the COBOL system and Neuron NG (see eras).
"""
import calendar
import datetime as dt
from conventions_dates import add_months


def clamp_to_month_end(value):
    """PS_BIRTH as a date; a day after the month end becomes the month end (31.11. -> 30.11.)."""
    n = int(value)  # n // 10000 is C * 100 + YY, which added to 1900 gives the year for both centuries
    year, month = 1900 + n // 10000, n // 100 % 100
    return dt.date(year, month, min(n % 100, calendar.monthrange(year, month)[1]))


def roll_into_next_month(value):
    """PS_BIRTH as a date; a day after the month end counts on into the next month (31.11. -> 1.12.)."""
    n = int(value)
    first = dt.date(1900 + n // 10000, n // 100 % 100, 1)
    return first + dt.timedelta(days=n % 100 - 1)


BIRTH_DATES = {'clamp to the month end': clamp_to_month_end, 'roll into the next month': roll_into_next_month}


def completed_years(start, date):
    """Completed policy years on `date`; anniversaries of a month-end start are clamped to the month end,
    so a 29 February start completes its year on 28 February of a common year."""
    years = date.year - start.year
    while years > 0 and add_months(start, 12 * years) > date:
        years -= 1
    return years
