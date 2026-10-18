"""t7: the premiums a payout pays back (rules.py T7_PREMIUM_AMOUNT, T7_BASIS_SHARE).

A withdrawal pays back its share of the premiums still open. Carried exactly, that share leaves 74 bases of later
payouts with fractions of a cent, which no answer of Neuron can have (scoring_t7 compares exactly); rounded to the cent
and carried rounded, none. The premium is the amount received, as in t0 and t3; the amount due changes cents on 854
payouts.
"""
from tables import scaled


def received_amount(row):
    """The premium as received (PR_AMTRC), as in t0 and t3."""
    return scaled(row['PR_AMTRC'], 2)


def due_amount(row):
    """The premium as due (PR_AMTDU)."""
    return scaled(row['PR_AMTDU'], 2)


def exact_share(value, rounding):
    """The paid back share as it is, carried exactly to the next payout."""
    return value


def share_to_the_cent(value, rounding):
    """The paid back share rounded to the cent by the system of the payout, and carried rounded."""
    return rounding(value)


PREMIUM_AMOUNTS = {'received (PR_AMTRC)': received_amount, 'due (PR_AMTDU)': due_amount}
BASIS_SHARES = {'exact': exact_share, 'to the cent': share_to_the_cent}
