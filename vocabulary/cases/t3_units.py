"""t3 units of a booking: which price, which price and exchange-rate dates, how units are rounded.

Bookings of premiums (PRM) buy units, admin fee, management and risk charges (ADM, AMC, RSK)
cancel units. Target: the units of the diagnostic file t3_booking.csv, from its amount.
Holes: issue or redemption price, the date of the price, the date of the exchange rate,
the rounding of the units. A sample of 1 % of the policies keeps the run short
(RF_SHARE=5 python3 vocabulary/run.py ... for 5 %).
"""
import csv
import datetime as dt
import os
import zlib
from bisect import bisect_right
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_DOWN
from pathlib import Path
from bricks import rounding, by_era
from engine import is_holdout

MICRO = D('0.000001')
SHARE = int(os.environ.get('RF_SHARE', 1))  # percent of the policies
PRICE = {'issue price (ask)': 2, 'redemption price (bid)': 1}
DATES = ('booking price date', 'trade date', 'money date')
FX_DATES = ('trade date', 'day before trade date', 'money date')
UNITS = {'6 decimals, half up': rounding(ROUND_HALF_UP, MICRO), '6 decimals, truncate': rounding(ROUND_DOWN, MICRO),
         '6 decimals, truncate before 2007-08-11, then half up': by_era(rounding(ROUND_DOWN, MICRO), rounding(ROUND_HALF_UP, MICRO))}


def build(legacy, targets):
    from tables import stream, grouped, day
    from market import market
    sample = {}
    with open(Path(targets) / 't3_booking.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if zlib.crc32(r['policy_id'].encode()) % 100 < SHARE:
                sample[r['booking_id']] = r
    policies, m, rows = grouped(legacy, 'NRPOLH', 'PH_POLNR'), market(legacy), []
    for b in stream(legacy, 'NRBOOK'):
        r = sample.get(b['BK_BOOKID'])
        if r is None:
            continue
        pid = r['policy_id']
        trade = day(b['BK_TRDDT'])
        dates = dict(zip(DATES, (day(b['BK_PRCDT']), trade, day(b['BK_RCVDT']))))
        fx_dates = dict(zip(FX_DATES, (trade, trade - dt.timedelta(days=1), day(b['BK_RCVDT']))))
        ccy = min(policies[pid], key=lambda v: int(v['PH_VRSNR']))['PH_CCY']
        rows.append({'policy': pid, 'key': r['booking_id'], 'holdout': is_holdout(pid), 'target': D(r['units']), 'amount': D(r['amount_pc']),
                     'fund': b['BK_FNDID'], 'ccy': ccy, 'dates': dates, 'fx_dates': fx_dates, 'trade': trade,
                     'sign': 1 if r['booking_type'] == 'PRM' else -1, 'market': m,
                     'features': {'booking type': r['booking_type'], 'trade year': trade.year}})
    slots = {'price': PRICE, 'price date': {d: d for d in DATES}, 'exchange rate date': {d: d for d in FX_DATES}, 'units': UNITS}
    return rows, slots, formula


def price_on(m, fund, date, column):
    """Price of the last price date on or before `date`."""
    from tables import legacy as cyymmdd
    return m.prices[fund][bisect_right(m.price_dates[fund], cyymmdd(date)) - 1][column]


def formula(row, c):
    m = row['market']
    price = price_on(m, row['fund'], row['dates'][c['price date']], c['price'])
    fx = m.fx(row['ccy'], row['fund'], row['fx_dates'][c['exchange rate date']])
    return row['sign'] * c['units'](row['amount'] * fx / price, row['trade'])
