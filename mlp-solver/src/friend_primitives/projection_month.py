"""One month of the offer projection (t2) in the order of the offer system.

The order is premium, admin fee, management charge, risk charge, growth. In the convention search
behind this rule it matched 29 of 45 first-year values, the next best order 17.
"""
from decimal import Decimal as D
from tables import scaled
from eras import rounded
from projection_charges import management_charge, risk_charge


def deduct(value, charge):
    """Take a charge from the value; it never goes below zero, the offer shows no debt."""
    return max(D(0), value - charge)


def advance(value, month, terms):
    """The value after policy month `month` (0 = first).

    Premiums come every `terms.every` months; the admin fee CG_ADMFEE (cents) is due every month,
    also after the last premium. Growth is credited last and rounded to cents.
    """
    if month % terms.every == 0:
        value += terms.net
    value = deduct(value, scaled(terms.charges['CG_ADMFEE'], 2))
    value = deduct(value, management_charge(value, terms))
    value = deduct(value, risk_charge(value, month, terms))
    return rounded(value * terms.growth, terms.applied)
