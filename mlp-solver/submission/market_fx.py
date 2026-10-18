"""Exchange rates by date (NRFXRT), a mixin of market.Market, which loads `rates`, `rate_dates` and `funds`.

A rate is CHF per unit of a currency; the cross rate of a fund is fund currency per policy currency, the
quotient of the two CHF rates (SCHEMA: cross rates go via CHF). Which rate date a day without a rate takes
and whether the quotient is rounded are choices of rules.py (T3_RATE_LOOKUP, T3_CROSS_RATE): the last rate
on or before the day, kept exact, match every unit of the 407,636 PRM bookings of the train policies.
The default arguments are the same choices, for the valuation of the units (ledger_value).
"""
from bisect import bisect_left, bisect_right
from decimal import Decimal as D
from functools import cache
from tables import legacy


class Exchange:
    """CHF rates of the fund and policy currencies CHF, EUR, USD, GBP and SEK."""

    @cache  # the same few thousand days are looked up for every policy
    def chf(self, ccy, date, after=False):
        """CHF per unit of `ccy` on the last rate date on or before `date` (with `after`: the first on or after).

        NRFXRT also lists CHF, always at 1.000000 (8,154 rows), so it is not looked up.
        EUR rates start 1998-12-31, before the first EUR fund price (1999-01-04).
        """
        if ccy == 'CHF':
            return D(1)
        n = legacy(date)
        i = bisect_left(self.rate_dates[ccy], n) if after else bisect_right(self.rate_dates[ccy], n) - 1
        return self.rates[ccy][i][1]

    @cache  # the same few thousand days are looked up for every policy
    def fx(self, policy_currency, fund, date, lookup=None, cross=None):
        """Fund currency per policy currency via CHF (SCHEMA); `lookup` (market, ccy, date) reads a CHF rate and
        `cross` rounds the quotient, both choices of rules.py (conventions_fx; by default: on or before, exact)."""
        fund_currency = self.funds[fund]
        if fund_currency == policy_currency:
            return D(1)
        rate = (lookup or Exchange.chf)
        quotient = rate(self, policy_currency, date) / rate(self, fund_currency, date)
        return cross(quotient) if cross else quotient
