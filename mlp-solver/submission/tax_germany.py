"""t7, Germany: capital gains tax on the gain of a payout in EUR (25 % of the taxable part, tax_germany_share).

A payout is taxed if NRTAXB has its KST booking (the rules found: a gain, not the old regime, not a death claim);
an old contract Neuron taxed anyway is taxed in full. The base is the taxable part of the gain, rounded.
"""
from decimal import Decimal as D
from eras import rounded
from tax_premiums import taxed, era
from tax_gain import gain
import rules
from tax_germany_regime import regime
from tax_germany_regime import taxable_share
from tax_germany_withheld import withheld


def payout_tax(folder, payout, home):
    """(taxable base, {tax type: amount}) of a payout to a holder living in Germany. Untaxed (a loss, an old
    contract, a death claim): the base is still the taxable part of the gain, the taxes 0."""
    profit, kind = gain(folder, payout, 'EUR'), regime(folder, payout, home)
    applies, at = taxed(folder, payout, 'KST', lambda: profit > 0 and kind != 'old' and payout.kind != 'death')
    kind = 'full' if applies and kind == 'old' else kind
    base = rounded(rules.T7_LOSS_BASE(profit, 'DE') * taxable_share(folder, payout, kind, at), era(payout))
    return base, withheld(folder, payout, home, base, at) if applies else {'KST': 0, 'SOL': 0, 'KIS': 0}
