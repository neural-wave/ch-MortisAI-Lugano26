"""t7: amounts in the tax currency (CHF for Switzerland, EUR for Italy and Germany), rounded like the system.

NRFXRT gives CHF per unit and a cross rate goes via CHF, exact. The rate of the last day on or before the date counts;
a day before the first rate of a currency (EUR starts 1998-12-31) takes that first rate, so premiums from 1994 convert
to EUR too. The system live on the day `era` rounds (eras.rounded: COBOL truncates, Neuron NG half up).
"""
from bisect import bisect_right
from decimal import Decimal as D
from functools import cache
from tables import legacy
from market_rates import rate_series, dates_of
from eras import rounded


@cache
def series(folder):
    """CHF rates by currency and their dates; CHF itself is 1 on every day."""
    rates = {**rate_series(folder), 'CHF': [(0, D(1))]}
    return rates, dates_of(rates)


@cache
def chf(folder, currency, date):
    """CHF per unit of `currency` on the last rate date on or before `date`, else the first rate (a premium of
    1994 in EUR takes the rate of 1998-12-31)."""
    rates, dates = series(folder)
    return rates[currency][max(bisect_right(dates[currency], legacy(date)) - 1, 0)][1]


def convert(folder, amount, currency, into, date, era):
    """`amount` in `currency` as `into` at the rate of `date`, rounded by the system live on `era`. The same
    currency is only rounded: a payout of a CHF policy to a Swiss holder keeps its cents."""
    exact = amount if currency == into else amount * chf(folder, currency, date) / chf(folder, into, date)
    return rounded(exact, era)
