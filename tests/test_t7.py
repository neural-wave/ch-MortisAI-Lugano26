"""Tests of t7 (The Tax Audit) on the extract:  .venv/bin/python tests/test_t7.py

The task shows one row of each table; both must come out to the cent and the day. Every payout since 1994 must get a
row (a payout without tax too: country, base, zeros, no date), and no policy may be skipped.
"""
import datetime as dt
import sys
from contextlib import redirect_stderr
from decimal import Decimal as D
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'my_solution'))
sys.path.insert(0, str(ROOT / 'starter_kit'))
import submission  # noqa: E402
import scoring_t7  # noqa: E402  (the official scoring of t7)
from tax_payouts import payouts  # noqa: E402
import rules  # noqa: E402

LEGACY = str(ROOT / 'legacy')
FAILED = []


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def main():
    errors = StringIO()
    with redirect_stderr(errors):
        payout, annual = submission.t7_tax_payout(LEGACY), submission.t7_tax_annual(LEGACY)
    check('the payout example of the task', payout.get(('BL10000086', 121)),
          ('DE', D('5628.16'), D('1407.04'), D('77.38'), D('0.00'), dt.date(2006, 8, 10)))
    check('the yearly example of the task', annual.get(('BL10000044', 2019)), (D(0),) * 3 + (D('616.11'),) + (D(0),) * 3)
    every = {(pid, p.event) for pid, items in payouts(LEGACY).items() for p in items if p.date >= dt.date(1994, 1, 1)}
    check('a row for every payout since 1994', set(payout), every)
    check('no policy skipped', errors.getvalue(), '')
    check('a date exactly when a tax was withheld (stamp duty alone as rules.py T7_BOC_DATED)',
          [k for k, v in payout.items() if (v[5] not in (None, '')) != bool(any(v[2:4]) or rules.T7_BOC_DATED(v[4]))], [])
    official(payout, annual)
    print('\n'.join(FAILED) if FAILED else 'all t7 tests passed')
    sys.exit(1 if FAILED else 0)


def official(payout, annual):
    """What the official scoring reads: every row passes scoring_t7.normalize (6 values a payout, 7 a year), no amount
    has a fraction of a cent (an exact comparison never matches it), and both rows of the task count through
    scoring_t7.accuracy (a target file of the two rows, written to a temporary folder, never into git)."""
    import tempfile
    for task, rows in (('t7_tax_payout', payout), ('t7_tax_annual', annual)):
        check(f'{task}: every row passes normalize', len(scoring_t7.normalize(task, rows)), len(rows))
        cents = [k for k, v in rows.items() for x in v if isinstance(x, D) and x != x.quantize(D('0.01'))]
        check(f'{task}: no amount with a fraction of a cent', len(cents), 0)
    with tempfile.TemporaryDirectory() as folder:
        Path(folder, 't7_tax_payout.csv').write_text(
            'policy_id,event_nr,country,taxable_base,withholding,surcharges,stamp_duty,remittance_date\n'
            'BL10000086,121,DE,5628.16,1407.04,77.38,0.00,2006-08-10\n')
        Path(folder, 't7_tax_annual.csv').write_text(
            'policy_id,year,ch_stp,ch_vst,it_sos,it_bol,de_kst,de_sol,de_kis\n'
            'BL10000044,2019,0.00,0.00,0.00,616.11,0.00,0.00,0.00\n')
        for task, rows in (('t7_tax_payout', payout), ('t7_tax_annual', annual)):
            check(f'{task}: the example of the task counts', scoring_t7.accuracy(task, rows, scoring_t7.read_targets(folder, task)), (1, 1))


if __name__ == '__main__':
    main()
