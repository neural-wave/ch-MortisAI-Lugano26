"""Exchange rates (NRFXRT) as date-sorted series of CHF per unit of currency, and the currency
of each fund (NRFUND) that says which series a fund's prices are converted with.

Currencies CHF, EUR, USD, GBP, SEK; the series start 1993-11-02, EUR on 1998-12-31.
"""
from collections import defaultdict
from tables import stream, table, scaled


def fund_currencies(folder):
    """Currency of each fund (NRFUND.FD_CCY): 30 funds in CHF, EUR, USD, GBP and SEK."""
    return {r['FD_FNDID']: r['FD_CCY'] for r in table(folder, 'NRFUND')}


def chf_rates(folder):
    """CHF per unit of currency (NRFXRT.FX_RATE, N(6)) by (upper-case currency, rate date).

    80 of the 39,484 rows carry a lower-case code (eur, usd, ...). None of them
    shares a day with the upper-case series, so they only fill its gaps; should both
    exist, the upper-case row wins.
    """
    rates = {}
    for row in stream(folder, 'NRFXRT'):
        key = row['FX_CCY'].upper(), int(row['FX_RATDT'])
        if key not in rates or row['FX_CCY'].isupper():
            rates[key] = scaled(row['FX_RATE'])
    return rates


def rate_series(folder):
    """Per currency, (rate date, CHF per unit) sorted by date."""
    series = defaultdict(list)
    for (ccy, date), rate in chf_rates(folder).items():
        series[ccy].append((date, rate))
    return {ccy: sorted(rows) for ccy, rows in series.items()}


def dates_of(series):
    """The date column of each series (rates here, prices in market_prices), the search keys for bisect."""
    return {key: [r[0] for r in rows] for key, rows in series.items()}
