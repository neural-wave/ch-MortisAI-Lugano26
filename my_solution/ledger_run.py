"""Replaying a policy day by day: premiums and customer orders add units, anniversaries take the charges.

With these rules the replay reproduces 6137 of the 6153 train surrender values (t3); the other 16 are
manual corrections in the legacy system, which t5 lists as outliers.
"""
from charges import monthly_charges
from ledger_premium import invest
from ledger_dates import anniversaries


def day_order(ledger):
    """Sort keys of the actions of one day: charges and trades (rule.T3_DAY_ORDER), the valuation
    (rule.T3_VALUATION_TIME): charges first, then trades, the valuation after every booking of its day."""
    order = ledger.rule.T3_DAY_ORDER()
    return {**order, 'valuation': ledger.rule.T3_VALUATION_TIME(order)}


def actions(ledger, premiums, orders, dates):
    """All actions of the policy as (date, kind, detail), unsorted.

    The charges come first on their day, so they see only the units traded before that day;
    a valuation comes last and sees every booking of its day. The detail of a trade is
    (fund, pot, units), of a charge the previous anniversary.
    """
    order = day_order(ledger)
    return [
        *[(trade, order['trade'], booking) for item in premiums for trade, *booking in invest(ledger, item)],
        *[(trade, order['trade'], booking) for trade, *booking in orders],
        *[(date, order['charge'], previous) for previous, date in anniversaries(ledger)],
        *[(date, order['valuation'], None) for date in dates],
    ]


def replay(ledger, premiums, orders, dates):
    """Run every action in date order and return {valuation date: policy value}."""
    values, order = {}, day_order(ledger)
    for date, kind, detail in sorted(actions(ledger, premiums, orders, dates), key=lambda a: a[:2]):
        if kind == order['trade']:
            fund, unit_pot, units = detail
            ledger.units[fund, unit_pot] += units
        elif kind == order['charge']:
            monthly_charges(ledger, date, detail)
        else:
            values[date] = ledger.value(date)
    return values
