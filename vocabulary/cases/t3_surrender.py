"""t3: the surrender value from the policy value (the two columns of t3_surrender_value.csv).

Holes: how the policy years of the penalty are counted, whether the waiver periods apply (conventions_penalty)
and the rounding of each era by the valuation date. The formula is accounts_surrender.surrender_value.
"""
import datetime as dt
from conventions import PENALTY_YEARS, WAIVERS, ROUNDINGS
from engine import is_holdout
from cases.common import read, money
from conventions_rounding import on_the_day, on_the_application_date
from cases.t3_common import applied, trial

TITLE, TASK, NEEDS_FOUND = 't3 surrender penalty', 't3_surrender_value', True
ERA_HOLES, ERA_RULE = ('surrender rounding',), 'T3_SURRENDER_ERA_DATE'
ERA_DATES = {'valuation date': on_the_day, 'application date': on_the_application_date}
RULES = {'penalty years': 'T3_PENALTY_YEARS', 'waiver': 'T3_WAIVER', 'surrender rounding': 'T3_SURRENDER_ROUNDING'}
PREFER = {'penalty years': ('completed policy years', 'SCHEMA.md: SR_YEAR is the completed policy years')}
NOTES = {'penalty years': 'the policy years of the NRSURR scale', 'waiver': 'the waiver periods of NRWAIV'}


def build(legacy, targets, found):
    rows = [{'policy': r['policy_id'], 'key': (r['policy_id'], r['valuation_date']), 'holdout': is_holdout(r['policy_id']),
             'target': money(r['surrender_value']), 'value': money(r['policy_value']), 'legacy': legacy, 'found': found,
             'date': dt.date.fromisoformat(r['valuation_date']),
             'features': {'valuation date': dt.date.fromisoformat(r['valuation_date']),
                          'application date': applied(legacy, r['policy_id'])}}
            for r in read(targets, 't3_surrender_value')]
    return rows, {'penalty years': PENALTY_YEARS, 'waiver': WAIVERS, 'surrender rounding': ROUNDINGS}, formula


def formula(row, c):
    from accounts_surrender import surrender_value
    choice = {'T3_PENALTY_YEARS': c['penalty years'], 'T3_WAIVER': c['waiver'],
              'T3_SURRENDER_ROUNDING': (c['surrender rounding'], c['surrender rounding'])}  # one era per search part
    return surrender_value(row['legacy'], trial(row['legacy'], row['policy'], row['found'], choice, RULES), row['date'], row['value'])
