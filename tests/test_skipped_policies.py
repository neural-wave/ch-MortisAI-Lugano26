"""A policy that breaks a rule is skipped and reported; every other value of the task stays as it was.

    .venv/bin/python tests/test_skipped_policies.py      # about 30 s, needs legacy/

Builds two small copies of the export in a temporary folder (the big tables are symbolic links): `clean`
with ten policies, and `broken` with the same policies, two of them damaged the way unseen data could be.
Policy A has no main risk in NRRISK (a KeyError in t0, t2, t3 and t4), policy B has an impossible maturity
date (a ValueError in t1, t2, t3 and t4). Every task must still return the values of the other policies,
unchanged, and name the skipped policies on stderr.
"""
import contextlib
import datetime as dt
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / 'legacy'
sys.path.insert(0, str(ROOT / 'my_solution'))
import submission  # noqa: E402
from tables import grouped, version  # noqa: E402
from conventions_steps import premium_paying  # noqa: E402

EXTRACT = dt.date(2026, 6, 30)
DATES = [dt.date(2006, 12, 31), dt.date(2020, 4, 30), dt.date(2025, 12, 31)]
LOOPED = ('NRPOLH', 'NRPREM')  # the tables the tasks loop over; the others are only looked up by policy
IMPOSSIBLE = '1261399'  # month 13
TASKS = {
    't0_commission': submission.t0_commission,
    't1_next_due_dates': lambda folder: submission.t1_next_due_dates(folder, EXTRACT),
    't2_projected_maturity_value': submission.t2_projected_maturity_value,
    't3_surrender_value': lambda folder: submission.t3_surrender_value(folder, DATES),
    't4_annual_statement': submission.t4_annual_statement,
}
FAILED = []


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def chosen_policies(count=10):
    """Policy B pays premiums on the extract date (so it has t1 rows); A is the first other policy."""
    policies = grouped(str(LEGACY), 'NRPOLH', 'PH_POLNR')
    paying = next(pid for pid, history in policies.items() if premium_paying(version(history, EXTRACT, 'PH')))
    others = [pid for pid in policies if pid != paying][:count - 1]
    return others[0], paying, {paying, *others}


def copy(folder, keep, damage=lambda name, header, fields: fields):
    """The export with only the policies `keep` in the looped tables, and every row passed through `damage`."""
    folder.mkdir()
    for path in sorted(LEGACY.glob('*.csv')):
        if path.stem not in (*LOOPED, 'NRRISK'):
            (folder / path.name).symlink_to(path)
            continue
        lines = path.read_text(encoding='utf-8').splitlines()
        header, rows = lines[0].split(';'), [line.split(';') for line in lines[1:]]
        rows = [damage(path.stem, header, r) for r in rows if path.stem == 'NRRISK' or r[0].strip() in keep]
        text = '\n'.join(';'.join(r) for r in [header] + [r for r in rows if r]) + '\n'
        (folder / path.name).write_text(text, encoding='utf-8')
    return str(folder)


def damaged(a, b):
    """A loses its main risk; B gets a maturity date that does not exist."""
    def damage(name, header, fields):
        if name == 'NRRISK' and fields[0].strip() == a:
            return None
        if name == 'NRPOLH' and fields[0].strip() == b:
            fields = list(fields)
            fields[header.index('PH_ENDDT')] = IMPOSSIBLE
        return fields
    return damage


def policy_of(key):
    return key[0] if isinstance(key, tuple) else key


def test_tasks_skip_damaged_policies():
    a, b, keep = chosen_policies()
    skipped = {'t0_commission': {a}, 't1_next_due_dates': {b}}
    with tempfile.TemporaryDirectory() as tmp:
        clean = copy(Path(tmp) / 'clean', keep)
        broken = copy(Path(tmp) / 'broken', keep, damaged(a, b))
        stderr = io.StringIO()  # one log for the whole run: t4 reuses the replay of t3, which named the skips
        for task, calculate in TASKS.items():
            expected, lost = calculate(clean), skipped.get(task, {a, b})
            check(f'{task}: the clean copy has values of the damaged policies',
                  lost <= {policy_of(k) for k in expected}, True)
            try:
                with contextlib.redirect_stderr(stderr):
                    got = calculate(broken)
            except Exception as error:  # the behaviour under test: one policy must not stop the task
                FAILED.append(f'{task}: the whole task failed on one damaged policy ({type(error).__name__}: {error})')
                continue
            check(f'{task}: values of the other policies unchanged', got,
                  {k: v for k, v in expected.items() if policy_of(k) not in lost})
            named = {p for p in lost if f'skipped policy {p}' in stderr.getvalue()}
            check(f'{task}: skipped policies named on stderr', named, lost)


if __name__ == '__main__':
    test_tasks_skip_damaged_policies()
    print('\n'.join(FAILED) if FAILED else 'all robustness tests passed')
    sys.exit(1 if FAILED else 0)
