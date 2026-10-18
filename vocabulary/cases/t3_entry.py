"""t4: the entry charges of a statement year, from the premiums invested in it (the column entry_charges).

Hole: what the entry charge of a fund is (conventions_entry.ENTRY_AMOUNTS). The fund amounts and trade dates
are the rules found before; a premium's entry charge counts in the year of its trade date (task t4).
"""
from collections import defaultdict
from decimal import Decimal as D
from conventions import ENTRY_AMOUNTS
from engine import is_holdout
from cases.common import read, money
from cases.t3_common import trial

TITLE, TASK, NEEDS_FOUND = 't4 entry charges', 't4_annual_statement', True
RULES = {'entry amount': 'T3_ENTRY_AMOUNT'}
NOTES = {'entry amount': 'the entry charge of a fund on the statement (t4)'}
YEARS = {}  # (policy, brick) -> {year: entry charges}


def build(legacy, targets, found):
    from tables import received, by_key
    premiums = by_key(received(legacy), 'PR_POLNR')
    rows = [{'policy': r['policy_id'], 'key': (r['policy_id'], int(r['year'])), 'holdout': is_holdout(r['policy_id']),
             'target': money(r['entry_charges']), 'year': int(r['year']), 'items': premiums[r['policy_id']],
             'legacy': legacy, 'found': found, 'features': {'year': int(r['year'])}}
            for r in read(targets, 't4_annual_statement')]
    return rows, {'entry amount': ENTRY_AMOUNTS}, formula


def formula(row, c):
    from ledger_parts import premium_parts
    key = (row['policy'], c['entry amount'])
    if key not in YEARS:
        ledger, years = trial(row['legacy'], row['policy'], row['found'], {}, RULES), defaultdict(D)
        for item in row['items']:
            for fund, trade, pot, part, amount, rate in premium_parts(ledger, item):
                rounding = ledger.era(ledger.rule.T3_AMOUNT_ROUNDING, trade)
                years[trade.year] += c['entry amount'](part, amount, rate, rounding, trade)
        YEARS[key] = years
    return YEARS[key].get(row['year'], D(0))
