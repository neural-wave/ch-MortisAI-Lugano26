"""The share of the year one month of an offer is charged for (t2), (start date, month) -> fraction of a year.

A month is a twelfth of the year, or its actual days over 360 or 365, counted between two monthly
anniversaries. Found on 82,059 policy years and maturity values of t2 (rules.py, T2_AMC_PERIOD): a twelfth,
in both eras, although the fund accounting of the COBOL years charged actual days / 360 (charges_management).

The order of the steps of one offer month (t2): the premium first or last, the charges and the growth between.

48 orders: the premium at the start of the month followed by any order of the admin fee, the management
charge, the risk charge and the growth, or those four in any order followed by the premium. The order changes
the value a charge is taken on, so the yearly values of t2_projection_year.csv tell them apart.

The term of an offer in months (t2), (start date, maturity date) -> months: the number of monthly steps.

The calendar months from start to maturity, the day of month ignored, or only the completed months (one less
when the maturity falls on an earlier day of the month than the start). Every train policy matures on the day
of its start or later, so the two counts agree on the train offers (rules.py notes the tie, T2_TERM).
"""
from decimal import Decimal as D
from conventions_dates import add_months
from itertools import permutations


def twelfth_of_a_year(start, month):
    """The month is a twelfth of the year."""
    return D(1) / 12


def days_over_360(start, month):
    """The days of the policy month over 360."""
    return D((add_months(start, month + 1) - add_months(start, month)).days) / 360


def days_over_365(start, month):
    """The days of the policy month over 365."""
    return D((add_months(start, month + 1) - add_months(start, month)).days) / 365


AMC_PERIODS = {'a twelfth': twelfth_of_a_year, 'days / 360': days_over_360, 'days / 365': days_over_365}


PARTS = ('admin', 'management', 'risk', 'growth')
ORDERS = {' -> '.join(order): order for order in [('premium', *p) for p in permutations(PARTS)]
          + [(*p, 'premium') for p in permutations(PARTS)]}


def calendar_months(start, end):
    """Calendar months from start to maturity; the day of month is ignored."""
    return (end.year - start.year) * 12 + end.month - start.month


def completed_months(start, end):
    """Whole months from start to maturity: a month counts once its day is reached."""
    return calendar_months(start, end) - (end.day < start.day)


TERMS = {'calendar months': calendar_months, 'completed months': completed_months}
