"""t7, Germany: the taxes withheld from a taxed payout: capital gains tax (KST), solidarity surcharge (SOL) and church
tax (KIS). SOL and KIS are rates of KST, cut to the cent in every era (rules.py T7_SURCHARGE_ROUNDING) (the first example of the task: 1407.04 and
77.38; the released samples: rounding half up is a cent too high on three of them). Church tax from 2009 for members: 8 % in Bavaria and Baden-Wuerttemberg, 9 % elsewhere.
"""
from decimal import Decimal as D
import rules
from eras import rounded
from tax_premiums import taxed, era
from tax_residence import rate



def withheld(folder, payout, home, base, at):
    """{KST, SOL, KIS} of a taxed payout with taxable base `base`; KST with church tax as rules.py T7_KST_CHURCH."""
    church, _ = taxed(folder, payout, 'KIS', lambda: home.church)
    k, when = rate(folder, 'DE', 'KIS', payout.date, at, home.region) if church else D(0), era(payout)
    kst = rounded(base * rules.T7_KST_CHURCH(rate(folder, 'DE', 'KST', payout.date, at), k), when)
    sol_booked, _ = taxed(folder, payout, 'SOL', lambda: True)
    sol = rules.T7_SURCHARGE_ROUNDING(kst * rate(folder, 'DE', 'SOL', payout.date, at), lambda x: rounded(x, when)) if sol_booked else 0
    return {'KST': kst, 'SOL': sol, 'KIS': rules.T7_SURCHARGE_ROUNDING(kst * k, lambda x: rounded(x, when))}
