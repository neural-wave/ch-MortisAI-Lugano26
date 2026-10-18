"""When a target value counts as overwritten by hand (t5).

Calling a task entry point the way the challenge calls it, so t5 compares like with like.
"""
from decimal import Decimal


def overwritten(predicted, target):
    """True if a calculated value and its target differ by at least one unit (any column of a row).

    Manual corrections are round amounts; cents point to a rounding rule (3 t4 train rows, left unflagged).
    A key the rules do not produce is not reported: without a calculated value there is no evidence.
    One changed column flags a whole t4 (policy, year) row. Dates and other non-amounts must match exactly."""
    if predicted is None:
        return False
    if isinstance(target, tuple):
        return any(overwritten(p, t) for p, t in zip(predicted, target))
    if isinstance(target, Decimal):
        return abs(Decimal(predicted) - target) >= 1
    return predicted != target


def predict(task, calculate, legacy_dir, targets, extract_date):
    """The rule result for one target file: {key: value} from its submission entry point.

    t3 and t1 take one extra argument. t3 is valued only on the valuation dates the target file
    asks for (second key column); t1 projects the year after the extract date of the legacy files.
    t0, t2 and t4 need nothing but legacy_dir.
    """
    if task == 't3_surrender_value':
        return calculate(legacy_dir, sorted({date for _, date in targets}))
    if task == 't1_next_due_dates':
        return calculate(legacy_dir, extract_date)
    return calculate(legacy_dir)
