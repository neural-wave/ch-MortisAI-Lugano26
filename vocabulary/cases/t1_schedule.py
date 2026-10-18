"""t1 due dates: how Neuron continues a regular premium schedule into the year after the extract date.

Holes (families of conventions.py): which past items count, the anchor day of the schedule, where it counts
from, and the month step at a short month. Target: every due date of t1_next_due_dates.csv. Which policies get
dates (in force on the extract date, a regular frequency) and the window (after the extract date, up to one
year later, before maturity) are stated in the task and are not searched.
"""
import datetime as dt
from conventions import PAST_DUE, ANCHOR_DAYS, ORIGINS, STEPS
from engine import is_holdout
from cases.common import read, iso

TITLE, TASK = 't1 due dates', 't1_next_due_dates'
RULES = {'past due': 'T1_PAST_DUE', 'anchor day': 'T1_ANCHOR_DAY', 'origin': 'T1_ORIGIN', 'step': 'T1_STEP'}
NOTES = {'past due': 'the history a schedule continues', 'anchor day': 'the day of month the schedule aims at',
         'origin': 'where the schedule counts from', 'step': 'the next due date after a short month'}
EXTRACT = dt.date(2026, 6, 30)
SCHEDULES = {}  # (policy, chosen bricks) -> due dates: every row of a policy needs the same schedule


def build(legacy, targets):
    from tables import grouped, version, day
    from conventions_dates import add_months
    from conventions_steps import FREQUENCY
    policies, premiums = grouped(legacy, 'NRPOLH', 'PH_POLNR'), grouped(legacy, 'NRPREM', 'PR_POLNR')
    rows = []
    for r in read(targets, 't1_next_due_dates'):
        policy = version(policies[r['policy_id']], EXTRACT, 'PH')
        start = day(policy['PH_BEGDT'])
        rows.append({'policy': r['policy_id'], 'key': (r['policy_id'], r['n']), 'holdout': is_holdout(r['policy_id']),
                     'n': int(r['n']), 'target': iso(r['due_date']), 'premiums': premiums[r['policy_id']],
                     'start': start, 'end': day(policy['PH_ENDDT']), 'months': FREQUENCY[policy['PH_FREQ']],
                     'limit': add_months(EXTRACT, 12),
                     'features': {'PH_FREQ': policy['PH_FREQ'], 'PH_PRDCD': policy['PH_PRDCD'], 'start date': start,
                                  'start day': start.day}})
    return rows, {'past due': PAST_DUE, 'anchor day': ANCHOR_DAYS, 'origin': ORIGINS, 'step': STEPS}, formula


def schedule(row, c):
    """The due dates after the extract date of the row's policy under the chosen bricks."""
    past = c['past due'](row['premiums'], EXTRACT)
    anchor, date, dates = c['anchor day'](past, row['start']), c['origin'](past, row['start']), []
    while date <= row['limit']:
        if EXTRACT < date < row['end']:
            dates.append(date)
        date = c['step'](date, row['months'], anchor)
    return dates


def formula(row, c):
    key = (row['policy'], *(c[hole] for hole in RULES))
    if key not in SCHEDULES:
        SCHEDULES[key] = schedule(row, c)
    dates = SCHEDULES[key]
    return dates[row['n'] - 1] if row['n'] <= len(dates) else None
