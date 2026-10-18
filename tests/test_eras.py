"""The cut-off between the COBOL system and Neuron NG comes from the extract itself: the day of its events 800
(system conversion), else the value autosolve found (rules.py ERA_CUTOFF).   .venv/bin/python tests/test_eras.py"""
import datetime as dt
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'my_solution'))
import rules  # noqa: E402
import eras  # noqa: E402

from decimal import Decimal as D  # noqa: E402

FAILED = []


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def extract(events):
    """A folder with an NREVNT of (event type, CYYMMDD day) rows."""
    folder = tempfile.mkdtemp()
    rows = ['EV_POLNR;EV_EVTNR;EV_EVTTP;EV_EFFDT'] + [f'P{i};{i};{kind};{day}' for i, (kind, day) in enumerate(events)]
    Path(folder, 'NREVNT.csv').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return folder


def main():
    found = rules.ERA_CUTOFF
    later = extract([('800', '1100301')] * 3 + [('800', '1100302'), ('110', '1050101')])
    eras.adopt(later)
    check('the day of the events 800', rules.ERA_CUTOFF, dt.date(2010, 3, 1))
    check('the era follows it', eras.rounded(D('1.005'), dt.date(2009, 1, 1)), D('1.00'))
    eras.adopt(extract([('110', '1050101')]))
    check('no events 800: the value autosolve found', rules.ERA_CUTOFF, found)
    eras.adopt(str(ROOT / 'legacy'))
    check('the extract of the challenge: unchanged', rules.ERA_CUTOFF, found)
    print('\n'.join(FAILED) if FAILED else 'all era tests passed')
    sys.exit(1 if FAILED else 0)


if __name__ == '__main__':
    main()
