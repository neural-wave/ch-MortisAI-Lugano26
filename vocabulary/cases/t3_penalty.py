"""t3 surrender penalty: how the policy years are counted, whether waivers apply, how it is rounded.

Target: surrender value; input: the policy value before the penalty (diagnostic column).
Penalty rate: NRSURR by the product's surrender scale and the policy years, 0 without a row.
"""
from decimal import Decimal as D
from bricks import ROUNDINGS, add_months
from engine import is_holdout
from cases.common import read, iso, money


def completed(start, date):
    years = date.year - start.year
    while years > 0 and add_months(start, 12 * years) > date:
        years -= 1
    return years


NREXCP = 't3_surrender_value'  # known manual corrections of this target

YEARS = {'completed policy years': completed,
         'calendar years since start': lambda s, d: d.year - s.year,
         'started policy years': lambda s, d: completed(s, d) + 1,
         'days / 365, truncated': lambda s, d: (d - s).days // 365}
WAIVER = {'waiver periods apply (NRWAIV)': True, 'no waivers': False}
RULES = {k: ROUNDINGS[k] for k in ('half up', 'truncate', 'truncate before 2007-08-11, then half up')}


def build(legacy, targets):
    from tables import grouped, table, day, scaled
    policies, products = grouped(legacy, 'NRPOLH', 'PH_POLNR'), {r['PD_PRDCD']: r for r in table(legacy, 'NRPROD')}
    scales = {(r['SR_SCALE'], int(r['SR_YEAR'])): scaled(r['SR_RATE']) for r in table(legacy, 'NRSURR')}
    waivers = [(day(r['WV_VLDFR']), day(r['WV_VLDTO'])) for r in table(legacy, 'NRWAIV')]
    rows = []
    for r in read(targets, 't3_surrender_value'):
        original = min(policies[r['policy_id']], key=lambda v: int(v['PH_VRSNR']))
        when, start = iso(r['valuation_date']), day(original['PH_BEGDT'])
        rows.append({'policy': r['policy_id'], 'key': (r['policy_id'], r['valuation_date']), 'holdout': is_holdout(r['policy_id']),
                     'target': money(r['surrender_value']),
                     'value': money(r['policy_value']), 'date': when, 'start': start,
                     'scale': products[original['PH_PRDCD']]['PD_SRPSCL'], 'scales': scales,
                     'waived': any(a <= when <= b for a, b in waivers),
                     'features': {'valuation date': r['valuation_date'], 'product': original['PH_PRDCD']}})
    return rows, {'policy years': YEARS, 'waiver': WAIVER, 'rounding': RULES}, formula


def formula(row, c):
    rate = row['scales'].get((row['scale'], c['policy years'](row['start'], row['date'])), D(0))
    if c['waiver'] and row['waived']:
        rate = D(0)
    return max(D(0), c['rounding'](row['value'] * (1 - rate), row['date']))
