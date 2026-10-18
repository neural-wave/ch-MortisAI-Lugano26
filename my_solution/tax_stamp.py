"""t7, Italy: the stamp duty on the policy value (BOL) a policy accrued, booking by booking and per year.

The yearly table counts a duty in the year of its effective date (the second example of the task: the 2019 duty
421.57 and the correction 194.54 make 616.11). Which bookings exist is NRTAXB's record.
"""
from functools import cache
from decimal import Decimal as D
from tax_stamp_bookings import stamp_bookings, CORRECTION
from tax_stamp_fix import duty, corrected


@cache
def accrued(folder, policy, currency):
    """[(BOL booking, amount)] of a policy, in the order Neuron booked them: each duty with the rates known when
    it was booked, then the corrections of the 2019 run (tax_stamp_fix) in their place in time."""
    items = stamp_bookings(folder).get(policy, [])
    booked = [(b, duty(folder, b, currency, b.processed)) for b in items if b.user != CORRECTION]
    fixes = corrected(folder, currency, booked, [b for b in items if b.user == CORRECTION])
    return sorted(booked + fixes, key=lambda row: row[0].processed)


def yearly(folder, policy, currency):
    """{year: BOL} of a policy."""
    result = {}
    for b, amount in accrued(folder, policy, currency):
        result[b.date.year] = result.get(b.date.year, D('0.00')) + amount
    return result
