"""t1 collection date: how is a due date moved to the day the money is collected?

Hole: the business-day shift (conventions.SHIFTS: no shift, weekdays, the federal and the Ticino calendars).
No single shift explains all rows, the diagnosis finds the column behind it, and each value gets its own rule.
The features are columns of the policy version valid on the extract date, so the split is written to
rules.py as it is (T1_COLLECTION_BY, T1_COLLECTION).
"""
import datetime as dt
from conventions import SHIFTS
from engine import is_holdout
from cases.common import read, iso

TITLE, TASK = 't1 collection date', 't1_next_due_dates'
RULES = {'collection': 'T1_COLLECTION'}
SPLIT = True  # the rule may differ by the value of one column
NOTES = {'collection': 'the shift from the due date to the collection day'}
EXTRACT = dt.date(2026, 6, 30)
COLUMNS = ('PH_PAYMT', 'PH_FREQ', 'PH_PRDCD', 'PH_CCY')


def build(legacy, targets):
    from tables import grouped, version
    policies = grouped(legacy, 'NRPOLH', 'PH_POLNR')
    rows = []
    for r in read(targets, 't1_next_due_dates'):
        policy = version(policies[r['policy_id']], EXTRACT, 'PH')
        rows.append({'policy': r['policy_id'], 'key': (r['policy_id'], r['n']), 'holdout': is_holdout(r['policy_id']),
                     'due': iso(r['due_date']), 'target': iso(r['collection_date']),
                     'features': {column: policy[column] for column in COLUMNS}})
    return rows, {'collection': SHIFTS}, formula


def formula(row, choice):
    return choice['collection'](row['due'])
