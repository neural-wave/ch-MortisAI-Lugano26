"""When a closed policy stops paying the monthly charges (t3): the version valid on the charge day is surrendered
or claimed (state 60, 70), or the state is not checked at all. Once surrendered, a policy holds no units, so
the train charges cannot tell the two apart (rules.py notes the tie, T3_CLOSED).

The value of a (fund, pot) slot, the base of the charges (t3): its units times the redemption price over the
exchange rate, rounded to the cent by the rule of its era, or exact. Neuron rounds each slot (rules.py,
T3_SLOT_VALUE); the policy value is the sum of the rounded slot values.

The days of the monthly charges of a policy (t3): every monthly anniversary from one month after the start,
before the maturity day or up to it, and up to the extract date (later charges were not run yet). No train
charge falls on a maturity day, so the two ends agree (rules.py notes the tie, T3_SCHEDULE).
"""
from tables import version
import datetime as dt
from conventions_dates import add_months


CLOSED = ('60', '70')  # NRPOLH.PH_STATE per NRCODE: surrendered, death claim


def closed_on_the_day(ledger, date):
    """The policy version valid on the day is surrendered or claimed."""
    return version(ledger.history, date, 'PH')['PH_STATE'] in CLOSED


def never_closed(ledger, date):
    """The state is not checked."""
    return False


CLOSINGS = {'closed on the day': closed_on_the_day, 'not checked': never_closed}


def rounded_value(units, price, fx, rounding, date):
    """The value of a slot rounded to the cent by its era."""
    return rounding(units * price / fx, date)


def exact_value(units, price, fx, rounding, date):
    """The value of a slot at full precision."""
    return units * price / fx


SLOT_VALUES = {'rounded to the cent': rounded_value, 'exact': exact_value}


def before_maturity(start, end, extract):
    """(previous, anniversary) of every month from start + 1 month, before maturity, up to the extract date."""
    month, last, dates = 1, min(extract, end - dt.timedelta(days=1)), []
    while add_months(start, month) <= last:
        dates.append((add_months(start, month - 1), add_months(start, month)))
        month += 1
    return dates


def up_to_maturity(start, end, extract):
    """As before_maturity, the maturity day itself included."""
    return before_maturity(start, end + dt.timedelta(days=1), extract)


SCHEDULES = {'monthly, before maturity': before_maturity, 'monthly, up to maturity': up_to_maturity}
