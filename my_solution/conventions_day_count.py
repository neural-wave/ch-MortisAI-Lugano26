"""The monthly management charge: a yearly rate on the value of each (fund, pot) slot (t3, t4).

The rate is the pot's NRCHRG rate (CG_AMCP1, CG_AMCP2) or an AMC agreement (NRAGRE) as rule.T3_AMC_RATE
says; the share of the year is rule.T3_DAY_COUNT of the era (COBOL: actual days since the previous
anniversary over 360, Neuron NG: a twelfth); each slot's charge is rounded by rule.T3_AMC_ROUNDING of the era.

The rate of a slot's management charge in the fund accounting (t3): an individual AMC agreement (NRAGRE)
replaces the tariff rate of both pots while it is valid, or only the rate of the base units (pot 2). Found:
both pots (rules.py, T3_AMC_RATE), on the charges of the 84 train policies with an AMC agreement.

The share of the year a monthly management charge of the fund accounting covers (t3), (previous anniversary,
anniversary) -> fraction: a twelfth, or the actual days since the previous anniversary over 360 or 365.
Found per era (rules.py, T3_DAY_COUNT): the COBOL system charged actual days / 360, Neuron NG a twelfth,
while the offers of t2 use a twelfth in both eras. Found on the ADM, AMC and RSK bookings of 3 % of the train policies, every charge day on its own (37,143 rows), and the options tied there were replayed on all train policies (1,077,102 charge totals).
"""
from tables import scaled
from decimal import Decimal as D


def management_charges(ledger, date, values, params, previous):
    """{(fund, pot): management charge} of the anniversary `date`."""
    rule = ledger.rule
    era = rule.T3_CHARGES_ERA_DATE
    period = ledger.era(rule.T3_DAY_COUNT, era, date)(previous, date)
    rounding = ledger.era(rule.T3_AMC_ROUNDING, era, date)
    return {(fund, pot): rounding(value * rule.T3_AMC_RATE(ledger, pot, date, params) * period, date)
            for (fund, pot), value in values.items()}


def agreement_for_both_pots(ledger, pot, date, params):
    """The pot's NRCHRG rate, replaced by an AMC agreement valid on the day."""
    return ledger.agreed('AMC', date, scaled(params['CG_AMCP' + pot]))


def agreement_for_pot_2(ledger, pot, date, params):
    """As agreement_for_both_pots, but an agreement leaves the initial units (pot 1) at the tariff rate."""
    rate = scaled(params['CG_AMCP' + pot])
    return ledger.agreed('AMC', date, rate) if pot == '2' else rate


AMC_AGREEMENTS = {'an agreement replaces both pots': agreement_for_both_pots, 'an agreement replaces pot 2': agreement_for_pot_2}


def a_twelfth(previous, date):
    """A twelfth of the yearly rate every month."""
    return D(1) / 12


def actual_days_360(previous, date):
    """The days since the previous anniversary over 360."""
    return D((date - previous).days) / 360


def actual_days_365(previous, date):
    """The days since the previous anniversary over 365."""
    return D((date - previous).days) / 365


DAY_COUNTS = {'a twelfth': a_twelfth, 'actual days / 360': actual_days_360, 'actual days / 365': actual_days_365}
