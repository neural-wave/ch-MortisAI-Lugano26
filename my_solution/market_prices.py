"""Unit prices of the funds (NRFPRC) as date-sorted series.

Series are {fund: [(CYYMMDD date, values...), ...]} sorted by date, so that Market
can find "the last date on or before" with bisect on the raw integers.
"""
from collections import defaultdict
from tables import stream, scaled

BID, ASK, MID = 1, 2, 3  # the columns of a price series after its date


def is_newer(row, latest, key):
    """True when `row` is the first or a later publication (FP_CHGTS) of its fund and day."""
    return key not in latest or row['FP_CHGTS'] > latest[key]['FP_CHGTS']


def latest_prices(folder):
    """The last publication of every (fund, price date) in NRFPRC.

    Neuron restated prices by inserting a new row with a later FP_CHGTS instead of
    updating the old one: 231,311 rows hold 230,647 distinct fund days, so 664 are
    restatements. The schema states that the latest publication counts.
    """
    latest = {}
    for row in stream(folder, 'NRFPRC'):
        key = row['FP_FNDID'], int(row['FP_PRCDT'])
        if is_newer(row, latest, key):
            latest[key] = row
    return latest


def price_series(folder):
    """Per fund, (price date, bid, ask, mid) sorted by date; prices are N(6) fixed point. Which price a
    booking takes is a choice of rules.py (conventions_trade)."""
    prices = defaultdict(list)
    for (fund, date), row in latest_prices(folder).items():
        prices[fund].append((date, scaled(row['FP_BIDPR']), scaled(row['FP_ASKPR']), scaled(row['FP_MIDPR'])))
    return {fund: sorted(rows) for fund, rows in prices.items()}
