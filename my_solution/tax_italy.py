"""t7, Italy: substitute tax on the gain of a payout (SOS), each rate on the part of the gain of its period (tax_italy_periods,
rules.py T7_SOS).

The gain is in EUR (tax_gain); a loss is not taxed and death claims are exempt (none of the 11 Italian death claims
has a SOS booking). The stamp duty on the policy value is in tax_stamp and tax_collect.
"""
from eras import rounded
from tax_premiums import taxed, era
from tax_italy_periods import substitute_tax
from tax_residence import rate
from tax_gain import gain
import rules


def payout_tax(folder, payout, home):
    """(taxable base, {tax type: amount}) of a payout to a holder living in Italy; the base of a loss is 0."""
    profit = gain(folder, payout, 'EUR')
    base = rules.T7_LOSS_BASE(profit, 'IT')
    applies, at = taxed(folder, payout, 'SOS', lambda: profit > 0 and payout.kind != 'death')
    tax = rules.T7_SOS(lambda: substitute_tax(folder, payout, profit), lambda: profit * rate(folder, 'IT', 'SOS', payout.date, at))
    return base, {'SOS': rounded(max(tax, 0), era(payout)) if applies and profit > 0 else 0}
