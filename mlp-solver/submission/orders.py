"""Customer orders: switches, withdrawals, surrenders and death claims move units as they were booked.

Event type (EV_EVTTP) to booking type (BK_BKTYP) in the export: 200 -> 6,558 SWO + 6,558 SWI,
400 -> 6,171 WDR, 410 -> 5,143 SUR, 500 -> 359 DTH. Corrections (990) book 123 SWI rows, left out.
"""
from collections import defaultdict
from functools import cache
from tables import matching, day, scaled, reversals

ORDER_TYPES = {'SWO', 'SWI', 'WDR', 'SUR', 'DTH'}  # switch out / in, withdrawal, surrender, death benefit
ORDER_EVENTS = {'200', '400', '410', '500'}  # switch, withdrawal, surrender, death claim


@cache
def order_bookings(folder):
    """The NRBOOK rows of customer orders, read once (6.8 million rows): t3 replays them, t7 sums its payouts."""
    return list(matching(folder, 'NRBOOK', 'BK_BKTYP', ORDER_TYPES))


@cache
def customer_orders(folder):
    """Unit movements of the customer orders that were not reversed, by policy: (trade date, fund, pot, units).

    Unlike premiums and charges, these bookings are complete in the export, so they are taken over.
    138 order events were reversed (900); their bookings stay in NRBOOK and are skipped.
    """
    rejected = reversals(folder)
    events = {(r['EV_POLNR'], r['EV_EVTNR']) for r in matching(folder, 'NREVNT', 'EV_EVTTP', ORDER_EVENTS)
              if (r['EV_POLNR'], r['EV_EVTNR']) not in rejected}
    orders = defaultdict(list)
    for r in order_bookings(folder):
        if (r['BK_POLNR'], r['BK_EVTNR']) in events:
            orders[r['BK_POLNR']].append((day(r['BK_TRDDT']), r['BK_FNDID'], r['BK_POTCD'], scaled(r['BK_UNITS'])))
    return orders
