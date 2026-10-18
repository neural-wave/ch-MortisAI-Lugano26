"""The payment history a premium schedule continues (t1): the NRPREM items due up to the extract date.

(items, extract date) -> sorted due dates: every item due, paid or not, or only the paid ones (state P).
An item that was not paid still keeps its place in the schedule if Neuron counts all of them; the train
due dates cannot tell the two apart (rules.py notes the tie).

Which policies have a premium schedule: the regular frequencies and the state on the extract date (task t1).

How a premium schedule continues: where it counts from, and the next due date after a month step.

The origin, (past due dates, start date) -> date, is the last past due date or the start date itself.
A step, (date, months, anchor day) -> date, moves by the months of the frequency to the anchor day; when the
month is too short, the date is clamped to its last day (the 31st becomes the 28th, then the 31st again),
rolled over into the next month, or the schedule keeps the shorter day from then on (drifting).
"""
from tables import day
import datetime as dt
from conventions_dates import add_months


def all_items_due(premiums, extract_date):
    """The due dates of every item due up to the extract date, paid or not."""
    return sorted(day(r['PR_DUEDT']) for r in premiums if day(r['PR_DUEDT']) <= extract_date)


def paid_items_due(premiums, extract_date):
    """The due dates of the paid items (state P) due up to the extract date."""
    return sorted(day(r['PR_DUEDT']) for r in premiums if r['PR_STATE'] == 'P' and day(r['PR_DUEDT']) <= extract_date)


PAST_DUE = {'all items due': all_items_due, 'paid items due': paid_items_due}


# PH_FREQ -> months between premiums (NRCODE domain FREQ); E (single premium) has no schedule.
FREQUENCY = {'M': 1, 'Q': 3, 'H': 6, 'J': 12}


def premium_paying(policy):
    """PH_STATE 10 (in force, premium paying) with a regular frequency.

    Paid-up (20), premium holiday (30), surrendered (60) and death claim (70) policies get no dates.
    """
    return policy and policy['PH_STATE'] == '10' and policy['PH_FREQ'] in FREQUENCY


def from_last_due_date(past, start):
    """The schedule continues from its last past due date (from the start without one)."""
    return past[-1] if past else start


def from_start_date(past, start):
    """The schedule is counted again from the start date."""
    return start


def clamped_step(date, months, anchor):
    """`months` later on the anchor day, clamped to the month end of a short month."""
    return add_months(date, months, anchor)


def rolled_step(date, months, anchor):
    """`months` later on the anchor day; a day after the month end runs on into the next month."""
    first = add_months(date.replace(day=1), months)
    return first + dt.timedelta(days=anchor - 1)


def drifting_step(date, months, anchor):
    """`months` later on the day of `date`: once clamped to a short month, the schedule keeps that day."""
    return add_months(date, months)


ORIGINS = {'last due date': from_last_due_date, 'start date': from_start_date}
STEPS = {'clamped to the month end': clamped_step, 'rolled into the next month': rolled_step,
         'drifting to the shorter day': drifting_step}
