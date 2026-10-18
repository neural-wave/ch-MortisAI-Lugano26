"""The monthly risk charge: the cost of the death cover, cancelled after the other charges (t3, t4).

The sum at risk of the benefit option (tariff_benefit) times the monthly death rate (tariff_risk) at the age of
rule.T3_CHARGE_AGE (the entry age plus the completed policy years), rounded by rule.T3_RISK_ROUNDING of the era
and split over the slots like the other charges. A zero charge, e.g. option B with a value above the sum
insured, books nothing.

The death probability of a month (t2, t3): how a loading and a smoker factor apply, and the monthly rate.

The medical loading RK_LOAD and the smoker factor CG_SMKFAC multiply (1 + load) x factor, or add up
(1 + load + factor - 1); the yearly death probability qx becomes a monthly rate as qx / 12 or compounded as
1 - (1 - qx) ** (1 / 12). Found on the risk charges (rules.py, RISK_LOADING, RISK_MONTHLY_RATE): multiplied,
and qx / 12; the offers of t2 use the same rate. Found on the ADM, AMC and RSK bookings of 3 % of the train policies, every charge day on its own (37,143 rows), and the options tied there were replayed on all train policies (1,077,102 charge totals).
"""
from tables import scaled
from tariff import risk_amount, risk_rate
from decimal import Decimal as D
RISK = 4

def risk_charge(ledger, date, params, values):
    """Cancel the risk charge of the anniversary `date` from the slot `values` it is taken on."""
    if not values:
        return
    rule = ledger.rule
    at_risk = risk_amount(sum(values.values()), scaled(ledger.risk['RK_SUMIN'], 2), ledger.tariff[-1])
    rate = risk_rate(ledger.risk, ledger.person, params, ledger.mortality, rule.T3_CHARGE_AGE(ledger, date), rule)
    era = rule.T3_CHARGES_ERA_DATE
    total = ledger.era(rule.T3_RISK_ROUNDING, era, date)(at_risk * rate, date)
    total = min(total, sum(values.values()))
    if total:
        ledger.cancel(date, RISK, rule.T3_SPLIT_REST(total, values, ledger.era(rule.T3_PIECE_ROUNDING, era, date), date))

def multiplied(load, factor):
    """(1 + RK_LOAD) x CG_SMKFAC (the factor is 1 for a non-smoker)."""
    return (1 + load) * factor

def added(load, factor):
    """1 + RK_LOAD + (CG_SMKFAC - 1)."""
    return 1 + load + factor - 1

def twelfth_of_qx(qx):
    """qx / 12."""
    return qx / 12

def compounded_qx(qx):
    """1 - (1 - qx) ** (1 / 12)."""
    return 1 - (1 - qx) ** (D(1) / 12)
LOADINGS = {'multiplied': multiplied, 'added': added}
MONTHLY_RATES = {'qx / 12': twelfth_of_qx, 'compounded': compounded_qx}
