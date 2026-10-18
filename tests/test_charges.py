"""Unit tests of the charge split, no data needed:  .venv/bin/python tests/test_charges.py

The split gives each (fund, pot) slot its pro rata piece rounded to the cent, and the largest slot the rest.
Neuron never books a negative piece: when the rounded pieces of the other slots already exceed the charge,
the largest slot books nothing (found on t3_booking: a risk charge of 0.05 over seven slots was booked as
six pieces of 0.01).
"""
import datetime as dt
import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'my_solution'))
from conventions_rest import largest_never_negative  # noqa: E402
from conventions_rounding import half_up  # noqa: E402


def split(total, values, date):
    return largest_never_negative(total, values, half_up, date)

NG = dt.date(2012, 11, 30)  # Neuron NG rounds half up
FAILED = []


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def test_largest_slot_takes_the_rest():
    values = {('F1', '1'): D('100'), ('F2', '1'): D('200'), ('F3', '2'): D('700')}
    pieces = split(D('10.01'), values, NG)
    check('pieces', pieces, {('F1', '1'): D('1.00'), ('F2', '1'): D('2.00'), ('F3', '2'): D('7.01')})


def test_no_negative_piece():
    values = {(f'F{i}', '1'): D('1') for i in range(6)} | {('BIG', '1'): D('3')}
    pieces = split(D('0.05'), values, NG)
    check('largest slot books nothing', pieces[('BIG', '1')], D('0.00'))
    check('other slots keep their rounded piece', sorted(set(p for k, p in pieces.items() if k[0] != 'BIG')), [D('0.01')])


if __name__ == '__main__':
    test_largest_slot_takes_the_rest()
    test_no_negative_piece()
    print('\n'.join(FAILED) if FAILED else 'all charge tests passed')
    sys.exit(1 if FAILED else 0)
