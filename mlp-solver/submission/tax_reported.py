"""t7, Switzerland: withholding tax reported for a holder with status M, not withheld (a hypothesis).

The yearly table lists what Neuron "withheld, accrued or reported". A holder with status M is reported to the tax
office instead of taxed; the tax that would apply (8 % of a payout above 5000 CHF) may be what Neuron reported. Whether
the table lists it is rules.py T7_REPORTED_VST: 884 years of the extract, 11 of them have a row already
(tax_reported_years sums them per year).
"""
from decimal import Decimal as D
from eras import rounded
from tax_money import convert
from tax_premiums import era
from tax_residence import rate
from tax_switzerland import above


def reported(folder, payout, home):
    """The withholding tax a payout to a holder with status M above the threshold would carry, else 0: 8 % of the
    payout in CHF at the rate known when it was processed, rounded like a withheld one."""
    base = convert(folder, payout.amount, payout.currency, 'CHF', payout.date, era(payout))
    if home.reporting != 'M' or not above(folder, payout, base):
        return D(0)
    return rounded(base * rate(folder, 'CH', 'VST', payout.date, payout.processed), era(payout))
