"""t7, Italy: which accrued stamp duties a payout can collect: those not counted yet that Neuron had booked by the
time it processed the payout, and the duty booked at the payout itself (the duty of its own year, booked with it).
A duty booked later (the yearly duty of a year still running) waits for the next payout.

t7, Italy: the stamp duty bookings (BOL) of every policy, in the order Neuron booked them.

Three kinds: the yearly duty on 31 December (event 0, batch TAXBATCH, 5,410 bookings), the duty at a payout during
the year (its event, also TAXBATCH, 134) and the 2019 correction of the 2017-2019 rate (event 0, run TAXFIX19, 375).
"""
from decimal import Decimal as D
import rules
from eras import rounded
from tax_premiums import era
from functools import cache
from tax_bookings import bookings


def newly_due(duties, used, payout):
    """The indexes of the accrued duties (booking, amount) that become due at `payout`, not in `used` yet."""
    return {i for i, (b, _) in enumerate(duties)
            if i not in used and (b.event == payout.event or b.processed <= payout.processed)}


def taken(open_duty, payout, collects):
    """What a payout collects of the open duty: nothing without a BOC booking, else its share (rules.py T7_BOC_SHARE)
    rounded by the system that processed it."""
    return rounded(open_duty * rules.T7_BOC_SHARE(payout), era(payout)) if collects else D('0.00')


CORRECTION = 'TAXFIX19'


@cache
def stamp_bookings(folder):
    """{policy: [BOL bookings]} by processing time, then event: the order the correction and the collection at
    a payout need to know what was booked before them."""
    result = {}
    for (pid, _), kinds in bookings(folder).items():
        result.setdefault(pid, []).extend(kinds.get('BOL', []))
    return {pid: sorted(items, key=lambda b: (b.processed, b.event)) for pid, items in result.items() if items}


def year_end(booking):
    """Whether a booking is the yearly duty of 31 December (not a payout, not the correction)."""
    return booking.event == 0 and booking.user != CORRECTION
