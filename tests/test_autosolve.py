"""Tests of the rules.py generator, no data needed:  .venv/bin/python tests/test_autosolve.py

The generator turns the choices of the search into my_solution/rules.py: plain assignments of the
conventions.py functions, with the evidence as comments. It must be deterministic (the same choices give
the same bytes), readable, and valid Python that imports only conventions.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'vocabulary'), str(ROOT / 'my_solution'), str(ROOT)]
from emit import Section, rules_text  # noqa: E402
from solve import choose, snap, ties  # noqa: E402
import datetime as dt  # noqa: E402
from conventions_rounding import half_up, truncate  # noqa: E402
from conventions_dates import money_date  # noqa: E402
from conventions_calendar import same_day, next_business_day_ticino  # noqa: E402

FAILED = []


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def t0_section():
    return Section('t0 commission', ['225,858 rows; 28 combinations of date (4) x rounding (7).'],
                   [('T0_DATE', money_date, 'the policy version and the rate are taken on this date'),
                    ('T0_ROUNDING', half_up, '')])


def test_rules_text():
    text = rules_text([t0_section()])
    check('deterministic', rules_text([t0_section()]), text)
    check('imports each brick from its module', ('from conventions_dates import money_date' in text, 'from conventions_rounding import half_up' in text), (True, True))
    check('assignment with its note', 'T0_DATE = money_date  # the policy version and the rate are taken on this date' in text, True)
    check('assignment without a note', '\nT0_ROUNDING = half_up\n' in text, True)
    check('evidence as a comment', '# 225,858 rows; 28 combinations of date (4) x rounding (7).' in text, True)
    space = {}
    exec(compile(text, 'rules.py', 'exec'), space)  # noqa: S102 (our own generated text)
    check('valid Python, the names are the functions', (space['T0_DATE'], space['T0_ROUNDING']), (money_date, half_up))


def test_values_of_every_shape():
    """A date, a pair (COBOL, Neuron NG), a split by a column and its text become plain Python literals."""
    section = Section('era and t1', [], [('ERA_CUTOFF', dt.date(2007, 8, 11), ''), ('T0_ROUNDING', (truncate, half_up), ''),
                                         ('T1_COLLECTION_BY', 'PH_PAYMT', ''),
                                         ('T1_COLLECTION', {'LS': next_business_day_ticino, 'UB': same_day}, '')])
    text = rules_text([section])
    check('date', 'ERA_CUTOFF = date(2007, 8, 11)' in text, True)
    check('pair', 'T0_ROUNDING = (truncate, half_up)' in text, True)
    check('text', "T1_COLLECTION_BY = 'PH_PAYMT'" in text, True)
    check('split', "T1_COLLECTION = {'LS': next_business_day_ticino, 'UB': same_day}" in text, True)
    check('imports', 'from datetime import date' in text, True)
    space = {}
    exec(compile(text, 'rules.py', 'exec'), space)  # noqa: S102 (our own generated text)
    check('values', (space['ERA_CUTOFF'], space['T0_ROUNDING'], space['T1_COLLECTION']['UB']),
          (dt.date(2007, 8, 11), (truncate, half_up), same_day))


def test_ties_and_the_principle():
    """Options with the best score tie; the stated preference wins a tie, else the earliest of the family."""
    family = {'half up': 1, 'truncate': 2, 'up': 3}
    results = [{'choice': {'rounding': 'half up'}, 'hits': (9, 3)}, {'choice': {'rounding': 'up'}, 'hits': (9, 3)},
               {'choice': {'rounding': 'truncate'}, 'hits': (8, 3)}]
    check('tie', ties(results), {'rounding': ['half up', 'up']})
    check('simplest', choose('rounding', ['up', 'half up'], family), ('half up', 'the simplest'))
    check('preferred', choose('rounding', ['up', 'half up'], family, ('up', 'the era')), ('up', 'the era'))
    check('preference outside the tie', choose('rounding', ['half up', 'up'], family, ('truncate', 'x')), ('half up', 'the simplest'))
    check('no tie', choose('rounding', ['up'], family, ('half up', 'x')), ('up', ''))


def test_cut_moves_onto_a_landmark():
    marks = {dt.date(2007, 8, 11): '800', dt.date(2010, 1, 1): '999'}
    check('landmark in the gap', snap(dt.date(2007, 8, 13), dt.date(2007, 8, 6), marks), (dt.date(2007, 8, 11), '800'))
    check('no landmark', snap(dt.date(2009, 3, 2), dt.date(2009, 2, 27), marks), (dt.date(2009, 3, 2), None))


def test_the_day_of_the_era():
    """The day that puts more rows into the era whose rule fits them wins; a tie goes to the first candidate."""
    from types import SimpleNamespace
    from autosolve import era_date
    cutoff, early, late = dt.date(2007, 8, 11), dt.date(2007, 1, 1), dt.date(2008, 1, 1)
    rows = [{'policy': 'P', 'holdout': False, 'target': 'NG' if b >= cutoff else 'COBOL',
             'features': {'trade date': a, 'application date': b}} for a, b in [(late, early), (late, late), (early, early)]]
    case = SimpleNamespace(ERA_DATES={'trade date': None, 'application date': None}, ERA_RULE='X_ERA_DATE')
    formula = lambda row, c: c['rule']  # noqa: E731
    bricks = [{'rule': 'COBOL'}, {'rule': 'NG'}]
    check('the deciding day wins', era_date(case, rows, formula, bricks, cutoff)[0], 'application date')
    same = [{**r, 'target': 'NG' if r['features']['trade date'] >= cutoff else 'COBOL',
             'features': {**r['features'], 'application date': r['features']['trade date']}} for r in rows]
    label, notes = era_date(case, same, formula, bricks, cutoff)
    check('the same day everywhere: the first candidate, no tie note', (label, len(notes)), ('trade date', 1))
    loose = [{**r, 'target': 'COBOL'} for r in rows[:1]] + [r for r in rows[1:]]
    label, notes = era_date(case, loose, lambda row, c: 'COBOL' if row is loose[0] else c['rule'], bricks, cutoff)
    check('a tie: the first candidate, noted', (label, notes[-1].startswith('Not distinguishable')), ('trade date', True))


def test_structure_never_sees_its_own_answer():
    """A tax booked exactly where a fact holds is found by the tree; a surcharge sees whether its base tax was booked,
    the base tax never sees itself."""
    from types import SimpleNamespace
    from autosolve import structure_section
    from engine import Journal
    rows = [{'policy': f'P{i}', 'key': i, 'holdout': i % 5 == 0, 'booked': {'A', 'B'} if i % 2 else set(),
             'features': {'fact': bool(i % 2), 'noise': i % 3}} for i in range(200)]
    case = SimpleNamespace(__name__='cases.demo', TITLE='demo', STRUCTURE=('A', 'B'), DEPENDS={'B': 'A'})
    slots = {'booked': {'never': lambda r: False, 'always': lambda r: True}}
    section, found = structure_section(case, rows, lambda row, c: c['booked'](row), slots, Journal(Path('/dev/null')))
    a_notes = section.notes[:section.notes.index(next(n for n in section.notes if n.startswith('B:')))]
    check('structure: A split on the fact', [n.split(':')[0].strip() for n in a_notes[1:]], ['fact == False', 'not fact == False'])
    check('structure: agreement', found, {'A': '200/200', 'B': '200/200'})
    check('structure: A never sees "A booked"', any('A booked' in n for n in a_notes), False)


def test_choice_by_evidence():
    """Each level of vocabulary/evidence.py decides in its turn, and samples are never compared with each other."""
    from evidence import decide, scored
    clean = {'checks': '', 'contradictions': 0, 'inconsistent': 0}
    profile = {'x': {**clean, 'checks': 'the example'}, 'y': dict(clean), 'z': {**clean, 'contradictions': 2}}
    check('evidence: (a) drops what breaks a check, (b) keeps fewer contradictions',
          decide('h', ['x', 'y', 'z'], profile, [], 'x')[0], 'y')
    log = [{'sample': 'A', 'payout': [9, 20], 'switches': {'h': 'p'}}, {'sample': 'A', 'payout': [11, 20], 'switches': {'h': 'q'}},
           {'sample': 'B', 'payout': [30, 40], 'switches': {'h': 'p'}}]
    same = {o: dict(clean) for o in 'pqr'}
    check('evidence: (d) the sample that compared the options decides', decide('h', ['p', 'q', 'r'], same, scored(log, 'payout'), 'p')[0], 'q')
    check("evidence: (d') the incumbent when no sample compared", decide('h', ['p', 'r'], same, scored(log, 'payout'), 'r')[0], 'r')
    check('evidence: (e) the first option without anything else', decide('h', ['r', 'p'], same, [], 's')[0], 'r')


if __name__ == '__main__':
    test_choice_by_evidence()
    test_structure_never_sees_its_own_answer()
    test_the_day_of_the_era()
    test_rules_text()
    test_ties_and_the_principle()
    test_cut_moves_onto_a_landmark()
    test_values_of_every_shape()
    print('\n'.join(FAILED) if FAILED else 'all autosolve tests passed')
    sys.exit(1 if FAILED else 0)
