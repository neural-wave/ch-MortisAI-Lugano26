"""The admin fee and the floor of an offer month (t2).

The admin fee is due every month of the term, or only in the months with a premium (a single premium policy
would then pay it once). A charge takes the value down to zero at most, or is taken in full and lets the value
go below zero; the train offers never reach that point (rules.py notes the tie).

The two charges of an offer month (t2) that depend on the value: management and risk.

The management charge is the value times the yearly rate of rule.T2_AMC_RATE for the share of the year of the
month (rule.T2_AMC_PERIOD); the risk charge is the sum at risk of the benefit option (tariff_benefit) times the
monthly death rate at the attained age (tariff_risk, rule.T2_ATTAINED_AGE). Each is rounded as
rule.T2_CHARGE_ROUNDING says and never takes the value below the floor of rule.T2_FLOOR.
"""
from decimal import Decimal as D
from tables import scaled
from tariff import risk_amount, risk_rate


def every_month(month, every):
    """The admin fee is due in every month of the term."""
    return True


def premium_months_only(month, every):
    """The admin fee is due only in a month with a premium."""
    return month % every == 0


def never_below_zero(value, charge):
    """A charge takes the value down to zero at most."""
    return max(D(0), value - charge)


def may_go_below_zero(value, charge):
    """A charge is taken in full."""
    return value - charge


ADMIN_MONTHS = {'every month': every_month, 'premium months only': premium_months_only}
FLOORS = {'never below zero': never_below_zero, 'may go below zero': may_go_below_zero}


def management(value, month, terms, rule):
    """The management charge: the value times the rate of rule.T2_AMC_RATE for the share of the year of the month."""
    rate = scaled(rule.T2_AMC_RATE(terms.charges, month, terms.initial))
    charge = value * rate * rule.T2_AMC_PERIOD(terms.start, month)
    return rule.T2_FLOOR(value, rule.T2_CHARGE_ROUNDING(charge, terms.applied, terms.rounding))


def risk(value, month, terms, rule):
    """The risk charge: the sum at risk of the benefit option times the monthly rate at the attained age."""
    age = rule.T2_ATTAINED_AGE(terms.age, month, terms.birth, terms.start, terms.age_rule)
    charge = risk_amount(value, terms.insured, terms.option) * risk_rate(terms.risk, terms.person, terms.charges,
                                                                          terms.mortality, age, rule)
    return rule.T2_FLOOR(value, rule.T2_CHARGE_ROUNDING(charge, terms.applied, terms.rounding))
