"""t7, Italy: the stamp duty of one booking: its base in EUR times its share of the year times the BOL rate known at
`known_at`, rounded by the system live then. Called with the time of the booking itself, and again by the 2019
correction with the time of that run (tax_stamp_fix), whose rates for 2017 to mid-2019 were raised.

t7, Italy: the 2019 correction of the stamp duty (run TAXFIX19, 2019-07-20).

The rate of 2017 to mid-2019 was raised afterwards (NRTAXR version 2, entered 2019-07-15). The run booked, for every
duty booked before, its base times the raise of the rate: in the second example of the task, those of 2017 and 2018
in one amount (194.54), rounded once.
"""
from eras import rounded
from tax_residence import rate
from tax_stamp_base import base
import rules


def duty(folder, booking, currency, known_at):
    """The duty of one booking with the rates known at `known_at` (a datetime), rounded by the system live then."""
    return rounded(exact(folder, booking, currency, known_at), known_at.date())


def corrected(folder, currency, booked, fixes):
    """[(correction booking, amount)] of the duties `booked` before the run, as rules.py T7_BOL_CORRECTION says (the
    released samples: the base times the raise of the rate, summed and rounded once: 104 of 110 rows, against 98
    recalculating each duty)."""
    if not fixes:
        return []
    at = fixes[0].processed
    rows = [(exact(folder, b, currency, at), amount, raise_of(folder, b, currency, at)) for b, amount in booked if b.processed < at]
    return rules.T7_BOL_CORRECTION(fixes, rows, lambda amount: rounded(amount, at.date()))


def exact(folder, booking, currency, known_at):
    """The duty of one booking with the rates known at `known_at`, not rounded."""
    amount, share = base(folder, booking, currency)
    return amount * share * rate(folder, 'IT', 'BOL', booking.date, known_at)


def raise_of(folder, booking, currency, known_at):
    """The base of one booking times the rate known at `known_at` less the rate it was booked with, not rounded."""
    amount, share = base(folder, booking, currency)
    return amount * share * (rate(folder, 'IT', 'BOL', booking.date, known_at) - rate(folder, 'IT', 'BOL', booking.date, booking.processed))
