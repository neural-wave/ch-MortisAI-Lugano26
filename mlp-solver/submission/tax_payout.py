"""t7_tax_payout: for every payout since 1994 the country Neuron taxed it in, its taxable base, the taxes withheld and
the day they reached the tax office. Switzerland, Italy and Germany have their own module; Luxembourg withholds
nothing, but a holder who left Italy still pays the Italian stamp duty accrued (BOC).
"""
import datetime as dt
from decimal import Decimal as D
from functools import cache
from guard import per_policy
from tax_payouts import payouts
from tax_residence import residence
from tax_collect import collected
from tax_payout_row import row
from tax_gain import gain
import rules
import tax_switzerland
import tax_italy
import tax_germany

COUNTRIES = {'CH': tax_switzerland, 'IT': tax_italy, 'DE': tax_germany}


def untaxed(folder, payout, home):
    """The base of a payout in a country without a tax on it (Luxembourg): rules.py T7_LOSS_BASE, 0 by default as
    in version 22; the signed gain in EUR is the alternative, a submission of its own."""
    return rules.T7_LOSS_BASE(gain(folder, payout, 'EUR'), home.country)


def taxes(folder, payout):
    """(payout, country, taxable base, {tax type: amount}, residence) of one payout, BOC included. The country is
    that of the holder's address as Neuron knew it then; a payout without one (no holder) gets no country."""
    home = residence(folder, payout.policy, payout.date, payout.processed)
    country = COUNTRIES.get(home.country)
    base, amounts = country.payout_tax(folder, payout, home) if country else (untaxed(folder, payout, home), {})
    return payout, home.country, base, {**amounts, 'BOC': collected(folder, payout)}, home


@cache
def payout_details(folder):
    """{(policy, event): taxes} of every payout since 1994; a policy the rules fail on is reported on stderr and
    left out (guard.per_policy) instead of failing the whole task."""
    return per_policy('t7_tax_payout', payouts(folder).items(), lambda pid, items: {
        (pid, p.event): taxes(folder, p) for p in items if p.date >= dt.date(1994, 1, 1)})


def payout_taxes(folder):
    """{(policy, event): (country, taxable base, withholding, surcharges, stamp duty, remittance date)}."""
    return {key: row(*detail) for key, detail in payout_details(folder).items()}
