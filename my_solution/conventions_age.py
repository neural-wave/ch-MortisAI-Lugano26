"""Ages of the insured person, (birth, date) -> whole years: the usual conventions of life insurance.

The age decides the death probability (NRMORT) of the risk charge. Found on the offers of t2 (rules.py,
ERA_AGE): the COBOL system counted the days since birth divided by 365 (829 train offers, all exact), Neuron NG
takes the age at the nearest birthday (2,190 offers, all exact). Last birthday, calendar years and
days / 365.25 complete the family and lose on both sides.
"""
from decimal import ROUND_HALF_UP, Decimal as D
from conventions_dates import add_months


def last_birthday(birth, date):
    """Completed years of life."""
    return date.year - birth.year - ((date.month, date.day) < (birth.month, birth.day))


def nearest_birthday(birth, date):
    """The age at the nearest birthday: the completed years six months later."""
    return last_birthday(birth, add_months(date, 6))


def calendar_years(birth, date):
    """The difference of the calendar years."""
    return date.year - birth.year


def days_365(birth, date):
    """Days since birth / 365, rounded half up."""
    return int((D((date - birth).days) / 365).quantize(D(1), rounding=ROUND_HALF_UP))


def days_36525(birth, date):
    """Days since birth / 365.25, rounded half up."""
    return int((D((date - birth).days) / D('365.25')).quantize(D(1), rounding=ROUND_HALF_UP))


AGES = {'last birthday': last_birthday, 'nearest birthday': nearest_birthday, 'calendar years': calendar_years,
        'days / 365': days_365, 'days / 365.25': days_36525}
