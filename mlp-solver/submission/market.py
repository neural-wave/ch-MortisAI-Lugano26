"""Fund prices and exchange rates, looked up by date.

Lookups compare CYYMMDD integers (tables.legacy) with bisect, so a date without a
publication (weekend, holiday) falls back to the last earlier one, as Neuron did.
Prices are looked up here, exchange rates in the mixin market_fx.Exchange. Which price and which date a
booking uses is a choice of rules.py (conventions_trade); this class only answers the lookups.
"""
from bisect import bisect_right
from functools import cache
from tables import day, legacy
from market_prices import price_series, BID
from market_rates import fund_currencies, rate_series, dates_of
from market_fx import Exchange


class Market(Exchange):
    """Prices of the 30 funds (NRFPRC) and CHF rates of their currencies (NRFXRT)."""

    def __init__(self, folder):
        self.funds = fund_currencies(folder)
        self.prices = price_series(folder)
        self.price_dates = dates_of(self.prices)
        self.rates = rate_series(folder)
        self.rate_dates = dates_of(self.rates)

    @cache  # the same few thousand days are looked up for every policy
    def price(self, fund, date, column):
        """The price in `column` (market_prices BID, ASK, MID) of the last price date on or before `date`."""
        return self.prices[fund][bisect_right(self.price_dates[fund], legacy(date)) - 1][column]

    def bid(self, fund, date):
        """Redemption price of the last price date on or before `date` (the valuation of the units)."""
        return self.price(fund, date, BID)

    @cache
    def price_date_after(self, fund, date):
        """The first price date of the fund strictly after `date`."""
        return day(self.price_dates[fund][bisect_right(self.price_dates[fund], legacy(date))])


@cache
def market(folder):
    """One Market per export folder; loading NRFPRC is the slow part."""
    return Market(folder)
