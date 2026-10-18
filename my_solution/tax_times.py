"""t7: what a payout paid, in policy currency: the sum of its WDR, SUR and DTH bookings in NRBOOK.

Those bookings keep their amounts in the extract (only PRM, ADM, AMC and RSK lost them), so the amount of a
withdrawal, a surrender or a death claim is read, not replayed.

t7: the time Neuron processed something, and the first version of a policy.

Every row of the tax tables carries `_CHGTS` (YYYYMMDDhhmmss): when Neuron was told. A version entered after a payout
was processed cannot have been used for it (a move reported late is taxed in the old country).
"""
from collections import defaultdict
from orders import order_bookings
import datetime as dt
from functools import cache
from tables import grouped


def paid_out(folder):
    """{(policy, event): paid out in cents}, the bookings of each payout summed (a payout may book per fund)."""
    paid = defaultdict(int)
    for row in order_bookings(folder):
        if row['BK_BKTYP'] in ('WDR', 'SUR', 'DTH'):
            paid[row['BK_POLNR'], row['BK_EVTNR']] += abs(int(row['BK_AMTPC']))
    return paid


def timestamp(value):
    """A `T` column as a datetime; an empty one means "always known"."""
    return dt.datetime.strptime(value, '%Y%m%d%H%M%S') if value else dt.datetime.min


@cache
def policies(folder):
    """{policy: first version of NRPOLH}: the currency, the start and the premium frequency, which never change
    between versions in the extract."""
    return {pid: min(rows, key=lambda r: int(r['PH_VRSNR'])) for pid, rows in grouped(folder, 'NRPOLH', 'PH_POLNR').items()}
