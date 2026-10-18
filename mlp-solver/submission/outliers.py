"""t5: values that were overwritten by hand follow no rule, so they differ from what the rules calculate.

Method: recalculate every target value with the t0..t4 rules and report the rows where the target
disagrees by a whole unit (outliers_compare). On the train targets this finds 55 rows:
t0 commission 10, t2 projected maturity value 8, t3 surrender value 16, t4 annual statement 21 (none in t1).
"""
from pathlib import Path

from outliers_compare import overwritten
from outliers_compare import predict
from outliers_targets import read_targets

# Per target file: how many leading columns form the key, how many after them are the value.
# t1: (policy_id, n) -> (due_date, collection_date); t4: (policy_id, year) -> six amount columns.
# t3 checks surrender_value only; the policy_value column after it is not part of the t3 result.
COLUMNS = {'t0_commission': (2, 1), 't1_next_due_dates': (2, 2), 't2_projected_maturity_value': (1, 1),
           't3_surrender_value': (2, 1), 't4_annual_statement': (2, 6)}


def outliers(tasks, legacy_dir, targets_dir, extract_date):
    """Every target value that differs from the rules by at least one currency unit or one day.

    tasks maps the target file name to its submission entry point; a missing target file is skipped.
    """
    found = set()
    for task, calculate in tasks.items():
        path = Path(targets_dir) / f'{task}.csv'
        if not path.exists():
            continue
        targets = read_targets(path, *COLUMNS[task])
        predicted = predict(task, calculate, legacy_dir, targets, extract_date)
        found |= {(task, key) for key, value in targets.items() if overwritten(predicted.get(key), value)}
    return found
