"""The answers of t7 the leaderboard scored us on (targets_t7/sample_*): exact rows per sample and the misses by group.

Only counts leave this module: no row of a sample is printed or written (the rows stay with the person and Qwen).
A row counts only if every column is exact, as in starter_kit/scoring_t7.py.
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'starter_kit'))
import scoring_t7  # noqa: E402

FOLDER = ROOT / 'targets_t7'
TASKS = ('t7_tax_payout', 't7_tax_annual')
COLUMNS = {'t7_tax_payout': ('country', 'taxable_base', 'withholding', 'surcharges', 'stamp_duty', 'remittance_date'),
           't7_tax_annual': ('STP', 'VST', 'SOS', 'BOL', 'KST', 'SOL', 'KIS')}


def samples(folder=FOLDER):
    """{sample: {task: {key: value}}} of every sample folder (empty without targets_t7)."""
    return {p.name: {t: scoring_t7.read_targets(p, t) for t in TASKS}
            for p in sorted(folder.glob('sample_*')) if (p / f'{TASKS[0]}.csv').exists()}


def score(answers, targets):
    """{sample: (payout right, payout rows, annual right, annual rows)}; `answers` = {task: {key: row}}."""
    out = {}
    for name, tasks in targets.items():
        out[name] = sum((scoring_t7.accuracy(t, answers[t], tasks[t]) for t in TASKS), ())
    return out


def exact(answers, targets):
    """Exact rows of all samples together (payout and annual)."""
    return sum(s[0] + s[2] for s in score(answers, targets).values())


def group(task, key, target):
    """The group of a row: payout by country and with or without tax; annual by the columns that carry an amount."""
    if task == 't7_tax_payout':
        return f"{target[0]} {'taxed' if target[2] or target[3] else 'untaxed'}"
    return 'annual ' + '+'.join(c for c, v in zip(COLUMNS[task], target) if v) if any(target) else 'annual zero'


def misses(answers, targets):
    """{(task, group): Counter} of rows, right rows, missing rows and wrong columns, over all samples."""
    found = {}
    for tasks in targets.values():
        for task in TASKS:
            mine = scoring_t7.normalize(task, answers[task])
            for key, target in tasks[task].items():
                c = found.setdefault((task, group(task, key, target)), Counter())
                c['rows'] += 1
                got = mine.get(key)
                if got is None:
                    c['missing'] += 1
                elif got == target:
                    c['right'] += 1
                else:
                    c.update(col for col, a, b in zip(COLUMNS[task], got, target) if a != b)
    return found


def report(answers, targets):
    """Lines of counts: the score per sample, then the misses per group and column."""
    lines = [f'{name}: payout {s[0]}/{s[1]}, annual {s[2]}/{s[3]}' for name, s in score(answers, targets).items()]
    for (task, name), c in sorted(misses(answers, targets).items()):
        wrong = ', '.join(f'{col} {n}' for col, n in c.items() if col not in ('rows', 'right', 'missing'))
        lines.append(f"{task} {name}: {c['right']}/{c['rows']} right" + (f", {c['missing']} missing" if c['missing'] else '')
                     + (f'; wrong: {wrong}' if wrong else ''))
    return lines


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'my_solution'))
    import submission
    legacy = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / 'legacy')
    print('\n'.join(report({t: getattr(submission, t)(legacy) for t in TASKS}, samples())))
