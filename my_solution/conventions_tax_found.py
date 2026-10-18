"""t7: the rules found on the two released t7 samples, each as a switch of rules.py with the variant it replaced.

Every function gets plain values (amounts, days, or a function to call), so rules.py can import this module before
any tax module. The default of each switch is the rule found; the other value is the build before it, so the
search can try both (vocabulary/t7_targets.py scores them on the samples).
"""
from decimal import Decimal as D, ROUND_DOWN


# Italian substitute tax (rules.py T7_SOS): of the gain, each rate on its period, or the rate of the payout day.
def by_rate_periods(periods, payout_day):
    """Each rate on the part of the gain of its period (tax_italy_periods)."""
    return periods()


def at_the_rate_of_the_payout_day(periods, payout_day):
    """The whole gain at the rate of the payout day."""
    return payout_day()


# Earlier payouts in the periods (rules.py T7_SOS_EARLIER): (premiums they paid back by then, share left).
def open_premiums_and_share_left(paid_back, left):
    """A period counts the premiums still open and keeps what earlier withdrawals left of it."""
    return paid_back, left


def all_premiums_whole_period(paid_back, left):
    """A period counts every premium received and all of its gain."""
    return D(0), D(1)


# Year of a payout's tax in the yearly table (rules.py T7_ANNUAL_YEAR).
def in_the_remittance_year(payout_day, remittance_day):
    """The year the tax reached the tax office (a December payout counts in January)."""
    return remittance_day.year


def in_the_payout_year(payout_day, remittance_day):
    """The year of the payout."""
    return payout_day.year


# Amount the Italian stamp duty at a payout is taken on (rules.py T7_BOL_PAYOUT_AMOUNT).
def before_the_penalty(net, gross):
    """What the payout paid before the surrender penalty."""
    return gross


def after_the_penalty(net, gross):
    """What the payout paid after the surrender penalty."""
    return net


# German solidarity surcharge and church tax (rules.py T7_SURCHARGE_ROUNDING).
def cut_to_the_cent(amount, round_by_era):
    """Cut to the cent in every era."""
    return D(amount).quantize(D('0.01'), ROUND_DOWN)


def by_the_system(amount, round_by_era):
    """Rounded like the other taxes, by the system of the payout's day."""
    return round_by_era(amount)


# Day whose system rounds a premium converted into the tax currency (rules.py T7_PREMIUM_ROUNDING).
def on_the_premium_day(premium_day, payout_day):
    """The premium's own money date (COBOL truncated before 2007-08-11)."""
    return premium_day


def on_the_payout_day(premium_day, payout_day):
    """The payout's day."""
    return payout_day


# The 2019 correction of the Italian stamp duty (rules.py T7_BOL_CORRECTION). `rows` holds per duty booked before
# the run (recalculated exactly, booked, base times the raise of the rate); `round` rounds by the run's system.
def the_rate_raise_rounded_once(fixes, rows, round):
    """The base times the raise of the rate, summed and rounded once on the first correction row."""
    return first_row(fixes, round(sum((raised for _, _, raised in rows), D(0))))


def recalculated_rounded_once(fixes, rows, round):
    """The recalculated duties less those booked, summed and rounded once on the first correction row."""
    return first_row(fixes, round(sum((new - booked for new, booked, _ in rows), D(0))))


def recalculated_duty_by_duty(fixes, rows, round):
    """Each duty recalculated and rounded less the booked one: the non-zero differences one per correction row,
    the rest on the last row."""
    found = [d for d in (round(new) - booked for new, booked, _ in rows) if d]
    amounts = (found + [D('0.00')] * len(fixes))[:len(fixes)]
    amounts[-1] += sum(found[len(fixes):], D('0.00'))
    return list(zip(fixes, amounts))


def first_row(fixes, amount):
    """The amount on the first correction row, nothing on the others."""
    return [(fixes[0], amount)] + [(fix, D('0.00')) for fix in fixes[1:]]


# The families autosolve chooses from (vocabulary/cases/t7_tax.py), the variant of the build before first.
SOS_RULES = {'the rate of the payout day': at_the_rate_of_the_payout_day, 'each rate on the gain of its period': by_rate_periods}
SOS_EARLIER = {'all premiums, the whole period': all_premiums_whole_period,
               'open premiums, the share left': open_premiums_and_share_left}
ANNUAL_YEARS = {'the payout year': in_the_payout_year, 'the remittance year': in_the_remittance_year}
BOL_PAYOUT_AMOUNTS = {'after the penalty': after_the_penalty, 'before the penalty': before_the_penalty}
SURCHARGE_ROUNDINGS = {'by the system': by_the_system, 'cut to the cent': cut_to_the_cent}
PREMIUM_ROUNDINGS = {'on the payout day': on_the_payout_day, 'on the premium day': on_the_premium_day}
BOL_CORRECTIONS = {'recalculated, duty by duty': recalculated_duty_by_duty,
                   'recalculated, rounded once': recalculated_rounded_once,
                   'the rate raise, rounded once': the_rate_raise_rounded_once}
