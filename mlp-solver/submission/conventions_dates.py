"""The date a premium item is looked at, (NRPREM row, NRPOLH versions of its policy) -> date.

The application date decides the offer (t2), the start date the anniversaries and policy years, the due
date the schedule (t1) and the money date the statement year (t4) and the investment (t3). Which one
selects the broker of a commission (t0) is a hole of the search. Start and application date never change
between the versions of a policy, so they are read from the first one.

Month arithmetic of the schedules; the holidays and business days are in conventions_holidays.
"""
from tables import day
from conventions_offer import first_version
import calendar
import datetime as dt
from functools import cache


def application_date(premium, history):
    """The day the customer signed the offer (PH_APPDT)."""
    return day(first_version(history)['PH_APPDT'])


def start_date(premium, history):
    """The first day of the contract (PH_BEGDT)."""
    return day(first_version(history)['PH_BEGDT'])


def due_date(premium, history):
    """The day the premium was due (PR_DUEDT)."""
    return day(premium['PR_DUEDT'])


def money_date(premium, history):
    """The day the money arrived (PR_RCVDT)."""
    return day(premium['PR_RCVDT'])


PREMIUM_DATES = {'application date': application_date, 'start date': start_date, 'due date': due_date,
                 'money date': money_date}


@cache  # every policy steps through the same few hundred months
def add_months(date, months, anchor=None):
    """Same day `months` later; a day that does not exist is clamped to the month end.

    `anchor` is the original day of month of a schedule, so a 31 January start runs
    31 Jan, 28/29 Feb, 31 Mar instead of drifting to the 28th after February.
    """
    year, month = divmod(date.year * 12 + date.month - 1 + months, 12)
    return dt.date(year, month + 1, min(anchor or date.day, calendar.monthrange(year, month + 1)[1]))
