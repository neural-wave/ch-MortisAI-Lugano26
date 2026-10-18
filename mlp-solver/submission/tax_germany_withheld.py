"""t7, Germany: the taxes withheld from a taxed payout: capital gains tax (KST), solidarity surcharge (SOL) and church
tax (KIS). KST follows the system era; SOL and KIS truncate separately to cents in both eras.
SOL and KIS are rates of the rounded KST (the first task example: 1407.04 and 77.38).
Church tax from 2009 for members: 8 % in Bavaria and Baden-Wuerttemberg, 9 % elsewhere.
"""
from decimal import Decimal as D
import rules
from eras import rounded
from conventions_rounding import truncate
from tax_premiums import taxed, era
from tax_residence import rate


def withheld(folder, payout, home, base, at):
    """{KST, SOL, KIS} of a taxed payout with taxable base `base`; KST with church tax as rules.py T7_KST_CHURCH."""
    church, _ = taxed(folder, payout, 'KIS', lambda: home.church)
    k, when = rate(folder, 'DE', 'KIS', payout.date, at, home.region) if church else D(0), era(payout)
    kst = rounded(base * rules.T7_KST_CHURCH(rate(folder, 'DE', 'KST', payout.date, at), k), when)
    sol_booked, _ = taxed(folder, payout, 'SOL', lambda: True)
    sol = truncate(kst * rate(folder, 'DE', 'SOL', payout.date, at)) if sol_booked else 0
    return {'KST': kst, 'SOL': sol, 'KIS': truncate(kst * k)}
