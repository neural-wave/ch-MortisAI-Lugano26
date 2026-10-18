"""Valuing the units of a policy: per fund and pot for the charges, and in total for the surrender value (t3).

Both use the redemption price (FP_BIDPR) of the last price date on or before the day, and the exchange rate of
that same day; a slot is worth rule.T3_SLOT_VALUE of its units (rounded to the cent by rule.T3_VALUE_ROUNDING of
the era), and the policy value is the sum of the slot values, not the rounded sum.
"""
from decimal import Decimal as D
from tables import version
from conventions_schedule import CLOSED


def fund_values(ledger, date):
    """{(fund, pot): value}, in sorted order; a slot worth 0 takes no share of the charges and is left out."""
    rule, market, values = ledger.rule, ledger.market, {}
    rounding = ledger.era(rule.T3_VALUE_ROUNDING, rule.T3_CHARGES_ERA_DATE, date)
    for (fund, pot), units in sorted(ledger.units.items()):
        if units > 0:
            value = rule.T3_SLOT_VALUE(units, market.bid(fund, date), market.fx(ledger.ccy, fund, date), rounding, date)
            if value > 0:
                values[fund, pot] = value
    return values


def policy_value(ledger, date):
    """Policy value by rule.T3_POLICY_VALUE (the sum of the rounded slot values). A surrendered policy or one
    with a death claim (PH_STATE 60 or 70) is worth 0, and so is a date outside every policy version."""
    policy = version(ledger.history, date, 'PH')
    if not policy or policy['PH_STATE'] in CLOSED:
        return D(0)
    return ledger.rule.T3_POLICY_VALUE(ledger, date)
