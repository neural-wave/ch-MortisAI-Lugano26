"""The search: fill the holes of a formula with every combination of bricks and keep what matches exactly.

A case gives rows (one per target value), the holes (slots) with their candidate bricks, and a
formula(row, choice) -> value. The engine
1. fits the holes whose candidates come from the data (Fit: an unknown constant such as a rate),
2. tries every combination on the search policies and scores exact matches,
3. prefers the simpler combination when two score the same (earlier options = simpler),
4. checks the winner on held-out policies it never saw,
5. if the winner is not perfect, lets a small decision tree say where it fails,
   splits the rows there and searches each part again,
6. if a part still is not explained, writes what is left (the candidates for manual corrections, t5)
   and a prompt for a language model; with a proposer (llm.py) it tries the proposed bricks and keeps
   one only if it raises the exact matches on the held-out policies,
7. writes everything to a journal for the report.
"""
import ast
import builtins
import datetime as dt
import itertools
import json
import signal
import time
import zlib
from collections import Counter, defaultdict
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
from types import SimpleNamespace

EXACT = 0.999  # a part counts as explained from this share of exact rows on
MIN_PART = 20  # a split is tried only if both sides have at least this many rows
MISSED_EXAMPLES = 20  # missed rows shown in a prompt


def is_holdout(group, share=0.2):
    """Stable 20 % split by policy (the same policy is never on both sides)."""
    return zlib.crc32(f'holdout/{group}'.encode()) % 100 < share * 100  # salted: independent of sampling


class Fit:
    """A hole whose candidates are fitted on the search rows: constants c with target = c x input.

    For every search row the ratio target / input is taken, rounded to 2 .. 6 decimals; the most
    frequent values become the candidates (fewer decimals first). A rounding in the formula is still
    searched, so the constant is checked exactly, not approximately.
    """

    def __init__(self, input_of, places=range(2, 7), top=3):
        self.input_of, self.places, self.top = input_of, places, top

    def candidates(self, rows):
        found = {}
        ratios = []
        for row in rows:
            try:
                value = self.input_of(row)
                if value and not row['holdout']:
                    ratios.append(D(row['target']) / D(value))
            except Exception:
                continue
        for places in self.places:
            for value, _ in Counter(r.quantize(D(1).scaleb(-places)) for r in ratios).most_common(self.top):
                found.setdefault(f'fitted {value.normalize()}', value)
        return found


def expand(rows, slots):
    """Slots with the fitted holes replaced by their candidates."""
    return {name: (hole.candidates(rows) if isinstance(hole, Fit) else hole) for name, hole in slots.items()}


def score(rows, formula, choice):
    """(hits on search rows, search rows, hits on held-out rows, held-out rows), plus the per-row result."""
    hits, ok = Counter(), bytearray()  # one byte per row: 1 exact, 0 missed
    for row in rows:
        try:
            good = formula(row, choice) == row['target']
        except Exception:  # a brick that does not apply counts as a miss, and is counted
            good = False
            hits['errors'] += 1
        side = 'test' if row['holdout'] else 'train'
        hits[side] += good
        hits[side + '_n'] += 1
        ok.append(good)
    return hits, ok


def search(rows, formula, slots, top=5):
    """Rank all combinations; returns a list of dicts, best first."""
    slots = expand(rows, slots)
    names = list(slots)
    results = []
    for combo in itertools.product(*(list(enumerate(slots[n].items())) for n in names)):
        choice = {n: fn for n, (_, (_, fn)) in zip(names, combo)}
        hits, ok = score(rows, formula, choice)
        results.append({'choice': {n: label for n, (_, (label, _)) in zip(names, combo)}, 'functions': choice,
                        'complexity': sum(i for i, _ in combo),
                        'train': hits['train'] / max(1, hits['train_n']),
                        'test': hits['test'] / max(1, hits['test_n']),
                        'hits': (hits['train'], hits['test']),
                        'n': hits['train_n'] + hits['test_n'], 'errors': hits['errors'], 'ok': ok})
    results.sort(key=lambda r: (-r['train'], r['complexity']))
    return results[:top] if top else results


def gini(bad, n):
    """Gini impurity of a set with `bad` misses out of `n`."""
    p = bad / n if n else 0
    return 2 * p * (1 - p)


