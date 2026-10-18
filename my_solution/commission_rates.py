"""NRCOMR commission rates; all six rows are valid from 1990-01-01 with an open end."""
from tables import scaled, version


def commission_rate(rates, tier, kind, date):
    """NRCOMR rate of broker tier and premium type valid on `date`.

    Regular premiums (L) pay A 4 %, B 3 %, C 2 %; single premiums (E) A 1.5 %, B 1 %, C 0.5 %.
    """
    return scaled(version([r for r in rates if r['CR_TIER'] == tier and r['CR_PAYTP'] == kind], date, 'CR')['CR_RATE'])
