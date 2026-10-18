"""Ablation: the t1 schedule without the anchor day Neuron uses (the highest day of the last 12 due dates).

The dictionary keeps the day of the start, of the last due date, the highest day ever and the most common recent
day. Schedules that drifted from the 31st to the 28th in the COBOL years, and month ends, are then missed; the
engine should say so and, with a model connected, take a proposed anchor day only if it raises the exact rows.
"""
from cases import t1_schedule
from conventions import ANCHOR_DAYS

REMOVED = 'highest day of the last 12 due dates'


def build(legacy, targets):
    rows, slots, formula = t1_schedule.build(legacy, targets)
    return rows, {**slots, 'anchor day': {k: v for k, v in ANCHOR_DAYS.items() if k != REMOVED}}, formula
