"""How a monthly charge is split over the (fund, pot) slots of a policy (t3): who takes the rounding rest.

Each slot gets its pro rata piece of the charge, rounded to the cent. The rest (the charge less the rounded
pieces) goes to the largest slot (ties: the first in key order) but never makes it negative, or goes to it
even if negative, or to the first slot, or nobody takes it. Found (rules.py, T3_SPLIT_REST): the largest slot,
never negative; a full replay of all train policies shows it: a negative rest misses 3 of the 1,077,102
charge totals (a risk charge of 0.05 over seven slots is booked as six pieces of 0.01, step 2).
"""


def _pieces(total, values, rounding, date):
    whole = sum(values.values())
    return {k: rounding(total * v / whole, date) for k, v in values.items()}


def largest_never_negative(total, values, rounding, date):
    """The largest slot takes the rest, but books no negative piece."""
    pieces, largest = _pieces(total, values, rounding, date), max(sorted(values), key=values.get)
    pieces[largest] = max(0, total - sum(p for k, p in pieces.items() if k != largest))
    return pieces


def largest_takes_the_rest(total, values, rounding, date):
    """The largest slot takes the rest, even a negative one."""
    pieces, largest = _pieces(total, values, rounding, date), max(sorted(values), key=values.get)
    pieces[largest] = total - sum(p for k, p in pieces.items() if k != largest)
    return pieces


def first_takes_the_rest(total, values, rounding, date):
    """The first slot in key order takes the rest."""
    pieces, first = _pieces(total, values, rounding, date), min(values)
    pieces[first] = total - sum(p for k, p in pieces.items() if k != first)
    return pieces


def no_rest(total, values, rounding, date):
    """Each slot keeps its rounded piece."""
    return _pieces(total, values, rounding, date)


SPLIT_RESTS = {'the largest slot, never negative': largest_never_negative, 'the largest slot': largest_takes_the_rest,
               'the first slot': first_takes_the_rest, 'nobody': no_rest}
