"""t7: the gain of a payout in the tax currency: what it paid out less the premiums it pays back.

A withdrawal of share s pays back s of the premiums not paid back yet; a surrender or a death claim pays back all of
them. 64 % of the surrenders are at a loss in the extract: a loss is not taxed.

t7: the version of a row Neuron used: valid on the day and entered by the time it processed the tax.

NRHOLD, NRADDR and NRTAXR are versioned twice: valid from `_VLDFR` to `_VLDTO` (both included) and entered at
`_CHGTS`. Of the versions valid on the day and entered by `at` (None: every version) the highest number wins.
"""
from functools import cache, partial
from decimal import Decimal as D
import rules
from eras import rounded
from tax_payouts import payouts
from tax_birth import paid_in
from tax_money import convert
from tax_premiums import era
from tables import legacy
from tax_times import timestamp


@cache
def bases(folder, policy, currency):
    """{event: premiums paid back} of the payouts of a policy, in `currency`. The payouts run in event order, so a
    withdrawal's paid back premiums are no longer open for the next payout; its share is rounded to the cent and
    carried rounded as rules.py T7_BASIS_SHARE says (exact shares left 74 bases with fractions of a cent)."""
    result, returned = {}, D(0)
    for p in payouts(folder)[policy]:
        still_open = paid_in(folder, p, currency) - returned
        result[p.event] = rules.T7_BASIS_SHARE(still_open * p.share, partial(rounded, date=era(p))) if p.kind == 'withdrawal' else still_open
        returned += result[p.event]
    return result


@cache
def gains(folder, policy, currency):
    """{event: gain} of the payouts of a policy, in `currency`: what it paid less the premiums it paid back;
    negative for a loss."""
    paid_back = bases(folder, policy, currency)
    return {p.event: convert(folder, p.amount, p.currency, currency, p.date, era(p)) - paid_back[p.event]
            for p in payouts(folder)[policy]}


def gain(folder, payout, currency):
    """The gain of one payout in `currency` (EUR for Italy and Germany, CHF for the Swiss alternative base)."""
    return gains(folder, payout.policy, currency)[payout.event]


def known(rows, date, prefix, at):
    """The highest version of `rows` valid on `date` among those entered by `at`, or None."""
    n = legacy(date)
    found = [r for r in rows if int(r[f'{prefix}_VLDFR']) <= n <= int(r[f'{prefix}_VLDTO'])
             and (at is None or timestamp(r[f'{prefix}_CHGTS']) <= at)]
    return max(found, key=lambda r: int(r[f'{prefix}_VRSNR'])) if found else None
