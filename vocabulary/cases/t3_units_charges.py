"""t3: the units a monthly charge cancels (the units of the ADM, AMC and RSK bookings of t3_booking.csv).

Holes: the price (bid, ask, mid) and the date of the exchange rate of a charge, and the rounding of the units of
each era by the charge date. The rate lookup and the cross rate are those found for the premiums. The amount
and the date are those of the booking; the formula is ledger_cancel.cancelled (units come out negative).
"""
from conventions import PRICES, CHARGE_FX_DATES, ROUNDINGS
from engine import is_holdout
from conventions_rounding import on_the_day, on_the_application_date
from cases.t3_common import applied, bookings, trial

TITLE, TASK, NEEDS_FOUND, DESCENT, SAMPLE = 't3 units of a charge', 't3_surrender_value', True, True, 20
ERA_HOLES, ERA_RULE = ('units rounding',), 'T3_CHARGE_UNITS_ERA_DATE'
ERA_DATES = {'charge date': on_the_day, 'application date': on_the_application_date}
RULES = {'price': 'T3_CHARGE_PRICE', 'exchange rate date': 'T3_CHARGE_FX_DATE', 'units rounding': 'T3_CHARGE_UNITS_ROUNDING'}
NOTES = {'price': 'the unit price a charge cancels at', 'exchange rate date': 'the day of the exchange rate of a charge'}
POLICIES = 3  # percent of the train policies whose 4.6 million charge bookings are read


def build(legacy, targets, found):
    rows = []
    for key, b in bookings(legacy, targets, ('ADM', 'AMC', 'RSK'), POLICIES).items():
        rows.append({'policy': b['policy'], 'key': key, 'holdout': is_holdout(b['policy']), 'target': b['units'],
                     'booking': b, 'legacy': legacy, 'found': found,
                     'features': {'charge date': b['trade'], 'application date': applied(legacy, b['policy']), 'type': b['type'],
                                  'fund': b['fund']}})
    return rows, {'price': PRICES, 'exchange rate date': CHARGE_FX_DATES, 'units rounding': ROUNDINGS}, formula


def formula(row, c):
    from ledger_cancel import cancelled
    b, choice = row['booking'], {RULES[h]: c[h] for h in RULES}
    choice['T3_CHARGE_UNITS_ROUNDING'] = (c['units rounding'], c['units rounding'])  # one era per search part
    return -cancelled(trial(row['legacy'], row['policy'], row['found'], choice, RULES), b['fund'], b['trade'], b['amount'])
