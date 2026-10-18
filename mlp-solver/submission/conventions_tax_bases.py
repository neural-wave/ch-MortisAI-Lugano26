"""t7: open choices of the amounts that no local data decides (the leaderboard or the meaning decides; rules.py).

Switzerland: the taxable base of a payout Neuron withheld nothing from (reporting status M, or E below the threshold)
is the payout in CHF, zero, or the gain. The yearly table lists what Neuron "withheld, accrued or reported": the
withholding tax of a holder with status M (8 % above the threshold) may have been reported without being withheld.
"""
from decimal import Decimal as D

ZERO = D('0.00')


def the_payout(base, gain):
    """The payout in CHF, as if the tax had been due."""
    return base


def nothing(base, gain):
    """Zero: without a tax Neuron kept no base."""
    return ZERO


def the_gain(base, gain):
    """The gain in CHF (`gain` calculates it), not below zero."""
    return max(gain(), ZERO)


def not_reported(table, reported):
    """The yearly table without reported withholding tax."""
    return table


def reported_in_new_years(table, reported):
    """Reported withholding tax as rows of its own, only in years the table has no row for (existing rows stay)."""
    return {**table, **{key: (ZERO, amount, ZERO, ZERO, ZERO, ZERO, ZERO)
                        for key, amount in reported.items() if key not in table}}


UNTAXED_BASES = {'the payout in CHF': the_payout, 'zero': nothing, 'the gain, not below zero': the_gain}
REPORTED_VST = {'none': not_reported, 'in the years without a row': reported_in_new_years}
