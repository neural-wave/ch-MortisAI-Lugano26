"""The era of Neuron: when the system changed, and how each system rounds and counts ages (t2, years 1 and 2).

The offer values of the first two policy years (t2_projection_year.csv) are calculated with plain bricks
only: no brick of the dictionary knows a cut-off. No single rule fits all offers, the diagnosis finds the
date where the rule changes, and each side is searched again: the COBOL rule before, Neuron NG after.
Holes: rounding, entry age, reading an impossible birth date. The growth (yearly rate / 12) and the
management rate (pot 2) are fixed here; the t2 case searches them with the whole offer.
"""
from decimal import Decimal as D
from types import SimpleNamespace
from conventions import ROUNDINGS, AGES, BIRTH_DATES, GROWTH, AMC_RATES
from conventions_offer import OFFER_DATES
from charges_risk import multiplied, twelfth_of_qx
from engine import is_holdout
from cases.common import read, money

TITLE, TASK = 'the era of Neuron (from the offers of t2, policy years 1 and 2)', 't2_projected_maturity_value'
ERA_FINDER = True  # this case finds ERA_CUTOFF; the era holes become pairs (COBOL, Neuron NG)
RULES = {'rounding': 'ERA_ROUNDING', 'entry age': 'ERA_AGE', 'birth date': 'BIRTH_DATE'}
ERA_HOLES = ('rounding', 'entry age')
ERA_DATES, ERA_RULE = OFFER_DATES, 'ERA_DATE'  # the day whose system wrote the offer: found by the diagnosis
NOTES = {'rounding': 'every amount of the calculations that follow the era (eras.rounded)',
         'entry age': 'the age at the start date, by the system that wrote the offer',
         'birth date': 'a PS_BIRTH that does not exist (31 November, 30 February)'}
PREFER = {'birth date': ('clamp to the month end', 'consistent with the month ends of every schedule (dates.add_months)')}
FREQUENCY = {'M': 1, 'Q': 3, 'H': 6, 'J': 12}
# The risk rate of the offer is searched later, on the charges of t3, which need the era first; this case assumes
# the simplest options, and autosolve checks that the later search finds the same.
ASSUMES = {'RISK_LOADING': multiplied, 'RISK_MONTHLY_RATE': twelfth_of_qx}
RISK = SimpleNamespace(**ASSUMES)
# The growth and the management rate are fixed at the options of Neuron; for an extract where they explain too few
# offers to find the era, autosolve searches them as well (they are written to rules.py by the t2 case, not here).
EXTRA = {'growth': GROWTH, 'management rate': AMC_RATES}


def build(legacy, targets):
    from tables import grouped, table, day, scaled, version
    from tariff import parameters, charge_parameters, entry_rate
    years = {}
    for r in read(targets, 't2_projection_year'):
        years.setdefault(r['policy_id'], {})[int(r['policy_year'])] = money(r['value'])
    risks, persons, brokers, mortality = parameters(legacy)
    rows = []
    for pid, versions in grouped(legacy, 'NRPOLH', 'PH_POLNR').items():
        if 1 not in years.get(pid, {}) or 2 not in years[pid]:
            continue
        policy = min(versions, key=lambda r: int(r['PH_VRSNR']))
        risk = risks[pid]
        applied, start = day(policy['PH_APPDT']), day(policy['PH_BEGDT'])
        rows.append({'policy': pid, 'key': pid, 'holdout': is_holdout(pid), 'target': (years[pid][1], years[pid][2]),
                     'applied': applied, 'start': start, 'risk': risk, 'person': persons[risk['RK_PERNR']],
                     'mortality': mortality, 'charges': charge_parameters(legacy, risk['RK_TARKEY'], applied),
                     'rate': scaled(version(table(legacy, 'NRILLU'), applied, 'IL')['IL_RATE']),
                     'premium': scaled(policy['PH_PREMI'], 2), 'every': FREQUENCY.get(policy['PH_FREQ'], 10 ** 6),
                     'entry': entry_rate(legacy, brokers[policy['PH_BRKNR']], applied),
                     'initial': int(grouped(legacy, 'NRPROD', 'PD_PRDCD')[policy['PH_PRDCD']][0]['PD_INIMON']),
                     'features': {'application date': applied, 'start date': start, 'product': policy['PH_PRDCD'],
                                  'frequency': policy['PH_FREQ']}})
    return rows, {'rounding': ROUNDINGS, 'entry age': AGES, 'birth date': BIRTH_DATES}, formula


def formula(row, c):
    from tables import scaled
    from tariff import risk_amount, risk_rate
    rnd, when = c['rounding'], row['applied']
    age = c['entry age'](c['birth date'](row['person']['PS_BIRTH']), row['start'])
    growth, pot = c.get('growth', GROWTH['yearly rate / 12'])(row['rate']), c.get('management rate', AMC_RATES['pot 2 rate'])
    admin, insured = scaled(row['charges']['CG_ADMFEE'], 2), scaled(row['risk']['RK_SUMIN'], 2)
    net, value, out = rnd(row['premium'] * (1 - row['entry']), when), D(0), []
    for month in range(24):
        if month % row['every'] == 0:
            value += net
        value = max(D(0), value - admin)
        amc = scaled(pot(row['charges'], month, row['initial']))
        value = max(D(0), value - rnd(value * amc / 12, when))
        monthly = risk_rate(row['risk'], row['person'], row['charges'], row['mortality'], age + month // 12, RISK)
        value = max(D(0), value - rnd(risk_amount(value, insured, row['risk']['RK_TARKEY'][-1]) * monthly, when))
        value = rnd(value * growth, when)
        if month % 12 == 11:
            out.append(value)
    return tuple(out)
