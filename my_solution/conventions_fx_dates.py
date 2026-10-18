"""The day of the exchange rate of a booking (t3): for a premium (trade date, money date) -> date, for a charge
(charge date) -> date.

A premium may take the rate of the day before the trade, of the trade or of the money date; a charge that of
its own day or the day before. Found on the units of the train bookings in a foreign-currency fund (rules.py):
a premium converts at the rate of the day before its trade (as BK_FXRAT in NRBOOK shows), a charge at the rate
of its own day; every PRM unit of the 407,636 bookings and every sampled charge unit matches.

The entry charge of one fund of a premium (t3, t4): (gross share, net amount, entry rate, rounding, date) -> charge.

It is the gross share of the fund less the amount invested, so the rounding rest of the net amount goes to the
charge, or the entry rate times the gross share rounded on its own. Found on the entry charges of all 34,145
train statements (t4): the gross share less the amount invested (rules.py, T3_ENTRY_AMOUNT), all exact.

The rates of the contract on a money date: individual agreements (NRAGRE) over the tariff, and the entry charge.

An agreement holds for its own validity period (AG_VLDFR to AG_VLDTO) and replaces the tariff rate of its
fee type: ENT the entry rate of the broker tier, AMC the annual management rate of the pot (charges.py).
"""
import datetime as dt
from tables import scaled, version
from tariff import entry_rate


def day_before_trade(trade, money):
    """The day before the trade date."""
    return trade - dt.timedelta(days=1)


def on_trade_date(trade, money):
    """The trade date itself."""
    return trade


def on_money_date(trade, money):
    """The day the money arrived."""
    return money


def on_charge_date(date):
    """The day of the charge."""
    return date


def day_before_charge(date):
    """The day before the charge."""
    return date - dt.timedelta(days=1)


PREMIUM_FX_DATES = {'day before the trade': day_before_trade, 'trade date': on_trade_date, 'money date': on_money_date}
CHARGE_FX_DATES = {'charge date': on_charge_date, 'day before the charge': day_before_charge}


def share_less_invested(part, amount, rate, rounding, date):
    """The gross share of the fund less the amount invested."""
    return part - amount


def rounded_entry_charge(part, amount, rate, rounding, date):
    """The entry rate times the gross share, rounded on its own."""
    return rounding(part * rate, date)


ENTRY_AMOUNTS = {'gross share less the invested amount': share_less_invested, 'its own rounded amount': rounded_entry_charge}


def agreed(ledger, kind, date, default):
    """The rate of the `kind` agreement valid on `date` (AG_RATE, 6 decimals), else `default`."""
    agreement = version([r for r in ledger.agreements if r['AG_FEETP'] == kind], date, 'AG')
    return scaled(agreement['AG_RATE']) if agreement else default


def net_share(ledger, date):
    """1 less the entry rate of the broker tier on the money date (PH_BRKNR), or of an ENT agreement."""
    tier = ledger.brokers[version(ledger.history, date, 'PH')['PH_BRKNR']]
    return 1 - agreed(ledger, 'ENT', date, entry_rate(ledger.folder, tier, date))
