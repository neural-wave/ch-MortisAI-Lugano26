"""t7, Italy: what one stamp duty booking is taken on: a base in EUR and a share of the year (tax_stamp_duty applies
the rate). The yearly duty takes the value on 31 December (the second example of the task: 210,787.23 EUR at 0.20 %
is 421.57), a full year; the duty at a payout takes what it paid before the surrender penalty (a death claim: its
amount) and the share of the year before it (rules.py T7_BOL_SHARE; the released samples). The year-end value converts on 31 December, the payout on its day.
"""
from decimal import Decimal as D
import rules
from tax_money import convert
from tax_premiums import era
from tax_payouts import payouts
from tax_stamp_values import year_end_values


def base(folder, booking, currency):
    """(value in EUR, share of the year) a booking is taken on; nothing for an event that is no payout."""
    if booking.event == 0:
        value = year_end_values(folder).get((booking.policy, booking.date), D('0.00'))
        return convert(folder, value, currency, 'EUR', booking.date, booking.processed.date()), rules.T7_BOL_FIRST_YEAR(folder, booking)
    payout = next((p for p in payouts(folder)[booking.policy] if p.event == booking.event), None)
    if payout is None:
        return D('0.00'), D('0.00')
    paid = rules.T7_BOL_PAYOUT_AMOUNT(payout.amount, payout.amount if payout.kind == 'death' else payout.paid)
    return convert(folder, paid, currency, 'EUR', payout.date, era(payout)), rules.T7_BOL_SHARE(payout.date)
