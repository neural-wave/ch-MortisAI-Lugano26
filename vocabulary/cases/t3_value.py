"""t3: the policy value on a valuation date from the units held (the policy_value column of t3_surrender_value.csv).

The units of each fund and pot on the date are those of t3_holding.csv (a diagnostic), so only the valuation is
searched: how the slot values add up (conventions_valuation). The formula is ledger_value.policy_value.
"""
import datetime as dt
from collections import defaultdict
from decimal import Decimal as D
from conventions import POLICY_VALUES
from engine import is_holdout
from cases.common import read, money
from cases.t3_common import trial

TITLE, TASK, NEEDS_FOUND = 't3 policy value', 't3_surrender_value', True
RULES = {'policy value': 'T3_POLICY_VALUE'}
NOTES = {'policy value': 'how the slot values add up to the policy value'}


def build(legacy, targets, found):
    held = defaultdict(dict)
    for r in read(targets, 't3_holding'):
        held[r['policy_id'], r['valuation_date']][r['fund_id'], r['pot']] = D(r['units'])
    rows = [{'policy': r['policy_id'], 'key': (r['policy_id'], r['valuation_date']), 'holdout': is_holdout(r['policy_id']),
             'target': money(r['policy_value']), 'date': dt.date.fromisoformat(r['valuation_date']), 'legacy': legacy,
             'found': found, 'units': held[r['policy_id'], r['valuation_date']],
             'features': {'valuation date': r['valuation_date']}} for r in read(targets, 't3_surrender_value')]
    return rows, {'policy value': POLICY_VALUES}, formula


def formula(row, c):
    from ledger_value import policy_value
    ledger = trial(row['legacy'], row['policy'], row['found'], {RULES['policy value']: c['policy value']}, RULES)
    ledger.units = defaultdict(D, row['units'])
    return policy_value(ledger, row['date'])
