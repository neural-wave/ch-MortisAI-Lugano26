"""t7: what a withdrawal, a surrender or a death claim paid (rules.py T7_PAYOUT_AMOUNT, T7_DEATH_AMOUNT).

The WDR and SUR bookings hold the value of the units sold, before the surrender penalty. Net of the penalty (the
surrender value of t3, a waiver period included) the rules of which payouts carry a tax contradict no NRTAXB booking
in Switzerland and Italy (gross: 2 and 5). A death claim pays without penalty; whether the tax module took the DTH
booking or the benefit of the tariff: the released samples show the benefit (52 of the 75 death claims differ).
"""
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace
from tables import grouped, day, scaled
from accounts_surrender import surrender_value
from tariff_rates import risk_amount
from tariff import main_risks

CENT = Decimal('0.01')


def the_gross_amount(folder, head, kind, date, gross, rule):
    """The amount booked: the value of the units sold, before the surrender penalty (a death claim as rules.py
    T7_DEATH_AMOUNT says). Version 22 and submissions 1 and 2 used it."""
    return rule.T7_DEATH_AMOUNT(folder, head, gross) if kind == 'death' else gross


def after_the_surrender_penalty(folder, head, kind, date, gross, rule):
    """A withdrawal or a surrender net of the penalty of its policy year, the surrender value of t3 to the cent
    (NRSURR by the product's scale and the completed policy years, none in a waiver period of NRWAIV); a death
    claim pays without penalty. 750 of the 2,493 payouts carry a penalty."""
    if kind == 'death':
        return rule.T7_DEATH_AMOUNT(folder, head, gross)
    ledger = SimpleNamespace(rule=rule, start=day(head['PH_BEGDT']),
                             product=grouped(folder, 'NRPROD', 'PD_PRDCD')[head['PH_PRDCD']][0])
    ledger.era = lambda pair, which, when, money=None: pair[when >= rule.ERA_CUTOFF]
    return surrender_value(folder, ledger, date, gross)


def the_death_booking(folder, head, value):
    """A death claim pays the DTH booking: the value of the units on the day of death, as booked in NRBOOK."""
    return value


def the_death_benefit(folder, head, value):
    """A death claim pays the benefit of the tariff: the value and the sum at risk of its option (A: 1 % of the
    value, B: the sum insured above the value, C: the sum insured), as the risk charge of t3 counts it, paid to the
    cent in policy currency (the released samples: 4 of 4 death claims; converted unrounded, one is a cent off)."""
    return the_death_benefit_not_rounded(folder, head, value).quantize(CENT, ROUND_HALF_UP)


def the_death_benefit_not_rounded(folder, head, value):
    """The benefit of the tariff as the risk charge of t3 counts it, not rounded to the cent."""
    risk = main_risks(folder)[head['PH_POLNR']]
    return value + risk_amount(value, scaled(risk['RK_SUMIN'], 2), risk['RK_TARKEY'][-1])


PAYOUT_AMOUNTS = {'gross': the_gross_amount, 'after the surrender penalty': after_the_surrender_penalty}
DEATH_AMOUNTS = {'the DTH booking': the_death_booking, 'the death benefit': the_death_benefit,
                 'the death benefit, not rounded': the_death_benefit_not_rounded}