def candidate_splits(rows, feature):
    """Possible tests on one feature: a threshold for numbers and dates, equality for anything else.

    A value that is missing on some rows (None) makes the feature a category, so a missing input
    never stops the diagnosis; "feature == None" is then a test like any other.
    """
    values = [r['features'][feature] for r in rows]
    ordered = all(isinstance(v, (int, D, dt.date)) and not isinstance(v, bool) for v in values)
    if not ordered:
        return [(f'{feature} == {v!r}', lambda r, v=v: r['features'][feature] == v) for v, _ in Counter(values).most_common(8)]
    cuts = sorted(set(values))
    step = max(1, len(cuts) // 2000)  # every distinct value on small sets, so a cut date is found exactly
    return [(f'{feature} < {c}', lambda r, c=c: r['features'][feature] < c) for c in cuts[::step][1:]]


def best_split(rows, ok):
    """The test that best separates matches from misses (largest Gini gain)."""
    n, bad = len(rows), sum(not x for x in ok)
    best = None
    for feature in rows[0]['features']:
        for label, test in candidate_splits(rows, feature):
            side = [test(r) for r in rows]
            n_a = sum(side)
            if not 0 < n_a < n:
                continue
            bad_a = sum(1 for x, s in zip(ok, side) if s and not x)
            n_b, bad_b = n - n_a, bad - bad_a
            impurity = (n_a * gini(bad_a, n_a) + n_b * gini(bad_b, n_b)) / n
            gain = gini(bad, n) - impurity
            if best is None or gain > best[0]:
                best = (gain, label, test, bad_a / n_a, bad_b / n_b, n_a, n_b)
    return best


def diagnose(rows, ok):
    """Where the rule fails: the best split as a sentence, or None if the misses look like noise."""
    split = best_split(rows, ok)
    if split is None or split[0] < 1e-4:
        return None
    gain, label, test, miss_yes, miss_no, n_yes, n_no = split
    return {'test': label, 'miss_if_true': round(miss_yes, 4), 'miss_if_false': round(miss_no, 4),
            'n_true': n_yes, 'n_false': n_no, 'split': test}


class Journal:
    """Every search, written as JSON lines and summarised in Markdown."""

    def __init__(self, path):
        self.path, self.entries = path, []
        open(path, 'w', encoding='utf-8').close()

    def add(self, case, step, results, note='', **extra):
        entry = {'case': case, 'step': step, 'note': note, 'time': time.strftime('%H:%M:%S'),
                 'tried': [{k: v for k, v in r.items() if k not in ('ok', 'functions')} for r in results], **extra}
        self.entries.append(entry)
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, default=str) + '\n')


def predicted(formula, row, functions):
    """The value of the formula for a row, or the error as text."""
    try:
        return formula(row, functions)
    except Exception as error:  # shown in the report of what is left
        return f'error: {error}'


def plain(value):
    """Readable text of a value for a prompt: dates as 2027-03-30, no datetime/Decimal reprs."""
    if isinstance(value, dict):
        return '{' + ', '.join(f'{k}: {plain(v)}' for k, v in value.items()) + '}'
    if isinstance(value, (tuple, list)):
        return '(' + ', '.join(plain(v) for v in value) + ')'
    return str(value)


def example_calls(rows, formula, functions, hole, k=3):
    """Real calls of the bricks of `hole` on some rows: [(args, result)], so a model sees the signature."""
    original, seen = functions.get(hole), []
    if not callable(original):
        return seen

    def spy(*args):
        result = original(*args)
        seen.append((args, result))
        return result
    for row in rows:
        if len(seen) >= k:
            break
        try:
            formula(row, {**functions, hole: spy})
        except Exception:
            continue
    return seen[:k]


def near_hits(rows, ok, days=7, limit=MISSED_EXAMPLES):
    """Exact rows whose date features lie within `days` of a missed row: what a proposed brick must not break."""
    missed = {v for r, good in zip(rows, ok) if not good for v in r['features'].values() if isinstance(v, dt.date)}
    near = [r for r, good in zip(rows, ok) if good and any(isinstance(v, dt.date) and any(
        abs((v - m).days) <= days for m in missed) for v in r['features'].values())]
    return near[:limit]


