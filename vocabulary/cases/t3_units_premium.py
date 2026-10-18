"""t3: the units a premium buys (the units of each PRM booking of t3_booking.csv, from its amount).

Holes: the price (ask, bid, mid), the date of the exchange rate, how a CHF rate is read and the cross rate
rounded (conventions_fx), and the rounding of the units of each era by the trade date. The trade date and the
amount are those of the booking, so only the conversion is searched. The formula is ledger_units.bought.
"""
from conventions import PRICES, PREMIUM_FX_DATES, RATE_LOOKUPS, CROSS_RATES, ROUNDINGS
from engine import is_holdout
from conventions_rounding import on_the_day, on_the_money_date, on_the_application_date
from cases.t3_common import applied, bookings, trial

TITLE, TASK, NEEDS_FOUND, DESCENT, SAMPLE = 't3 units of a premium', 't3_surrender_value', True, True, 10
ERA_HOLES, ERA_RULE = ('units rounding',), 'T3_UNITS_ERA_DATE'
ERA_DATES = {'trade date': on_the_day, 'money date': on_the_money_date, 'application date': on_the_application_date}
RULES = {'price': 'T3_PREMIUM_PRICE', 'exchange rate date': 'T3_PREMIUM_FX_DATE', 'rate lookup': 'T3_RATE_LOOKUP',
         'cross rate': 'T3_CROSS_RATE', 'units rounding': 'T3_UNITS_ROUNDING'}
NOTES = {'price': 'the unit price a premium buys at', 'exchange rate date': 'the day of the exchange rate of a premium'}


def build(legacy, targets, found):
    rows = []
    for key, b in bookings(legacy, targets, ('PRM',), 100).items():
        rows.append({'policy': b['policy'], 'key': key, 'holdout': is_holdout(b['policy']), 'target': b['units'],
                     'booking': b, 'legacy': legacy, 'found': found,
                     'features': {'trade date': b['trade'], 'money date': b['money'], 'application date': applied(legacy, b['policy']),
                                  'fund': b['fund']}})
    slots = {'price': PRICES, 'exchange rate date': PREMIUM_FX_DATES, 'rate lookup': RATE_LOOKUPS, 'cross rate': CROSS_RATES,
             'units rounding': ROUNDINGS}
    return rows, slots, formula


def formula(row, c):
    from ledger_parts import bought
    b, choice = row['booking'], {RULES[h]: c[h] for h in RULES}
    choice['T3_UNITS_ROUNDING'] = (c['units rounding'], c['units rounding'])  # one era per search part
    ledger = trial(row['legacy'], row['policy'], row['found'], choice, RULES)
    return bought(ledger, b['fund'], b['trade'], b['money'], b['amount'])
