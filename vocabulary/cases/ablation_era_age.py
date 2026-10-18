"""Ablation: the era case without the age rule of the COBOL system (days since birth / 365, rounded).

The diagnosis still finds the application date of 2007-08-11 (a landmark: the day of all events 800); the
offers before it then miss with every remaining age rule. With a model connected, a proposed age brick is
kept only if it raises the exact rows of the held-out policies.
"""
from cases import era
from conventions import AGES

REMOVED = 'days / 365'


def build(legacy, targets):
    rows, slots, formula = era.build(legacy, targets)
    return rows, {**slots, 'entry age': {k: v for k, v in AGES.items() if k != REMOVED}}, formula