def llm_prompt(case, label, best, rows, slots, formula, context=''):
    """What a language model needs to propose a new brick: the rule, where it fails, examples, the holes."""
    missed_rows = [r for r, good in zip(rows, best['ok']) if not good]
    missed = Counter(f"- {plain(r['features'])} expected {plain(r['target'])} calculated "
                     f"{plain(predicted(formula, r, best['functions']))}" for r in missed_rows)
    lines = [f'# Rule search stalled: {case} / {label}', '', *([context.strip(), ''] if context else []),
             f"Best rule: {best['choice']} - {100 * best['train']:.3f} % exact on the search rows, "
             f"{100 * best['test']:.3f} % on held-out policies.", '',
             'Holes and the bricks already tried:']
    lines += [f'- {name}: {", ".join(list(options)[:40])}' for name, options in slots.items()]
    lines += ['', f'Rows the best rule gets wrong ({len(missed_rows)} rows; features, expected, calculated; '
                  f'the {MISSED_EXAMPLES} most frequent cases):']
    lines += [line + (f'  (x{count})' if count > 1 else '') for line, count in missed.most_common(MISSED_EXAMPLES)]
    lines += ['', 'Rows the best rule gets right close to the missed ones (by date); a new brick must keep them:']
    lines += [f"- {plain(r['features'])} expected {plain(r['target'])}" for r in near_hits(rows, best['ok'])]
    lines += ['', 'How the bricks of each hole are called (real calls of the best rule on missed rows):']
    for hole in slots:
        for args, result in example_calls(missed_rows or rows, formula, best['functions'], hole):
            lines.append(f"- {hole}({', '.join(map(repr, args))}) -> {result!r}")
    lines += ['', 'The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the',
              'current best brick of the hole (the one called above) and can be called inside your brick.',
              '', 'Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines',
              '`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment',
              '`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime',
              'module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP',
              'and plain Python. Write a general business rule: no policy numbers and no lists of the',
              'expected values above. A brick is kept only if it raises the exact matches on held-out policies.']
    return '\n'.join(lines)


DATETIME = SimpleNamespace(date=dt.date, timedelta=dt.timedelta, datetime=dt.datetime)  # not the module itself
SANDBOX = {'D': D, 'dt': DATETIME, 'datetime': DATETIME, 'date': dt.date, 'timedelta': dt.timedelta,
           'ROUND_HALF_UP': ROUND_HALF_UP, 'ROUND_HALF_EVEN': ROUND_HALF_EVEN, 'ROUND_HALF_DOWN': ROUND_HALF_DOWN,
           'ROUND_DOWN': ROUND_DOWN, 'ROUND_UP': ROUND_UP}
SAFE_BUILTINS = {name: getattr(builtins, name)
                 for name in ('abs', 'all', 'any', 'bool', 'dict', 'divmod', 'enumerate', 'float', 'int', 'isinstance',
                              'len', 'list', 'max', 'min', 'range', 'reversed', 'round', 'set', 'sorted', 'str',
                              'sum', 'tuple', 'zip', 'ValueError', 'TypeError', 'ArithmeticError')}
PROPOSAL_SECONDS = 20  # a proposal that needs longer on a sample of rows is dropped (e.g. an endless loop)


# Attributes that lead from plain values to frames, code, globals or formatting tricks; together with every attribute
# starting with an underscore, a brick may not use them.
BLOCKED = {'format', 'format_map', 'mro', 'gi_frame', 'gi_code', 'gi_yieldfrom', 'cr_frame', 'cr_code', 'cr_await',
           'ag_frame', 'ag_code', 'f_back', 'f_globals', 'f_locals', 'f_builtins', 'f_code', 'tb_frame', 'tb_next',
           'co_code', 'func_globals'}
DATES = {'date', 'timedelta', 'datetime'}  # the only attributes of `dt` a brick may use


