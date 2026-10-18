"""t7: the premiums a payout pays back: the items paid and not reversed (tables.received), by money date.

The gain of a payout is what it paid less these premiums (tax_gain), each converted on its own money date.

t7: whether Neuron booked a tax, and the day whose system rounds it (rules.py T7_PRESENCE).

NRTAXB is Neuron's record, its mistakes included, so it decides by default. The rules the data show agree with it:
Swiss withholding tax for status E above the threshold 257 of 259 payouts, German capital gains tax on a gain outside
the old regime 86 of 92, Italian substitute tax on a gain except death claims 153 of 158.
"""
from collections import defaultdict, namedtuple
from functools import cache
from tables import day, received
import rules
from tax_bookings import booked


Premium = namedtuple('Premium', 'event date amount')


@cache
def premiums(folder):
    """{policy: [Premium]} in the order of their money dates."""
    result = defaultdict(list)
    for row in received(folder):
        result[row['PR_POLNR']].append(Premium(int(row['PR_EVTNR']), day(row['PR_RCVDT']), rules.T7_PREMIUM_AMOUNT(row)))
    for items in result.values():
        items.sort(key=lambda p: p.date)
    return result


def taxed(folder, payout, kind, rule):
    """(taxed?, time the tax was booked) of one tax of a payout; `rule()` says whether the rules found tax it."""
    return rules.T7_PRESENCE(booked(folder, payout.policy, payout.event, kind), rule, payout.processed)


def era(payout):
    """The day whose system rounds the taxes of a payout: the payout day (Neuron processes every payout on that day,
    so the processing day of the first two examples gives the same system)."""
    return payout.date
