"""Calendar rules: month arithmetic here, the business days of Ticino in dates_holidays."""
import calendar
import datetime as dt
from functools import cache
from dates_holidays import following


@cache  # every policy steps through the same few hundred months
def add_months(date, months, anchor=None):
    """Same day `months` later; a day that does not exist is clamped to the month end.

    `anchor` is the original day of month of a schedule, so a 31 January start runs
    31 Jan, 28/29 Feb, 31 Mar instead of drifting to the 28th after February.
    """
    year, month = divmod(date.year * 12 + date.month - 1 + months, 12)
    return dt.date(year, month + 1, min(anchor or date.day, calendar.monthrange(year, month + 1)[1]))