def checked(source):
    """The source if its syntax stays inside the sandbox, else ValueError: no import; no attribute that starts with
    an underscore or is in BLOCKED; no dunder name; no text that contains a dunder; of `dt` only date, timedelta and
    datetime. A filter of the syntax is no security boundary against hostile code (that needs a separate process);
    it keeps the model the team runs itself from leaving the restricted builtins by accident."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError('a brick may not import')
        if isinstance(node, ast.Attribute) and (node.attr.startswith('_') or node.attr in BLOCKED or (
                isinstance(node.value, ast.Name) and node.value.id in ('dt', 'datetime') and node.attr not in DATES)):
            raise ValueError(f'a brick may not use the attribute {node.attr!r}')
        name = getattr(node, 'id', None) or getattr(node, 'arg', None) or getattr(node, 'name', None)
        text = node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else ''
        if (isinstance(name, str) and name.startswith('__')) or '__' in text:
            raise ValueError(f'a brick may not use {name or text!r}')
    return source


def compile_brick(source, best=None):
    """A proposed brick from its source, with only Decimal, datetime and safe builtins in reach (no import).

    The syntax is checked first (checked: no import, nothing starting with an underscore), then the code runs
    with restricted builtins. This keeps an honest model from reaching files or the network; for hostile
    code a separate process would be the boundary, so only a model the team runs itself should be connected.
    """
    space = {'__builtins__': SAFE_BUILTINS, **SANDBOX, 'best': best}
    source = checked(source)
    exec(source, space)  # noqa: S102 (proposals are checked on held-out data before they are used)
    return space['brick']


class TimeLimit:
    """Stop a block after `seconds` (Unix; elsewhere no limit)."""

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        if hasattr(signal, 'SIGALRM'):
            self.previous = signal.signal(signal.SIGALRM, self.stop)
            signal.alarm(self.seconds)

    def __exit__(self, *exc):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            signal.signal(signal.SIGALRM, self.previous)

    @staticmethod
    def stop(*_):
        raise TimeoutError('too slow')


def runs_in_time(rows, formula, functions, hole, brick, sample=200):
    """True if the brick evaluates a sample of rows within PROPOSAL_SECONDS (errors are allowed, hangs are not)."""
    try:
        with TimeLimit(PROPOSAL_SECONDS):
            score(rows[:sample], formula, {**functions, hole: brick})
        return True
    except TimeoutError:
        return False


def discover(case, rows, formula, slots, journal, depth=2, label='all rows', context='', plausible=None):
    """Search, check, and if needed split where the rule fails and search each part (piecewise rule).

    Returns the parts top-down: the part itself, then its sub-parts. Only the parts marked `leaf`
    are the final rule; the others show how the engine got there. With `plausible` (test text -> bool), a split
    it rejects (e.g. a date that is no business event) is not made: the part stays whole and notes it as deferred,
    so a language model can be asked about the whole part first (discover_with_proposals).
    """
    results = search(rows, formula, slots, top=0)
    best = results[0]
    journal.add(case, label, results[:8], note=f'{len(rows)} rows, {len(results)} combinations')
    part = {'segment': label, 'rule': best['choice'], 'train': best['train'], 'test': best['test'], 'n': best['n']}
    where = diagnose(rows, best['ok']) if depth > 0 and best['train'] < 1 else None
    if where and plausible and not plausible(where['test']):
        part['deferred'], where = where['test'], None
    if where and min(where['n_true'], where['n_false']) >= MIN_PART:
        inside = [r for r in rows if where['split'](r)]
        outside = [r for r in rows if not where['split'](r)]
        children = discover(case, inside, formula, slots, journal, depth - 1, f"{label} / {where['test']}", context, plausible)
        children += discover(case, outside, formula, slots, journal, depth - 1, f"{label} / not {where['test']}", context,
                             plausible)
        if any(c['rule'] != best['choice'] for c in children if c.get('leaf')):  # the split changes the rule: keep it
            part['fails_where'] = {k: v for k, v in where.items() if k != 'split'}
            return [part] + children
        # the same rule on both sides: the split explained nothing, the misses are noise (t5) or a missing brick
    leaf(part, case, rows, formula, slots, best, context)
    return [part]


def leaf(part, case, rows, formula, slots, best, context=''):
    """Mark a final part, keep the rows its rule does not explain (candidates for t5) and,
    if the part is not explained, the prompt for a language model."""
    part.update(leaf=True, rows=rows, best=best)
    part['unexplained'] = [(r, predicted(formula, r, best['functions'])) for r, good in zip(rows, best['ok']) if not good]
    part['prompt'] = (llm_prompt(case, part['segment'], best, rows, expand(rows, slots), formula, context)
                      if best['train'] < EXACT else None)


def with_learned(slots, learned):
    """The slots plus the proposed bricks kept so far (learned: {hole: {label: brick}})."""
    return {hole: ({**options, **learned[hole]} if learned.get(hole) else options) for hole, options in slots.items()}


def exact_rows(report):
    """(exact search rows, exact held-out rows) of the final rule: the sum over its leaves."""
    leaves = [p['best']['hits'] for p in report if p.get('leaf')]
    return sum(a for a, _ in leaves), sum(b for _, b in leaves)


def proposed_bricks(case, part, formula, slots, hole, proposer, journal):
    """The proposer's bricks for one hole of an unexplained part, compiled and timed: {label: brick}, {label: source}."""
    best, rows = part['best'], part['rows']
    bricks, sources = {}, {}
    for name, source in (proposer(part['prompt'], hole) or {}).items():
        try:
            brick = compile_brick(source, best['functions'][hole])
        except Exception as error:
            journal.add(case, f"{part['segment']} / proposal rejected", [], note=f'{name}: does not compile: {error}')
            continue
        if not runs_in_time(rows, formula, best['functions'], hole, brick):
            journal.add(case, f"{part['segment']} / proposal rejected", [], note=f'{name}: too slow')
            continue
        tag = f'proposed: {name}' + (f" (extends: {best['choice'][hole]})" if 'best(' in source else '')
        bricks[tag], sources[tag] = brick, (source, best['functions'][hole])
    return bricks, sources


