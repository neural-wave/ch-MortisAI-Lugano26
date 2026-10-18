"""t7, Italy: the values the yearly stamp duty is taken on: on 31 December, in policy currency.

They come from the fund ledger of t3 (accounts_replay.replay, the very code of t3), but only for the policies with a
yearly duty (about a fifth of them), each on its own year ends: replaying every policy for this took 30 of the 38
seconds of t7. rules.py T7_BOL_VALUE says which value (the policy value; the surrender value differs in 1,517 rows).
"""
from functools import cache
import rules
from tables import by_key, received
from orders import customer_orders
from accounts_replay import replay
from guard import per_policy
from tax_stamp_bookings import stamp_bookings, year_end


@cache
def year_end_values(folder):
    """{(policy, 31 December): value} for every year-end booking; a policy the replay fails on is reported and left
    out (guard.per_policy), its duty then 0."""
    orders, paid = customer_orders(folder), by_key(received(folder), 'PR_POLNR')

    def values(pid, items):
        ledger, found = replay(folder, pid, paid[pid], orders[pid], sorted({b.date for b in items if year_end(b)}))
        return {(pid, d): rules.T7_BOL_VALUE(folder, ledger, d, v) for d, v in found.items()}
    return per_policy('t7 stamp duty values', stamp_bookings(folder).items(), values)
