"""t2 offer projection: rounding, entry age, growth and management rate of the first two policy years.

Holes: rounding, entry age, growth per month, management rate (pot 1 or pot 2).
Target: the projected value at the end of policy years 1 and 2 (diagnostic file).
"""
from decimal import Decimal as D
from bricks import ROUNDINGS, AGES, GROWTH, age_by_era, age_days_365, age_nearest_birthday
from engine import is_holdout
from cases.common import read, money

RULES = {k: ROUNDINGS[k] for k in ('half up', 'truncate', 'truncate before 2007-08-11, then half up')}
AGE_RULES = {k: (lambda f: lambda b, d, ref: f(b, d))(AGES[k]) for k in ('last birthday', 'nearest birthday', 'days / 365')}
AGE_RULES['days / 365 before 2007-08-11, then nearest'] = age_by_era(age_days_365, age_nearest_birthday)
AMC = {'pot 1 rate': 'CG_AMCP1', 'pot 2 rate': 'CG_AMCP2'}
FREQUENCY = {'M': 1, 'Q': 3, 'H': 6, 'J': 12}
from cases.era import RISK  # noqa: E402 (the simplest risk rate, as the era case assumes)


def build(legacy, targets):
    from tables import grouped, table, day, scaled, version
    from tariff import parameters, charge_parameters, entry_rate
    from conventions_birth import clamp_to_month_end as birth_date
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
                     'birth': birth_date(persons[risk['RK_PERNR']]['PS_BIRTH']), 'mortality': mortality,
                     'charges': charge_parameters(legacy, risk['RK_TARKEY'], applied),
                     'rate': scaled(version(table(legacy, 'NRILLU'), applied, 'IL')['IL_RATE']),
                     'premium': scaled(policy['PH_PREMI'], 2), 'every': FREQUENCY.get(policy['PH_FREQ'], 10 ** 6),
                     'entry': entry_rate(legacy, brokers[policy['PH_BRKNR']], applied),
                     'features': {'application date': applied, 'application year': applied.year, 'product': policy['PH_PRDCD'], 'frequency': policy['PH_FREQ']}})
    slots = {'rounding': RULES, 'entry age': AGE_RULES, 'growth': GROWTH, 'management rate': AMC}
    return rows, slots, formula


def formula(row, c):
    from tables import scaled
    from tariff import risk_amount, risk_rate
    rnd, when = c['rounding'], row['applied']
    age = c['entry age'](row['birth'], row['start'], when)
    growth, amc = c['growth'](row['rate']), scaled(row['charges'][c['management rate']])
    admin, insured = scaled(row['charges']['CG_ADMFEE'], 2), scaled(row['risk']['RK_SUMIN'], 2)
    net, value, out = rnd(row['premium'] * (1 - row['entry']), when), D(0), []
    for month in range(24):
        if month % row['every'] == 0:
            value += net
        value = max(D(0), value - admin)
        value = max(D(0), value - rnd(value * amc / 12, when))
        monthly = risk_rate(row['risk'], row['person'], row['charges'], row['mortality'], age + month // 12, RISK)
        value = max(D(0), value - rnd(risk_amount(value, insured, row['risk']['RK_TARKEY'][-1]) * monthly, when))
        value = rnd(value * growth, when)
        if month % 12 == 11:
            out.append(value)
    return tuple(out)
