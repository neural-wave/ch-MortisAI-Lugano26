"""The management charge of an offer month (t2): which yearly rate, and which share of the year a month is.

The offer has no real units, so it may use the pot 2 rate (base units) for the whole value, the pot 1 rate
(initial units), or pot 1 in the initial months of the product (PD_INIMON) and pot 2 after them.
Found on 82,059 policy years and maturity values of t2 (rules.py, T2_AMC_RATE): the pot 2 rate for every
month, although the fund accounting of t3 keeps the two pots apart with their own rates.

Where the terms of an offer come from (t2): the policy version, the date of the parameters, the term.

An offer is printed once, so later versions of the policy and later tariffs might or might not reach it:
the first version or the latest one, the parameters (NRCHRG, NRILLU, NRENTC) valid on the application date
or on the start date. Found on 82,059 policy years and maturity values of t2 (rules.py, T2_VERSION and
T2_PARAMETER_DATE): the first version (the premium of 83 train policies changes later, and the offer keeps
the old one) and the application date.
"""
from tables import day


def pot_2_rate(charges, month, initial):
    """The management rate of the base units (CG_AMCP2) in every month."""
    return charges['CG_AMCP2']


def pot_1_rate(charges, month, initial):
    """The management rate of the initial units (CG_AMCP1) in every month."""
    return charges['CG_AMCP1']


def pot_1_then_pot_2(charges, month, initial):
    """CG_AMCP1 in the first `initial` months (PD_INIMON), CG_AMCP2 after them."""
    return charges['CG_AMCP1' if month < initial else 'CG_AMCP2']


AMC_RATES = {'pot 2 rate': pot_2_rate, 'pot 1 rate': pot_1_rate, 'pot 1 in the initial months, then pot 2': pot_1_then_pot_2}


def first_version(history):
    """The original policy version, the one with the lowest PH_VRSNR."""
    return min(history, key=lambda r: int(r['PH_VRSNR']))


def latest_version(history):
    """The newest policy version, the one with the highest PH_VRSNR."""
    return max(history, key=lambda r: int(r['PH_VRSNR']))


def on_application_date(policy):
    """The day the customer signed the offer (PH_APPDT)."""
    return day(policy['PH_APPDT'])


def on_start_date(policy):
    """The first day of the contract (PH_BEGDT)."""
    return day(policy['PH_BEGDT'])


OFFER_VERSIONS = {'first version': first_version, 'latest version': latest_version}
OFFER_DATES = {'application date': on_application_date, 'start date': on_start_date}
