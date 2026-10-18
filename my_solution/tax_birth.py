"""t7: the birth date of a policyholder, for the German half-income rule (age 60 or 62 at the payout).

NRPERS holds it; an impossible day (31 November) is read as rules.py BIRTH_DATE says, like every other age.

t7: the premiums received up to a payout, in the tax currency: each converted on its own money date and rounded
on its own by the system of its day (the first example of the task, a German surrender of 2006: 5628.16 to
the cent only so).
"""
import datetime as dt
from functools import cache
from tables import grouped
from eras import birth_date
from decimal import Decimal as D
from tax_premiums import premiums
from tax_money import convert
import rules


@cache
def birth(folder, person):
    """Birth date of a person, date.min if NRPERS does not know the person."""
    rows = grouped(folder, 'NRPERS', 'PS_PERNR')[person]
    return birth_date(rows[0]['PS_BIRTH']) if rows else dt.date.min


def paid_in(folder, payout, currency, until=None):
    """The sum of the premiums received up to the payout day (or `until`), in `currency`."""
    return sum((received_in(folder, p, payout, currency)
                for p in premiums(folder)[payout.policy] if p.date <= (until or payout.date)), D(0))


def received_in(folder, premium, payout, currency):
    """One premium in `currency`, converted on its money date and rounded by the system of the day rules.py
    T7_PREMIUM_ROUNDING says (the released samples: its own day, COBOL truncated the old ones; rounding them by the
    payout's system missed 1 to 8 cents of 10 rows)."""
    return convert(folder, premium.amount, payout.currency, currency, premium.date,
                   rules.T7_PREMIUM_ROUNDING(premium.date, payout.date))
