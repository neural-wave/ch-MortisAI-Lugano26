"""t3: the units held on a valuation date (the units of t3_holding.csv), from a replay of the policy.

Hole: when in the day the valuation comes (conventions_valuation): after every booking of its day, or before
its trades. Every policy is replayed with the solution's ledger_run.replay on a light ledger and the rules found
before; the units of each fund and pot at the valuation are compared with t3_holding.csv.
"""
import datetime as dt
from collections import defaultdict
from decimal import Decimal as D
from conventions import VALUATION_TIMES
from engine import is_holdout
from cases.common import read
from cases.t3_common import trial

TITLE, TASK, NEEDS_FOUND, SAMPLE = 't3 units on a valuation date', 't3_surrender_value', True, 20
RULES = {'valuation time': 'T3_VALUATION_TIME'}
NOTES = {'valuation time': 'the valuation of a day comes after its bookings'}
HELD = {}  # (policy, brick) -> {(fund, pot, date): units}


def build(legacy, targets, found):
    from tables import received, by_key
    from orders import customer_orders
    premiums, orders, dates = by_key(received(legacy), 'PR_POLNR'), customer_orders(legacy), defaultdict(set)
    holdings = read(targets, 't3_holding')
    for r in holdings:
        dates[r['policy_id']].add(dt.date.fromisoformat(r['valuation_date']))
    rows = [{'policy': r['policy_id'], 'key': (r['policy_id'], r['fund_id'], r['pot'], r['valuation_date']),
             'holdout': is_holdout(r['policy_id']), 'target': D(r['units']), 'legacy': legacy, 'found': found,
             'slot': (r['fund_id'], r['pot'], dt.date.fromisoformat(r['valuation_date'])), 'dates': sorted(dates[r['policy_id']]),
             'premiums': premiums.get(r['policy_id'], []), 'orders': orders[r['policy_id']],
             'features': {'valuation date': r['valuation_date']}} for r in holdings]
    return rows, {'valuation time': VALUATION_TIMES}, formula


def held(row, c):
    """{(fund, pot, date): units} of the row's policy at its valuations under the trial."""
    from ledger_run import replay
    ledger = trial(row['legacy'], row['policy'], row['found'], {RULES['valuation time']: c['valuation time']}, RULES)
    ledger.units, ledger.annual, units = defaultdict(D), defaultdict(lambda: [D(0)] * 5), {}

    def value(date):
        units.update({(fund, pot, date): n for (fund, pot), n in ledger.units.items()})
        return D(0)
    ledger.value = value
    replay(ledger, row['premiums'], row['orders'], row['dates'])
    return units


def formula(row, c):
    key = (row['policy'], c['valuation time'])
    if key not in HELD:
        HELD[key] = held(row, c)
    return HELD[key].get(row['slot'], D(0))  # a slot emptied or never filled holds 0 units (rows of 0 exist)
