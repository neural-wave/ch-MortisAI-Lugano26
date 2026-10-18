"""The admin fee of a month (t3): at most the policy value, or always in full. No train policy is charged down to
zero by it, so the two agree (rules.py notes the tie, T3_ADMIN_CAP); at most the value is the rule of the
offer as well, where no charge takes the value below zero.

The NRCHRG row a monthly charge takes (t3): the one valid on the charge date or on the application date.
The fund accounting charges by the tariff of the day (rules.py, T3_TARIFF_DAY), unlike the offer of t2,
which keeps the tariff of its application date. Found on the ADM, AMC and RSK bookings of 3 % of the train policies, every charge day on its own (37,143 rows), and the options tied there were replayed on all train policies (1,077,102 charge totals).

The age a risk charge of the fund accounting reads the death probability at (t3): the entry age plus the
completed policy years (it grows on the policy anniversary, as in the offer of t2), or the insured person's
own age on the day of the charge. Found: the policy anniversary (rules.py, T3_CHARGE_AGE). Found on the ADM, AMC and RSK bookings of 3 % of the train policies, every charge day on its own (37,143 rows), and the options tied there were replayed on all train policies (1,077,102 charge totals).
"""
from conventions_birth import completed_years


def at_most_the_value(fee, value):
    """The admin fee takes the value down to zero at most."""
    return min(value, fee)


def the_full_fee(fee, value):
    """The admin fee is taken in full."""
    return fee


ADMIN_CAPS = {'at most the value': at_most_the_value, 'the full fee': the_full_fee}


def on_the_charge_date(ledger, date):
    """The tariff of the day of the charge."""
    return date


def on_the_application_date(ledger, date):
    """The tariff of the day the offer was signed."""
    return ledger.applied


TARIFF_DAYS = {'charge date': on_the_charge_date, 'application date': on_the_application_date}


def at_the_last_anniversary(ledger, date):
    """The entry age plus the completed policy years."""
    return ledger.age + completed_years(ledger.start, date)


def own_age_on_the_day(ledger, date):
    """The insured person's age on the day, by the age rule of the offer's era."""
    return ledger.age_rule(ledger.birth, date)


CHARGE_AGES = {'entry age + completed policy years': at_the_last_anniversary, "the insured's own age": own_age_on_the_day}
