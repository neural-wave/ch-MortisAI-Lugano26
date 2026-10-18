"""t7: one row of t7_tax_payout from the taxes of a payout.

    withholding   CH VST, IT SOS, DE KST
    surcharges    DE SOL + KIS
    stamp duty    the Italian stamp duty collected at the payout (BOC)
The remittance date is what rules.py T7_NO_REMITTANCE gives when nothing was withheld (the task: None), else
tax_remit's day.
"""
from decimal import Decimal as D
import rules
from tax_annual_table import remittance

ZERO = D('0.00')


def row(payout, country, base, amounts, home):
    """(country, taxable base, withholding, surcharges, stamp duty, remittance date)."""
    withholding = sum((amounts.get(k, 0) for k in ('VST', 'SOS', 'KST')), ZERO)
    surcharges = sum((amounts.get(k, 0) for k in ('SOL', 'KIS')), ZERO)
    stamp = amounts['BOC'] + ZERO
    paid = withholding or surcharges or rules.T7_BOC_DATED(stamp)
    return country, base + ZERO, withholding, surcharges, stamp, remittance(country, payout.date) if paid else rules.T7_NO_REMITTANCE()
