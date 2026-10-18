"""The attained age of a later month of the term: the age the death probability of the risk charge is read at.

It grows on each policy anniversary (the entry age plus the completed policy years) or with the insured
person's own birthdays (the age on the day of the month, by the age rule of the era). Found on every policy
year of the offers of t2 (rules.py, T2_ATTAINED_AGE): the policy anniversary, as in the fund accounting of t3.

Which day decides the era of a t3 rule: the COBOL system or Neuron NG applies its pair (rules.py *_ERA_DATE).

A calculation that changed with the conversion has a pair of rules in rules.py; the system live on one day applies
it. The candidates: the day of the calculation itself (the trade, the charge or the valuation), the day the money
came in, and the application date (the system that wrote the policy). autosolve counts the exact rows of each.

Roundings, (value, date, places) -> value: to the cent by default, to 6 decimals for fund units.

Neuron NG (from 2007-08-11) rounds half up; the COBOL system before it truncated in the offer and the fund
accounting (rules.py, ERA_ROUNDING). Half even (the Java default of many systems), half down, up (fees never
below the tariff) and the Swiss cash rounding to 0.05 are the other usual candidates, kept so that the
search can rule them out. The date is unused here; it lets a rule depend on the system live on it.
"""
from conventions_dates import add_months
from decimal import ROUND_DOWN, ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP, Decimal as D
from tables import CENT


def policy_year_age(entry, month, birth, start, age):
    """The entry age plus the completed policy years: it grows on the policy anniversary."""
    return entry + month // 12


def own_age(entry, month, birth, start, age):
    """The insured person's age on the day of the month, by the age rule of the era (`age`)."""
    return age(birth, add_months(start, month))


ATTAINED_AGES = {'entry age + policy years': policy_year_age, "the insured's own age": own_age}


def on_the_day(day, ledger, money=None):
    """The day of the calculation itself: the trade, the charge or the valuation date."""
    return day


def on_the_money_date(day, ledger, money=None):
    """The day the premium came in (PR_RCVDT); a charge has none, so it keeps its own day."""
    return money or day


def on_the_application_date(day, ledger, money=None):
    """The application date of the policy: the system that wrote it."""
    return ledger.applied


def half_up(value, date=None, places=CENT):
    """Half up, the commercial rounding."""
    return value.quantize(places, rounding=ROUND_HALF_UP)


def truncate(value, date=None, places=CENT):
    """Cut after the last place."""
    return value.quantize(places, rounding=ROUND_DOWN)


def half_even(value, date=None, places=CENT):
    """Half to even, the banker's rounding."""
    return value.quantize(places, rounding=ROUND_HALF_EVEN)


def half_down(value, date=None, places=CENT):
    """Half down: a 5 after the last place is dropped."""
    return value.quantize(places, rounding=ROUND_HALF_DOWN)


def up(value, date=None, places=CENT):
    """Away from zero: any fraction counts as a full unit of the last place."""
    return value.quantize(places, rounding=ROUND_UP)


def five_rappen(value, date=None, places=CENT):
    """Swiss cash rounding to 0.05 (cash only: amounts on accounts keep the cent)."""
    return (value * 20).quantize(D(1), rounding=ROUND_HALF_UP) / 20


ROUNDINGS = {'half up': half_up, 'truncate': truncate, 'half even': half_even, 'half down': half_down, 'up': up,
             '5 Rappen': five_rappen}
