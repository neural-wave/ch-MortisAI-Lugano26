"""t7, Switzerland: withholding tax on a payout (VST), 8 % of the payout in CHF.

Withheld when the holder objected to being reported (status E) and the payout is above 5000 CHF (the NRTAXR
threshold): 257 of the 259 such payouts have a VST booking, death claims included. The base of a payout taxed is the
payout in CHF; of one not taxed (status M, or below the threshold) rules.py T7_CH_UNTAXED_BASE decides.
"""
import rules
from eras import rounded
from tax_money import convert
from tax_premiums import taxed, era
from tax_residence import rate, threshold
from tax_gain import gain


def payout_tax(folder, payout, home):
    """(taxable base, {tax type: amount}) of a payout to a holder living in Switzerland. The tax is 8 % of the
    payout in CHF at the rate known when it was booked, rounded by the system that processed the payout."""
    base = convert(folder, payout.amount, payout.currency, 'CHF', payout.date, era(payout))
    applies, at = taxed(folder, payout, 'VST', lambda: home.reporting == 'E' and above(folder, payout, base))
    if not applies:
        return rules.T7_CH_UNTAXED_BASE(base, lambda: gain(folder, payout, 'CHF')), {'VST': 0}
    return base, {'VST': rounded(base * rate(folder, 'CH', 'VST', payout.date, at), era(payout))}


def above(folder, payout, base):
    """Whether the payout in CHF is above the threshold: 257 of 259 payouts so; the other 2 are withdrawals just
    above it (5042.28 and 5092.72 CHF) without a booking."""
    return base > threshold(folder, 'CH', 'VST', payout.date)
