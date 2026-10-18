"""t7: the birth date of a policyholder, for the German half-income rule (age 60 or 62 at the payout).

NRPERS holds it; an impossible day (31 November) is read as rules.py BIRTH_DATE says, like every other age.

t7: the premiums received up to a payout, in the tax currency: each converted on its own money date
and rounded by the system active on that money date (COBOL truncation before conversion, half up after).
"""
import datetime as dt
from functools import cache
from tables import grouped
from eras import birth_date
from decimal import Decimal as D
from tax_premiums import premiums
from tax_money import convert


@cache
def birth(folder, person):
    """Birth date of a person, date.min if NRPERS does not know the person."""
    rows = grouped(folder, 'NRPERS', 'PS_PERNR')[person]
    return birth_date(rows[0]['PS_BIRTH']) if rows else dt.date.min


def paid_in(folder, payout, currency):
    """The sum of the premiums received up to the payout day, in `currency`."""
    return sum((convert(folder, p.amount, payout.currency, currency, p.date, p.date)
                for p in premiums(folder)[payout.policy] if p.date <= payout.date), D(0))
