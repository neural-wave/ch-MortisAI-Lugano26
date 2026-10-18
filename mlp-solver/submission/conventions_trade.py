"""When a premium buys fund units and at which price (t3): (market, fund, date) -> trade date or price.

A premium is invested at a forward price: on the first price date after the money arrived, on the money date
itself when a price is published that day, or a price date later. The units are bought at the issue price
(ask), charges cancel units at the redemption price (bid) or a system might use the mid price. Checked on the
trade dates and prices of the PRM and charge bookings (NRBOOK and t3_booking.csv, diagnostics only).
"""
import datetime as dt
from market_prices import BID, ASK, MID


def next_price_date(market, fund, money):
    """The first price date strictly after the money date."""
    return market.price_date_after(fund, money)


def same_or_next_price_date(market, fund, money):
    """The money date if a price is published that day, else the next price date."""
    return market.price_date_after(fund, money - dt.timedelta(days=1))


def second_price_date(market, fund, money):
    """The second price date after the money date."""
    return market.price_date_after(fund, market.price_date_after(fund, money))


def issue_price(market, fund, date):
    """The ask price of the last price date on or before `date`."""
    return market.price(fund, date, ASK)


def redemption_price(market, fund, date):
    """The bid price of the last price date on or before `date`."""
    return market.price(fund, date, BID)


def mid_price(market, fund, date):
    """The mid price of the last price date on or before `date`."""
    return market.price(fund, date, MID)


TRADE_DATES = {'next price date': next_price_date, 'same or next price date': same_or_next_price_date,
               'second price date': second_price_date}
PRICES = {'issue price (ask)': issue_price, 'redemption price (bid)': redemption_price, 'mid price': mid_price}
