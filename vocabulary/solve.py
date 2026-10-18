"""How autosolve turns a search into rules: ties, the principle that settles them, eras and splits.

- A tie: several options of a hole match exactly as many rows as the winner. The train data cannot tell them
  apart, so a principle chooses: first the option consistent with the same era in the other calculations
  (or a preference the case states with its reason), else the simplest (the earliest of its family).
  Every such choice is reported as "not distinguishable on train".
- An era: rows before and after the cut-off are searched apart; an era hole gets a pair (COBOL, Neuron NG).
- A cut-off found by the diagnosis lies somewhere in a gap of the data; it is moved onto a landmark of the
  export inside that gap: a day on which one kind of event happened to many policies at once.
- A split on a column (e.g. the payment method) gives a rule per value of that column.
"""
import csv
import datetime as dt
from collections import defaultdict
from pathlib import Path
from engine import search, diagnose, expand, score

LANDMARK_EVENTS = 10
STUCK = 0.99  # a coordinate search below this share of exact search rows also tries two holes at a time  # an event type counts as a one-day landmark if at least this many events share its only day


def ranked(rows, formula, slots):
    """All combinations, best first, with the families expanded."""
    return search(rows, formula, slots, top=0), expand(rows, slots)


def ties(results):
    """{hole: [labels]} of the options that reach the best number of exact rows (in the order of the family)."""
    best = results[0]['hits']
    tied = defaultdict(list)
    for result in results:
        if result['hits'] == best:
            for hole, label in result['choice'].items():
                if label not in tied[hole]:
                    tied[hole].append(label)
    return tied


def choose(hole, labels, family, preferred=None):
    """(label, reason) for a hole whose tied options are `labels`; reason is '' when there is no tie."""
    labels = sorted(labels, key=list(family).index)
    if len(labels) == 1:
        return labels[0], ''
    if preferred and preferred[0] in labels:
        return preferred[0], f'{preferred[1]}'
    return labels[0], 'the simplest'


def landmarks(legacy):
    """Days on which one kind of event happened to many policies and never on another day (NREVNT)."""
    days, counts = defaultdict(set), defaultdict(int)
    with open(Path(legacy) / 'NREVNT.csv', encoding='utf-8') as handle:
        for row in csv.DictReader(handle, delimiter=';'):
            days[row['EV_EVTTP']].add(row['EV_EFFDT'])
            counts[row['EV_EVTTP']] += 1
    from tables import day
    return {day(next(iter(d))): kind for kind, d in days.items() if len(d) == 1 and counts[kind] >= LANDMARK_EVENTS}


def cut(rows, results):
    """(feature, cut date, last value below it) of the diagnosis of the best rule, or None if no date splits it.
    The era is a date: if another column splits the misses first (a client whose other conventions differ too),
    the diagnosis looks at the date columns alone."""
    where = diagnose(rows, results[0]['ok'])
    if not where or ' < ' not in where['test']:
        dated = [{**r, 'features': {k: v for k, v in r['features'].items() if isinstance(v, dt.date)}} for r in rows]
        where = diagnose(dated, results[0]['ok'])
    if not where or ' < ' not in where['test']:
        return None
    feature, value = where['test'].split(' < ')
    when = dt.date.fromisoformat(value)
    below = max(r['features'][feature] for r in rows if r['features'][feature] < when)
    return feature, when, below


def snap(when, below, marks):
    """The landmark inside the gap (below, when], else the cut itself: (date, landmark kind or None)."""
    inside = sorted(day for day in marks if below < day <= when)
    return (inside[0], marks[inside[0]]) if len(inside) == 1 else (when, None)


def single_moves(families, labels):
    """Every other option of one hole, the rest fixed."""
    return [{**labels, hole: label} for hole, family in families.items() for label in family if label != labels[hole]]


def pair_moves(families, labels):
    """Every other combination of two holes, the rest fixed: the way out when two holes only work together
    (e.g. two dates that both have no policy version on the simplest option)."""
    holes = list(families)
    return [{**labels, a: x, b: y} for i, a in enumerate(holes) for b in holes[i + 1:]
            for x in families[a] for y in families[b] if (x, y) != (labels[a], labels[b])]


def descend(rows, formula, slots, passes=8):
    """A coordinate search for cases with too many holes to try every combination.

    Start from the simplest option of every hole; try each other option of one hole with the rest fixed and
    keep it if it explains more search rows; when no single change helps and the rule is still far from exact
    (STUCK), try two holes together; repeat until nothing changes. Returns the labels, their (search, held-out) exact rows, the evaluations made, and per
    hole the options that score exactly the same.
    """
    families = expand(rows, slots)
    labels = {hole: next(iter(family)) for hole, family in families.items()}

    def scored(trial):
        hits, _ = score(rows, formula, {hole: families[hole][label] for hole, label in trial.items()})
        return hits['train'], hits['test']
    best, evaluations = scored(labels), 1
    search_rows = sum(1 for r in rows if not r['holdout'])
    for _ in range(passes):
        changed = False
        stuck = best[0] < STUCK * search_rows  # far from any rule: two holes may only work together
        for moves in (single_moves(families, labels), pair_moves(families, labels) if stuck else []):
            for trial in moves:  # one hole at a time; two at a time only when no single move helps
                hits = scored(trial)
                evaluations += 1
                if hits[0] > best[0]:
                    labels, best, changed = trial, hits, True
            if changed:
                break
        if not changed:
            break
    tied = {hole: [label for label in family if label == labels[hole] or scored({**labels, hole: label}) == best]
            for hole, family in families.items()}
    return labels, best, evaluations, tied, families
