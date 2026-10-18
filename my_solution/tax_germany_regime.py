"""t7, Germany: the regime of a payout, by the law (no local amount checks its dates and ages).

    old    begun before 2005, premiums for five years or more, paid after twelve years: tax free
    half   begun from 2005, paid after twelve years and after the holder's 60th birthday (62nd for contracts begun
           from 2012): half the gain is taxed (HEV)
    full   any other payout

t7, Germany: the share of the gain that is taxed under a regime (tax_germany_regime).

From 2018 the law exempts a share of the gain (TFS, 15 % in NRTAXR); Neuron did not apply it (rules.py T7_TFS: the
released samples tax two withdrawals of 2020 and 2023 in full). A half-income payout takes the HEV share (50 %), its
exemption as rules.py T7_TFS_WITH_HEV says. An old contract is
tax free, unless NRTAXB has a KST booking for its payout: then tax_germany taxes it in full, as Neuron did.
"""
import datetime as dt
from tables import day
from conventions_birth import completed_years
from tax_birth import birth
from tax_times import policies
from decimal import Decimal as D
import rules
from tax_residence import rate


OLD_REGIME_END, TAX_FREE_YEARS = dt.date(2005, 1, 1), 12
HEV_AGES = ((dt.date(2012, 1, 1), 62), (dt.date.min, 60))  # (contracts begun from, age)


def regime(folder, payout, home):
    """'old', 'half' or 'full' for one payout: by the start and the premium frequency of the contract (a single
    premium, frequency E, never had the old privilege) and the holder's age at the payout."""
    head = policies(folder)[payout.policy]
    start = day(head['PH_BEGDT'])
    if completed_years(start, payout.date) < TAX_FREE_YEARS:
        return 'full'
    if start < OLD_REGIME_END:
        return 'old' if head['PH_FREQ'] != 'E' else 'full'
    age = next(age for since, age in HEV_AGES if start >= since)
    return 'half' if completed_years(birth(folder, home.person), payout.date) >= age else 'full'


def taxable_share(folder, payout, kind, at):
    """The share of the gain taxed under regime `kind` ('old', 'half' or 'full')."""
    if kind == 'old':
        return D(0)
    exempt = rate(folder, 'DE', 'TFS', payout.date, at)
    if kind != 'half':
        return D(1) - rules.T7_TFS(exempt)
    return rate(folder, 'DE', 'HEV', payout.date, at) * (D(1) - rules.T7_TFS_WITH_HEV(exempt))
