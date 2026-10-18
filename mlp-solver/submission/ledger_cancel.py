"""The values a charge of the month is taken on (t3). The management charge sees the slot values before the
charges or after the admin fee; the risk charge sees the values less the admin and management pieces, the
remaining units valued again, or the values before the charges. Found (rules.py, T3_MANAGEMENT_BASE and
T3_RISK_BASE): both on the values before the charges, the risk charge less the two charges, which a full
replay prefers: valuing the units again misses 2 of the 1,077,102 charge totals of the train policies.

Paying a monthly charge by cancelling fund units, by the choices of ledger.rule (T3_CHARGE_*), to 6 decimals.

A charge cancels units at rule.T3_CHARGE_PRICE (the redemption price, bid) with the exchange rate of
rule.T3_CHARGE_FX_DATE (the day of the charge), read and rounded like the premiums' rate (ledger_units.fx);
the units are rounded by the pair of the era of the charge date (COBOL truncates, Neuron NG rounds half up).
Checked on every ADM, AMC and RSK booking of a sample of the train policies (t3_booking.csv): all exact.
"""
from decimal import Decimal as D
from functools import cache
from tables import MICRO


def before_the_charges(values, admin, management, ledger, date):
    """The slot values before the charges of the day."""
    return values


def after_the_admin_fee(values, admin, management, ledger, date):
    """The slot values less the admin fee pieces."""
    return {k: v - admin.get(k, D(0)) for k, v in values.items() if v - admin.get(k, D(0)) > 0}


def less_the_charges(values, admin, management, ledger, date):
    """The slot values less the admin and management pieces, the remaining units not valued again."""
    left = {k: v - admin.get(k, D(0)) - management.get(k, D(0)) for k, v in values.items()}
    return {k: v for k, v in left.items() if v > 0}


def valued_again(values, admin, management, ledger, date):
    """The remaining units valued again after the admin fee and the management charge were cancelled."""
    return ledger.slots(date)


MANAGEMENT_BASES = {'the values before the charges': before_the_charges, 'after the admin fee': after_the_admin_fee}
RISK_BASES = {'the values less the two charges': less_the_charges, 'the units valued again': valued_again,
              'the values before the charges': before_the_charges}


@cache  # the admin fee, the management and the risk charge of a fund on a day share their rate and price
def rate_and_price(market, ccy, fund, date, price, fx_date, lookup, cross):
    """The exchange rate and the unit price a charge of `fund` on `date` cancels at, by the chosen bricks."""
    return market.fx(ccy, fund, fx_date(date), lookup, cross), price(market, fund, date)


def cancelled(ledger, fund, date, amount):
    """Units of `fund` that pay `amount` of a charge on `date`."""
    rule = ledger.rule
    fx, price = rate_and_price(ledger.market, ledger.ccy, fund, date, rule.T3_CHARGE_PRICE, rule.T3_CHARGE_FX_DATE,
                               rule.T3_RATE_LOOKUP, rule.T3_CROSS_RATE)
    rounding = ledger.era(rule.T3_CHARGE_UNITS_ROUNDING, rule.T3_CHARGE_UNITS_ERA_DATE, date)
    return rounding(amount * fx / price, date, MICRO)


def cancel_units(ledger, date, kind, amounts):
    """Cancel units worth the charged {(fund, pot): amount}, and add the amounts to the year of `date`.

    `kind` is the position in the yearly totals: 2 admin fee, 3 management, 4 risk charge.
    """
    for (fund, pot), amount in amounts.items():
        if amount:  # a zero piece cancels no units and adds nothing (most risk pieces of small slots)
            ledger.units[fund, pot] -= cancelled(ledger, fund, date, amount)
            ledger.annual[date.year][kind] += amount
