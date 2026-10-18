"""Writing my_solution/rules.py from the choices of the search: plain assignments, the evidence as comments.

The text depends only on the choices and their evidence (no date of the run, no timing), so two runs on the
same data give the same bytes. A value is a brick (a named function of a my_solution/conventions_*.py module), a date,
a text (a column name), a pair (COBOL, Neuron NG) or a split {value of a column: brick}.
"""
import datetime as dt
import textwrap
from typing import NamedTuple

HEADER = '''"""Rules of Neuron found by autosolve.py: generated, do not edit by hand (run `python3 autosolve.py`).

Each choice was picked by an exact-match search over the families of conventions.py: every combination
is scored by the rows it matches to the cent or the day, the simplest of the best wins, and 20 % of the
policies are held out of the search to check the winner. A pair is (COBOL system, Neuron NG): the era
of the calculation decides. "Not distinguishable on train" marks a choice the train rows cannot make;
it follows the rule of the same era in the other calculations, else the simplest option, and may matter
on unseen policies.
"""'''


class Section(NamedTuple):
    """The rules of one target: a title, comment lines with the evidence, (constant, value, note) triples."""
    title: str
    notes: list
    assignments: list


def code(value):
    """The Python literal of a value of rules.py."""
    if isinstance(value, dt.date):
        return f'date({value.year}, {value.month}, {value.day})'
    if isinstance(value, tuple):
        return '(' + ', '.join(map(code, value)) + ')'
    if isinstance(value, dict):
        return '{' + ', '.join(f'{key!r}: {code(v)}' for key, v in value.items()) + '}'
    return repr(value) if isinstance(value, str) else value.__name__


def bricks(value):
    """The conventions functions inside a value, as (module, name) pairs."""
    if isinstance(value, (tuple, dict)):
        return set().union(*map(bricks, value.values() if isinstance(value, dict) else value))
    return set() if isinstance(value, (str, dt.date)) else {(value.__module__, value.__name__)}


def imports(pairs):
    """One `from <module> import ...` per conventions module, wrapped in parentheses when the line gets long."""
    lines = []
    for module in sorted({module for module, _ in pairs}):
        names = ', '.join(sorted(name for m, name in pairs if m == module))
        line = f'from {module} import {names}'
        lines += [line] if len(line) <= 110 else [f'from {module} import (', *textwrap.wrap(
            names + ',', 106, initial_indent='    ', subsequent_indent='    ', break_on_hyphens=False), ')']
    return lines


def rules_text(sections):
    """The whole rules.py: header, imports, one block per section."""
    values = [value for s in sections for _, value, _ in s.assignments]
    dates = ['from datetime import date'] if any(isinstance(v, dt.date) for v in values) else []
    lines = [HEADER, *dates, *imports(set().union(*map(bricks, values)))]
    for section in sections:
        lines += ['', f'# {section.title}', *(f'# {note}' for note in section.notes)]
        lines += [f'{name} = {code(value)}' + (f'  # {note}' if note else '') for name, value, note in section.assignments]
    return '\n'.join(lines) + '\n'
