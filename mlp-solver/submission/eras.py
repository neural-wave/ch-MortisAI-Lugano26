"""The two systems behind Neuron: the COBOL system until ERA_CUTOFF, Neuron NG from then on.

Each system rounds and counts ages in its own way; autosolve found the cut-off and the pair of rules of each
in the data and wrote them to rules.py (ERA_CUTOFF, ERA_ROUNDING, ERA_AGE). Which day decides the era is a rule
of each calculation too (ERA_DATE of the offer, T0_ERA_DATE, T3_*_ERA_DATE), found by autosolve among the dates
of the calculation: the application, money, trade, charge or valuation date.
"""
from collections import Counter
from functools import cache
import rules
from tables import CENT, matching, day
from conventions_birth import completed_years  # noqa: F401 (re-exported: an era-independent date rule)
from rules import ERA_CUTOFF, ERA_ROUNDING, ERA_AGE, ERA_DATE, BIRTH_DATE as birth_date  # noqa: F401 (re-exported)

FOUND = ERA_CUTOFF  # the cut-off autosolve found on the extract of the challenge


@cache
def conversion_day(folder):
    """The first day of Neuron NG in this extract: the day of its events 800, system conversion (NREVNT: all 946 of
    the challenge's extract on 2007-08-11, where autosolve found the cut-off); without them the cut-off found."""
    days = Counter(day(r['EV_EFFDT']) for r in matching(folder, 'NREVNT', 'EV_EVTTP', {'800'}))
    return days.most_common(1)[0][0] if days else FOUND


def adopt(folder):
    """Calculate the extract in `folder` with its own cut-off (rules.ERA_CUTOFF), so another client converted on
    another day is split right without a new search."""
    rules.ERA_CUTOFF = conversion_day(folder)


def by_era(pair, date):
    """The rule of `pair` (COBOL, Neuron NG) for the system live on `date`."""
    return pair[1] if date >= rules.ERA_CUTOFF else pair[0]


def rounded(value, date, places=CENT):
    """Round like the system live on `date` (ERA_ROUNDING), to the cent or to `places`."""
    return by_era(ERA_ROUNDING, date)(value, date, places)


def entry_age(birth, start, day):
    """Age at the start date by the age rule of the system live on `day` (ERA_AGE, on the ERA_DATE of the offer)."""
    return by_era(ERA_AGE, day)(birth, start)
