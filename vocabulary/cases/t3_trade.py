"""t3: when a premium buys its units and into which pot (the trade date and the pot of each PRM booking).

Target: the trade date and the pot of the PRM bookings in NRBOOK (a diagnostic: the solution derives both).
Holes: the trade date after the money date (conventions_trade), the day that decides the pot and the boundary
of the initial months (conventions_premium).
"""
from conventions import TRADE_DATES, PREMIUM_DATES, POT_BOUNDARIES
from engine import is_holdout
from cases.t3_common import bookings, premium_items, light_ledger

TITLE, TASK, NEEDS_FOUND, SAMPLE = 't3 trade date and pot of a premium', 't3_surrender_value', True, 20
RULES = {'trade date': 'T3_TRADE_DATE', 'pot date': 'T3_POT_DATE', 'pot boundary': 'T3_POT_BOUNDARY'}
NOTES = {'trade date': 'the day a premium buys units', 'pot date': 'the day that decides pot 1 or 2'}


def build(legacy, targets, found):
    from tables import day
    from conventions_dates import add_months
    items, rows = premium_items(legacy), []
    for key, b in bookings(legacy, targets, ('PRM',), 100).items():
        item, ledger = items[b['policy'], b['event']], light_ledger(legacy, b['policy'])
        rows.append({'policy': b['policy'], 'key': key, 'holdout': is_holdout(b['policy']), 'target': (b['trade'], b['pot']),
                     'item': item, 'ledger': ledger, 'fund': b['fund'], 'money': day(item['PR_RCVDT']),
                     'initial end': add_months(ledger.start, int(ledger.product['PD_INIMON'])),
                     'features': {'fund': b['fund'], 'money weekday': day(item['PR_RCVDT']).weekday()}})
    return rows, {'trade date': TRADE_DATES, 'pot date': PREMIUM_DATES, 'pot boundary': POT_BOUNDARIES}, formula


def formula(row, c):
    trade = c['trade date'](row['ledger'].market, row['fund'], row['money'])
    initial = c['pot boundary'](c['pot date'](row['item'], row['ledger'].history), row['initial end'])
    return trade, '1' if initial else '2'
