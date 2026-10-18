"""t4: the last year of a policy's annual statements (the years of t4_annual_statement.csv).

Hole: the year a policy ends by surrender or death (conventions_end); the statements run until then, at the
latest 2025 (task t4). One row per train policy: its last statement year.
"""
from conventions import END_YEARS
from engine import is_holdout
from cases.common import read

TITLE, TASK = 't4 last statement year', 't4_annual_statement'
RULES = {'end year': 'T4_END_YEAR'}
PREFER = {'end year': ('the first closed version', 'the task counts the year the policy ends: the validity start of the '
                                                  'closed version, not the day a clerk entered it (PH_CHGTS)')}
NOTES = {'end year': 'the year a policy ends by surrender or death'}


def build(legacy, targets):
    from tables import grouped
    last = {}
    for r in read(targets, 't4_annual_statement'):
        last[r['policy_id']] = max(last.get(r['policy_id'], 0), int(r['year']))
    policies = grouped(legacy, 'NRPOLH', 'PH_POLNR')
    rows = [{'policy': pid, 'key': pid, 'holdout': is_holdout(pid), 'target': year, 'history': policies[pid],
             'features': {'last year': year}} for pid, year in last.items()]
    return rows, {'end year': END_YEARS}, formula


def formula(row, c):
    return min(2025, c['end year'](row['history']) or 2025)
