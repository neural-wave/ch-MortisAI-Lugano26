"""t7, Italy: the stamp duty of one booking: its base in EUR times its share of the year times the BOL rate known at
`known_at`, rounded by the system live then. Called with the time of the booking itself, and again by the 2019
correction with the time of that run (tax_stamp_fix), whose rates for 2017 to mid-2019 were raised.

t7, Italy: the 2019 correction of the stamp duty (run TAXFIX19, 2019-07-20).

The rate of 2017 to mid-2019 was raised afterwards (NRTAXR version 2, entered 2019-07-15). The run recalculated every
duty booked before with the rates known then and booked the sum of the exact rate differences, rounded once.
In the second example of the task, the 2017 and 2018 differences make one amount (194.54).
"""
from eras import rounded
from tax_residence import rate
from tax_stamp_base import base
from decimal import Decimal as D


def duty(folder, booking, currency, known_at):
    """The duty of one booking with the rates known at `known_at` (a datetime)."""
    amount, share = base(folder, booking, currency)
    return rounded(amount * share * rate(folder, 'IT', 'BOL', booking.date, known_at), known_at.date())


def corrected(folder, currency, booked, fixes):
    """[(correction booking, amount)]: the exact rate differences batched and rounded once.
    Additional correction rows at the same run carry no remaining difference."""
    if not fixes:
        return []
    at = fixes[0].processed
    # TAXFIX batches the exact differences before the single cent rounding.
    # Rounding each old/new duty separately changes the resulting correction.
    exact = D(0)
    for booking, amount in booked:
        if booking.processed >= at:
            continue
        value, share = base(folder, booking, currency)
        old_rate = rate(folder, 'IT', 'BOL', booking.date, booking.processed)
        new_rate = rate(folder, 'IT', 'BOL', booking.date, at)
        exact += value * share * (new_rate - old_rate)
    correction = rounded(exact, at.date())
    amounts = [correction] + [D('0.00')] * (len(fixes) - 1)
    return list(zip(fixes, amounts))
