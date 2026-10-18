"""How Neuron continues a regular premium schedule and collects it: the choices of rules.py (T1_*).

The past due dates of the history, the anchor day and the origin of the schedule, the month step at a short
month and the shift to the collection day were all found by the rule search on the train due dates.
"""
from tables import day
from conventions_dates import add_months
from conventions_steps import FREQUENCY
from rules import T1_PAST_DUE, T1_ANCHOR_DAY, T1_ORIGIN, T1_STEP, T1_COLLECTION_BY, T1_COLLECTION


def upcoming(policy, premiums, extract_date):
    """Due dates after the extract date up to one year later, strictly before maturity PH_ENDDT."""
    past, start, end = T1_PAST_DUE(premiums, extract_date), day(policy['PH_BEGDT']), day(policy['PH_ENDDT'])
    months, anchor, date = FREQUENCY[policy['PH_FREQ']], T1_ANCHOR_DAY(past, start), T1_ORIGIN(past, start)
    while date <= add_months(extract_date, 12):
        if extract_date < date < end:
            yield date
        date = T1_STEP(date, months, anchor)


def collection(policy, date):
    """Collection day: the shift found for the policy's value of T1_COLLECTION_BY (PH_PAYMT)."""
    return T1_COLLECTION[policy[T1_COLLECTION_BY]](date)
