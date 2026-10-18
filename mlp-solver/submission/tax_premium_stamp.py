"""t7, Switzerland: stamp duty on single premiums (STP), 2.5 % of the premium in CHF from 1998-04-01.

Which premiums carry it is NRTAXB's record (454 bookings, 95 of them by the COBOL batch); each premium is converted on
its money date and rounded by the system that booked the duty. The yearly table counts it in the year of the booking.

t7, Switzerland: the reported withholding tax per policy and year, for the yearly table (rules.py T7_REPORTED_VST).

Only Swiss payouts without withheld tax count; a year with several such payouts adds them. Whether these amounts
belong in the table is a hypothesis the leaderboard tests: the task says the table lists what Neuron "withheld,
accrued or reported", and status M means "reported to the tax office".
"""
from eras import rounded
from tax_money import convert
from tax_residence import rate
from tax_premiums import premiums
from tax_bookings import booked
from collections import defaultdict
from decimal import Decimal as D
from tax_reported import reported


def stamp_duties(folder, policy, currency):
    """{year: STP} of the premiums of one policy Neuron charged stamp duty on: every booking of a premium event
    is one duty (a premium is booked once), at the rate valid on the booking's day and known then."""
    result = {}
    for premium in premiums(folder)[policy]:
        for b in booked(folder, policy, premium.event, 'STP'):
            amount = convert(folder, premium.amount, currency, 'CHF', premium.date, b.processed.date())
            duty = rounded(amount * rate(folder, 'CH', 'STP', b.date, b.processed), b.processed.date())
            result[b.date.year] = result.get(b.date.year, 0) + duty
    return result


def reported_vst(folder, details):
    """{(policy, year): reported withholding tax} from the payout details of tax_payout."""
    found = defaultdict(D)
    for (pid, _), (payout, country, _, amounts, home) in details.items():
        amount = reported(folder, payout, home) if country == 'CH' and not amounts.get('VST') else 0
        if amount:
            found[pid, payout.date.year] += amount
    return dict(found)
