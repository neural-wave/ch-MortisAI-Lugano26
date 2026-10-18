"""The terms an offer (t2) was calculated with, read once per policy before the monthly loop.

Which policy version and which day of the tariff count, how the term is counted, how the net premium and
the growth factor are formed: all are choices of `rule` (rules.py). `era(date)` gives the rounding and the
age rule of the system live on rule.ERA_DATE (the application date), because the offer belongs to that system.
"""
from types import SimpleNamespace
from tables import day, scaled, table, version, grouped
from tariff import parameters, charge_parameters, entry_rate
from conventions_steps import FREQUENCY

# Interval of a single premium (PH_FREQ 'E'): no policy runs a million months, so `month % SINGLE == 0` holds
# only in month 0 and the premium is paid once.
SINGLE = 1_000_000


def offer(folder, history, rule, era):
    """The terms of one policy's offer from its NRPOLH versions, under the choices of `rule`.

    Fields: the application and start dates, the term in months, the months between premiums (`every`),
    the net premium, the monthly growth factor, the entry age and the birth date, the risk data (NRRISK and
    NRPERS rows, sum insured, benefit option, qx table), the NRCHRG row, the initial months of the product
    (PD_INIMON), and the rounding and the age rule of the era of the offer.
    """
    policy = rule.T2_VERSION(history)
    risks, persons, brokers, mortality = parameters(folder)
    risk = risks[policy['PH_POLNR']]
    person, applied, start = persons[risk['RK_PERNR']], day(policy['PH_APPDT']), day(policy['PH_BEGDT'])
    on, (rounding, age_rule) = rule.T2_PARAMETER_DATE(policy), era(rule.ERA_DATE(policy))
    entry = entry_rate(folder, brokers[policy['PH_BRKNR']], on)
    net = rule.T2_NET_ROUNDING(scaled(policy['PH_PREMI'], 2) * (1 - entry), applied, rounding)
    birth = rule.BIRTH_DATE(person['PS_BIRTH'])
    product = grouped(folder, 'NRPROD', 'PD_PRDCD')[policy['PH_PRDCD']][0]
    return SimpleNamespace(
        applied=applied, start=start, months=rule.T2_TERM(start, day(policy['PH_ENDDT'])), net=net,
        every=FREQUENCY.get(policy['PH_FREQ'], SINGLE), age=age_rule(birth, rule.T2_AGE_AT(policy)), birth=birth,
        growth=rule.T2_GROWTH(scaled(version(table(folder, 'NRILLU'), on, 'IL')['IL_RATE'])), risk=risk, person=person,
        insured=scaled(risk['RK_SUMIN'], 2), option=risk['RK_TARKEY'][-1], mortality=mortality, initial=int(product['PD_INIMON']),
        charges=charge_parameters(folder, risk['RK_TARKEY'], on), rounding=rounding, age_rule=age_rule)
