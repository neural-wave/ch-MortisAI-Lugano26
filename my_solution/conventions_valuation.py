"""Valuing a policy on a valuation date (t3): when in the day, and how the slot values add up.

The valuation of a day sees every booking of that day, or only those before its trades. The policy value is
the sum of the slot values (each rounded to the cent, rules.py T3_SLOT_VALUE) or the exact total rounded once.
Checked on the policy value of t3_surrender_value.csv (a diagnostic column) with the units of t3_holding.csv,
and on those units with a replay of the policies.
"""
from decimal import Decimal as D


def after_every_booking(order):
    """The valuation comes after every charge and trade of its day."""
    return max(order.values()) + 1


def before_the_trades(order):
    """The valuation comes before the trades of its day."""
    return order['trade'] - D('0.5')


def sum_of_the_slots(ledger, date):
    """The sum of the slot values, each rounded to the cent."""
    return sum(ledger.slots(date).values(), D(0))


def rounded_total(ledger, date):
    """The exact value of all units, rounded once by the era of the date."""
    market, total = ledger.market, D(0)
    for (fund, pot), units in ledger.units.items():
        if units > 0:
            total += units * market.bid(fund, date) / market.fx(ledger.ccy, fund, date)
    return ledger.era(ledger.rule.T3_VALUE_ROUNDING, ledger.rule.T3_CHARGES_ERA_DATE, date)(total, date)


VALUATION_TIMES = {'after every booking of the day': after_every_booking, 'before the trades of the day': before_the_trades}
POLICY_VALUES = {'the sum of the rounded slots': sum_of_the_slots, 'the exact total rounded once': rounded_total}
