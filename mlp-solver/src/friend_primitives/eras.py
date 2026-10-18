"""The two systems behind Neuron. The COBOL system ran until the conversion to Neuron NG on 2007-08-11,
and both calculate rounding and ages in their own way."""
import datetime as dt
from decimal import Decimal as D, ROUND_DOWN, ROUND_HALF_UP
from dates import add_months
from dates_years import birth_date, completed_years  # re-exported: the era-independent date rules
from tables import CENT

# Go-live of Neuron NG; each rule compares its own reference date with it.
CONVERSION = dt.date(2007, 8, 11)


def rounded(value, date, places=CENT):
    """Round like the system live on `date`: the COBOL system truncated, Neuron NG rounds half up."""
    return value.quantize(places, rounding=ROUND_DOWN if date < CONVERSION else ROUND_HALF_UP)


def entry_age(birth, start, application):
    """Age at the start date, by the system that wrote the offer.

    Neuron NG takes the nearest age (the age six months after the start), the COBOL system counted
    the days since birth divided by 365, rounded half up.
    """
    if application < CONVERSION:
        return int((D((start - birth).days) / 365).quantize(D(1), rounding=ROUND_HALF_UP))
    shifted = add_months(start, 6)
    return shifted.year - birth.year - ((shifted.month, shifted.day) < (birth.month, birth.day))
