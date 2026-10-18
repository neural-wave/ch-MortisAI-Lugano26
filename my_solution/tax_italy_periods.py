"""t7, Italy: the substitute tax (SOS) of a gain that grew while the rate changed.

Italy taxed gains at 12.5 % until 2011, 20 % until mid-2014 and 26 % since. A payout pays each rate on the part of
its gain that accrued while that rate applied: the gain of a period is the policy value at its last day (the t3
ledger) less the premiums still open then (received, less those earlier withdrawals paid back), less the same of
the period before. A withdrawal takes its share of each period, and leaves the rest of it to the later payouts.
The last period is the rest of the gain. Found on the released t7 samples: 16 of the 20 SOS amounts exact, the
other four within 8 cents, against 8 with the rate of the payout day alone.
"""
import datetime as dt
from decimal import Decimal as D
from functools import cache
from tables import by_key, received, day
from orders import customer_orders
from accounts_replay import replay
from tax_rate_rows import rows_of
from tax_residence import rate
from tax_money import convert
from tax_premiums import era
from tax_birth import paid_in
from tax_payouts import payouts
from tax_gain import bases
import rules


@cache
def rate_ends(folder):
    """The last days of the SOS rates before the current one, from the valid-from days of NRTAXR."""
    starts = sorted({day(r['TX_VLDFR']) for r in rows_of(folder).get(('IT', 'SOS'), [])})
    return tuple(s - dt.timedelta(days=1) for s in starts[1:]
                 if rate(folder, 'IT', 'SOS', s) != rate(folder, 'IT', 'SOS', s - dt.timedelta(days=1)))


@cache
def values(folder, policy):
    """{last day of a rate: policy value in policy currency} for one policy (empty if the replay fails)."""
    try:
        paid = by_key(received(folder), 'PR_POLNR')
        return replay(folder, policy, paid[policy], customer_orders(folder)[policy], list(rate_ends(folder)))[1]
    except Exception:  # a policy the ledger cannot replay keeps the rate of the payout day
        return {}


def accrued(folder, payout, end, paid_back):
    """Policy value less the premiums received and not `paid_back`, in EUR, on the last day of a rate."""
    value = convert(folder, values(folder, payout.policy)[end], payout.currency, 'EUR', end, era(payout))
    return value - paid_in(folder, payout, 'EUR', end) + paid_back


def paid_back_by(folder, payout, end):
    """The premiums the earlier payouts of the policy paid back by `end`, in EUR."""
    paid_back = bases(folder, payout.policy, 'EUR')
    return sum((paid_back[p.event] for p in earlier(folder, payout) if p.date <= end), D(0))


def earlier(folder, payout):
    """The payouts of the policy before `payout`."""
    return [p for p in payouts(folder)[payout.policy] if p.event < payout.event]


def left(folder, payout, end):
    """The share of a period's gain the withdrawals after its last day and before `payout` left to it."""
    rest = D(1)
    for p in earlier(folder, payout):
        if p.kind == 'withdrawal' and p.date > end:
            rest *= 1 - p.share
    return rest


def substitute_tax(folder, payout, gain):
    """The SOS of a payout with a positive gain in EUR, before rounding: each rate on the gain of its period."""
    share = payout.share if payout.kind == 'withdrawal' else D(1)
    tax, before, taken = D(0), D(0), D(0)
    for end in rate_ends(folder):
        if end < payout.date and end in values(folder, payout.policy):
            paid_back, kept = rules.T7_SOS_EARLIER(paid_back_by(folder, payout, end), left(folder, payout, end))
            now = accrued(folder, payout, end, paid_back)
            part = (now - before) * share * kept
            tax += part * rate(folder, 'IT', 'SOS', end)
            taken += part
            before = now
    return tax + (gain - taken) * rate(folder, 'IT', 'SOS', payout.date)
