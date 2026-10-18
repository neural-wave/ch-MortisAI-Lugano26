"""How the exchange rate of a booking is read and rounded (t3): fund currency per policy currency, via CHF.

A day without a published rate takes the last rate before it or the first one after; the cross rate of two
CHF rates stays exact or is rounded to the 6 decimals of BK_FXRAT. Found on the units of the 407,636 PRM
bookings of the train policies (1,145 of them hold a fund in another currency): the last rate on or before,
and the exact cross rate (rules.py, T3_RATE_LOOKUP and T3_CROSS_RATE); only the units are rounded.

Investing one received premium (NRPREM) in the funds of the policy, by the choices of ledger.rule (T3_*).

The amounts and units of the PRM bookings are blank in NRBOOK: the nightly job that filled them is not in the
extract. These rules rebuild them: which day decides the entry rate, the pot and the fund shares (the money
date), when the units are bought (the next price date), how a fund's amount is rounded (once, by its era) and
what the entry charge is (the gross share less the amount invested). The search checked each choice on the
407,636 PRM rows of t3_booking.csv, the trade dates and pots of NRBOOK (diagnostics only, never read here) and
the entry charges of the 34,145 train statements: all exact.
"""
from decimal import ROUND_HALF_UP
from tables import MICRO
from tables import day, scaled
from ledger_parts import premium_parts
from ledger_parts import bought


def rate_on_or_before(market, ccy, date):
    """The CHF rate of the last rate date on or before `date`."""
    return market.chf(ccy, date)


def rate_on_or_after(market, ccy, date):
    """The CHF rate of the first rate date on or after `date`."""
    return market.chf(ccy, date, after=True)


def exact_cross_rate(rate):
    """The quotient of the two CHF rates at full precision."""
    return rate


def cross_rate_to_6_decimals(rate):
    """The quotient rounded half up to 6 decimals, as BK_FXRAT stores it."""
    return rate.quantize(MICRO, rounding=ROUND_HALF_UP)


RATE_LOOKUPS = {'last rate on or before': rate_on_or_before, 'first rate on or after': rate_on_or_after}
CROSS_RATES = {'exact': exact_cross_rate, 'rounded to 6 decimals': cross_rate_to_6_decimals}


PREMIUMS, ENTRY = 0, 1  # positions in Ledger.annual; the charges follow as 2, 3 and 4 (charges.py)


def invest(ledger, item):
    """Book one premium item: [(trade date, fund, pot, units)] for each fund of the allocation.

    The premium counts in the statement year it was received, its entry charge in the year it was invested
    (task t4): a premium received on 31 December is invested in January.
    """
    rule, money = ledger.rule, day(item['PR_RCVDT'])
    ledger.annual[money.year][PREMIUMS] += scaled(item['PR_AMTRC'], 2)
    bookings = []
    for fund, trade, unit_pot, part, amount, rate in premium_parts(ledger, item):
        bookings.append((trade, fund, unit_pot, bought(ledger, fund, trade, money, amount)))
        rounding = ledger.era(rule.T3_AMOUNT_ROUNDING, rule.T3_AMOUNT_ERA_DATE, trade, money)
        ledger.annual[trade.year][ENTRY] += rule.T3_ENTRY_AMOUNT(part, amount, rate, rounding, trade)
    return bookings
