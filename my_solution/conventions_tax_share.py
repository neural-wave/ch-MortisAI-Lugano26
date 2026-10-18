"""t7, Italy: the share of a year the stamp duty at a payout is due for (rules.py T7_BOL_SHARE).

A payout during the year accrues the duty on the payout for the part of the year before it. Nothing local decides
between the shares: 134 payout years in the extract, about 2 % of the yearly rows.

t7, Italy: the value the yearly stamp duty is taken on, and what a withdrawal collects of the open duty.

The second example of the task has the same duty with both values (an old policy: no surrender penalty left); they
differ in 1,517 of the yearly rows (rules.py T7_BOL_VALUE). A withdrawal collects its share (EV_PCTG) of the duty
accrued and not collected yet, or all of it: 167 withdrawals differ (T7_BOC_SHARE).
"""
import calendar
from decimal import Decimal as D
from accounts_surrender import surrender_value


def days_share(date):
    """The days of the year up to `date`, the payout day included, over the days of that year (365 or 366): the
    duty of the days the policy was held in the year."""
    return D(date.timetuple().tm_yday) / (366 if calendar.isleap(date.year) else 365)


def days_365_share(date):
    """The days of the year up to `date` over 365."""
    return D(date.timetuple().tm_yday) / 365


def months_share(date):
    """The months of the year up to `date` over 12."""
    return D(date.month) / 12


def full_year(date):
    """The whole year's duty."""
    return D(1)


BOL_SHARES = {'days of the year': days_share, 'days / 365': days_365_share, 'months': months_share, 'the full year': full_year}


def the_policy_value(folder, ledger, date, value):
    """The value of the units on the day."""
    return value


def the_surrender_value(folder, ledger, date, value):
    """The value less the surrender penalty of the day."""
    return surrender_value(folder, ledger, date, value)


def withdrawn_share(payout):
    """A withdrawal its share, any other payout all of it."""
    return payout.share if payout.kind == 'withdrawal' else 1


def everything(payout):
    """Every payout all the open duty."""
    return 1


BOL_VALUES = {'policy value': the_policy_value, 'surrender value': the_surrender_value}
BOC_SHARES = {'the withdrawn share': withdrawn_share, 'everything': everything}
