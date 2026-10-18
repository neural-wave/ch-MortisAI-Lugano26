"""t0 commission: on which date is the broker (and his tier) taken, and how is the amount rounded?

Holes: the date that selects the policy version and the rate (application, start, due or money date)
and the rounding brick. Formula: rounding(received amount x rate(tier on that date, premium type)).
Both families come from my_solution/conventions.py, so the winner is written to rules.py as it is.
"""
from conventions import PREMIUM_DATES, ROUNDINGS
from engine import is_holdout
from cases.common import read, money

NREXCP = 't0_commission'  # known manual corrections of this target, to check what is left over
TITLE, TASK = 't0 commission', 't0_commission'  # the rules.py section and the target it is scored on
RULES = {'date': 'T0_DATE', 'rounding': 'T0_ROUNDING'}  # hole -> constant of rules.py
ERA_HOLES = ('rounding',)  # the rounding may differ by era
ERA_DATES, ERA_RULE = {label: PREMIUM_DATES[label] for label in ('money date', 'due date', 'application date', 'start date')}, 'T0_ERA_DATE'
NOTES = {'date': 'the policy version (broker tier) and the commission rate are taken on this date'}


def build(legacy, targets):
    from tables import grouped, table, scaled, version, received
    from tariff import parameters
    expected = {(r['policy_id'], int(r['due_nr'])): money(r['amount']) for r in read(targets, 't0_commission')}
    policies, rates = grouped(legacy, 'NRPOLH', 'PH_POLNR'), table(legacy, 'NRCOMR')
    risks, _, brokers, _ = parameters(legacy)
    rows = []
    for item in received(legacy):
        pid, key = item['PR_POLNR'], (item['PR_POLNR'], int(item['PR_DUENR']))
        if key not in expected:
            continue
        history, kind = policies[pid], risks[pid]['RK_TARKEY'][5]
        raw, dates = {}, {}
        for brick in PREMIUM_DATES.values():  # the amount before rounding, for each candidate date
            date = dates[brick] = brick(item, history)
            policy = version(history, date, 'PH')
            tier = brokers[policy['PH_BRKNR']] if policy else None
            rate = version([r for r in rates if r['CR_TIER'] == tier and r['CR_PAYTP'] == kind], date, 'CR')
            raw[brick] = scaled(item['PR_AMTRC'], 2) * scaled(rate['CR_RATE']) if rate else None
        rows.append({'policy': pid, 'key': key, 'holdout': is_holdout(pid), 'raw': raw, 'dates': dates,
                     'target': expected[key], 'features': {'premium type': kind, **{label: dates[brick] for label, brick in PREMIUM_DATES.items()}}})
    return rows, {'date': PREMIUM_DATES, 'rounding': ROUNDINGS}, formula


def formula(row, choice):
    return choice['rounding'](row['raw'][choice['date']], row['dates'][choice['date']])