def discover_with_proposals(case, rows, formula, slots, journal, depth=2, context='', proposer=None, plausible=None):
    """discover(), then ask the proposer about every part that stays unexplained.

    For each such part and each hole that takes code, the proposed bricks join the dictionary of
    this case and the whole search runs again. They are kept only if the final rule of the case is
    never worse and better somewhere: more exact rows on the held-out policies, or, if those are
    all exact already, on the search policies. A wrong brick therefore cannot cost a single row.
    With `plausible`, splits it rejects wait until the proposer was asked about the whole part; a part that
    stays unexplained afterwards is split after all (the last discover).
    """
    report = discover(case, rows, formula, slots, journal, depth, context=context, plausible=plausible)
    learned, asked, kept_sources = {}, set(), {}
    while proposer is not None:
        open_parts = [p for p in report if p.get('leaf') and p['prompt'] and p['segment'] not in asked]
        if not open_parts:
            break
        part = max(open_parts, key=lambda p: p['n'] * (1 - p['train']))  # the part with the most missed rows first
        asked.add(part['segment'])
        for hole in slots:
            if not callable(part['best']['functions'][hole]):  # fitted constants and expression holes take no code
                continue
            bricks, sources = proposed_bricks(case, part, formula, slots, hole, proposer, journal)
            if not bricks:
                continue
            trial = {**learned, hole: {**learned.get(hole, {}), **bricks}}
            new = discover(case, rows, formula, with_learned(slots, trial), journal, depth, context=context, plausible=plausible)
            before, after = exact_rows(report), exact_rows(new)
            kept = after[1] >= before[1] and after[0] >= before[0] and (after[1], after[0]) > (before[1], before[0])
            used = sorted({p['rule'][hole] for p in new if p.get('leaf')} & set(bricks)) if kept else []
            journal.add(case, f"{part['segment']} / proposals for {hole}", [], accepted=used,
                        proposals={tag: source for tag, (source, _) in sources.items()},
                        note=f"{'kept' if kept else 'rejected'}: exact rows (search, held out) {before} -> {after}")
            if kept:
                learned, report = trial, new
                kept_sources.update({(hole, tag): (sources[tag], f'{before} -> {after}') for tag in used})
                break
    if any(p.get('deferred') and p['train'] < 1 for p in report if p.get('leaf')):  # still needed: split after all
        report = discover(case, rows, formula, with_learned(slots, learned), journal, depth, context=context)
    report[0]['learned'] = kept_sources  # {(hole, tag): ((source, the brick it extends), exact rows before -> after)}
    return report


def by_group(rows, ok, key):
    """Share of exact matches per value of `key` (e.g. application year) - shows change points."""
    tally = defaultdict(lambda: [0, 0])
    for row, good in zip(rows, ok):
        tally[key(row)][0] += good
        tally[key(row)][1] += 1
    return {k: round(a / b, 4) for k, (a, b) in sorted(tally.items())}
