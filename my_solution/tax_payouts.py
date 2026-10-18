"""t7: the payouts the tax module works on: withdrawals (event 400), surrenders (410) and death claims (500).

EV_PCTG is the share of a withdrawal and EV_CHGTS the time Neuron processed the payout. None of the 2,493 payouts
of the extract is reversed; a reversed one (event 900) would be left out.
"""
from collections import defaultdict, namedtuple
from functools import cache
from tables import matching, day, scaled, reversals
from tax_times import timestamp, policies, paid_out
import rules

KINDS = {'400': 'withdrawal', '410': 'surrender', '500': 'death'}
Payout = namedtuple('Payout', 'policy event kind date share processed amount currency paid')


@cache
def payouts(folder):
    """{policy: [Payout]} by event number, the amount in policy currency as rules.py T7_PAYOUT_AMOUNT says (net of
    the surrender penalty). The event number orders them as Neuron processed them, which tax_gain and tax_collect
    need: what one payout pays back or collects, the next does not."""
    paid, cancelled, heads, result = paid_out(folder), reversals(folder), policies(folder), defaultdict(list)
    for row in matching(folder, 'NREVNT', 'EV_EVTTP', set(KINDS)):
        pid, event = row['EV_POLNR'], row['EV_EVTNR']
        if (pid, event) not in cancelled:
            kind, date = KINDS[row['EV_EVTTP']], day(row['EV_EFFDT'])
            result[pid].append(Payout(pid, int(event), kind, date, scaled(row['EV_PCTG'] or 0), timestamp(row['EV_CHGTS']),
                                      rules.T7_PAYOUT_AMOUNT(folder, heads[pid], kind, date, scaled(paid.get((pid, event), 0), 2), rules),
                                      heads[pid]['PH_CCY'], scaled(paid.get((pid, event), 0), 2)))
    for items in result.values():
        items.sort(key=lambda p: p.event)
    return result
