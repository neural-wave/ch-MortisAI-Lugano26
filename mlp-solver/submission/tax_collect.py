"""t7, Italy: the stamp duty collected at a payout (BOC), from what tax_stamp accrued.

A payout with a BOC booking collects the duty open by then (tax_collect_due); a withdrawal as rules.py T7_BOC_SHARE
says (its share, by default), any other payout all of it. The rest stays open for the next payout. It is collected
whatever the country of residence is now: 12 of the 295 BOC bookings are of holders who had left Italy.
"""
from decimal import Decimal as D
from functools import cache
from tax_payouts import payouts
from tax_bookings import booked
from tax_stamp import accrued
from tax_stamp_bookings import newly_due, taken


@cache
def collections(folder, policy):
    """{event: BOC} of the payouts of one policy, in event order: the open duty carries from one payout to the
    next, and what a payout collects is rounded by the system that processed it."""
    result, open_duty, used, items = {}, D('0.00'), set(), payouts(folder)[policy]
    duties = accrued(folder, policy, items[0].currency) if items else []
    for p in items:
        new = newly_due(duties, used, p)
        used |= new
        open_duty += sum((duties[i][1] for i in sorted(new)), D('0.00'))
        result[p.event] = taken(open_duty, p, booked(folder, policy, p.event, 'BOC'))
        open_duty -= result[p.event]
    return result


def collected(folder, payout):
    """BOC of one payout."""
    return collections(folder, payout.policy)[payout.event]
