"""The premium items that actually bought units: NRPREM rows minus unpaid and reversed items.

Evidence on the extract: NRPREM has 323,441 items. 9,105 have no received date and no received amount
(states O 'open' and W 'written off' in NRCODE domain PRSTAT). 7,880 are cancelled by a reversal event,
exactly the items in state R 'direct debit returned'. The 306,456 that remain are exactly the state P 'paid' items.
"""
from functools import cache
from tables_read import matching
from tables_grouped import table


@cache
def reversals(folder):
    """(policy, event) pairs cancelled by a reversal.

    In NREVNT a reversal has event type 900 and names the event it cancels in EV_REVNR. Of the 8,130
    reversals, 7,880 cancel premium bookings; the others cancel other events, such as customer orders.
    """
    return {(r['EV_POLNR'], r['EV_REVNR']) for r in matching(folder, 'NREVNT', 'EV_EVTTP', {'900'})}


def _paid(row, cancelled):
    """Money was received (PR_RCVDT and PR_AMTRC set) and the booking event PR_EVTNR was not reversed."""
    return int(row['PR_RCVDT']) > 0 and int(row['PR_AMTRC']) > 0 \
        and (row['PR_POLNR'], row['PR_EVTNR']) not in cancelled


@cache
def received(folder):
    """Premium items that were paid and not reversed later, in NRPREM order."""
    cancelled = reversals(folder)
    return [r for r in table(folder, 'NRPREM') if _paid(r, cancelled)]
