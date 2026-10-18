"""A new target from a JSON spec, without writing Python: rows, joins, holes and the formula are declared.

    python3 vocabulary/run.py --spec vocabulary/specs/t0_commission.json

A spec names
- the target file and its key and value columns,
- the rows: an anchor table of the export, the target file itself ("target:<file>") or any CSV
  ("csv:<path>"), a filter and the key of each row (matched to the target keys),
- joins to other tables, by equal columns; a versioned table (with ..._VLDFR / ..._VLDTO) is joined
  as of a date, and that date may itself be a hole ("hole:<name>"),
- the holes: a brick family of the dictionary ("ROUNDINGS", "AGES", "SHIFTS", "DAY_COUNTS", "GROWTH",
  or the generated "ROUNDINGS_ANY" / "OFFSETS_ANY"), candidate expressions ({"label": "expression"}),
  or a constant fitted from the data ({"fit": "ratio", "of": "<input expression>"}),
- the formula, one expression over the row's columns, the holes and a few helpers.

Expressions are Python expressions over the column names (PR_AMTRC, RK_TARKEY[5], ...) and the helpers
date(cyymmdd), iso(text), num(value, decimals), D, int, str, min, max, abs, len. The spec is written by
the team, not taken from the data, so evaluating it is safe here.

A join without a matching row adds no columns: a formula that needs them counts that row as a miss,
and a feature that needs them is None for that row (the diagnosis can still split on it).
A fitted hole reads its input from the first value of the join holes.
"""
import csv
import datetime as dt
import json
import zlib
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
import bricks
from engine import is_holdout, Fit

FAMILIES = {name: getattr(bricks, name) for name in ('ROUNDINGS', 'AGES', 'SHIFTS', 'DAY_COUNTS', 'GROWTH')}
FAMILIES.update({'ROUNDINGS_ANY': bricks.roundings_any(), 'OFFSETS_ANY': bricks.offsets_any()})
OPEN = {0: dt.date.min, 9999999: dt.date.max}


def date(value):
    """Legacy date CYYMMDD -> date (0 = none, 9999999 = open end)."""
    n = int(value)
    return OPEN[n] if n in OPEN else dt.date(1900 + n // 10000, n // 100 % 100, n % 100)


def feature(code, namespace):
    """A feature of a row, or None when its input is missing (e.g. no matching row in a join)."""
    try:
        return evaluate(code, namespace)
    except (NameError, KeyError, IndexError, TypeError, ValueError, ArithmeticError):
        return None


HELPERS = {'date': date, 'iso': dt.date.fromisoformat, 'num': lambda v, s=0: D(v) / 10 ** int(s),
           'D': D, 'int': int, 'str': str, 'min': min, 'max': max, 'abs': abs, 'len': len}
TYPES = {'decimal': D, 'date': dt.date.fromisoformat, 'int': int, 'str': str}


def compile_expr(text):
    """A spec expression, compiled once."""
    return compile(text, f'<spec: {text}>', 'eval')


def evaluate(code, namespace):
    """The value of a compiled expression over a row, with the helpers and no other builtins."""
    return eval(code, {'__builtins__': {}, **HELPERS}, namespace)  # noqa: S307 (the team's own spec)


def read_rows(source, legacy, targets=None):
    """Rows of a legacy table (';', trimmed), of the target file ('target:<file>') or of a CSV ('csv:<path>')."""
    if source.startswith(('csv:', 'target:')):
        path = source[4:] if source.startswith('csv:') else Path(targets) / f'{source[7:]}.csv'
        with open(path, encoding='utf-8') as f:
            return [{k: (v or '').strip() for k, v in r.items()} for r in csv.DictReader(f)]
    with open(Path(legacy) / f'{source}.csv', encoding='utf-8') as f:
        return [{k: (v or '').strip() for k, v in r.items()} for r in csv.DictReader(f, delimiter=';')]


class Join:
    """One join: rows of `table` whose `on` columns equal expressions over the row; versioned as of a date."""

    def __init__(self, spec, legacy):
        rows = read_rows(spec['table'], legacy)
        if 'where' in spec:
            where = compile_expr(spec['where'])
            rows = [r for r in rows if evaluate(where, r)]
        self.columns = list(spec['on'])
        self.values = [compile_expr(e) for e in spec['on'].values()]
        self.as_of = spec.get('as_of')
        self.index = defaultdict(list)
        for r in rows:
            self.index[tuple(r[c] for c in self.columns)].append(r)
        prefix = next(iter(rows[0])).split('_')[0] if rows else ''
        self.period = (f'{prefix}_VLDFR', f'{prefix}_VLDTO') if rows and f'{prefix}_VLDFR' in rows[0] else None
        self.order = f'{prefix}_VRSNR'

    def lookup(self, namespace, when):
        """The matching row (the version valid on `when`, highest version number), or None."""
        found = self.index.get(tuple(str(evaluate(v, namespace)) for v in self.values), [])
        if self.period and when is not None:
            found = [r for r in found if date(r[self.period[0]]) <= when <= date(r[self.period[1]])]
        return max(found, key=lambda r: int(r.get(self.order, 0) or 0), default=None)


def build(spec_path, legacy, targets):
    """rows, slots, formula for the engine, from a spec file."""
    spec = json.loads(Path(spec_path).read_text(encoding='utf-8'))
    target = spec['target']
    convert = TYPES[target.get('type', 'decimal')]
    with open(Path(targets) / f"{target['file']}.csv", encoding='utf-8') as f:
        expected = {tuple(r[k] for k in target['keys']): convert(r[target['value']]) for r in csv.DictReader(f)}
    slots, expression_holes = {}, {}
    for name, hole in spec['holes'].items():
        if isinstance(hole, str):  # a whole family of the dictionary
            slots[name] = FAMILIES[hole]
        elif 'family' in hole:  # part of a family: {"family": "ROUNDINGS", "only": ["half up", "truncate"]}
            slots[name] = {k: FAMILIES[hole['family']][k] for k in hole['only']}
        elif 'fit' in hole:  # an unknown constant fitted from the data: {"fit": "ratio", "of": "<input expression>"}
            of = compile_expr(hole['of'])
            slots[name] = Fit(lambda row, of=of: evaluate(of, next(iter(row['spaces'].values()))))
        else:  # candidate expressions
            expression_holes[name] = {label: compile_expr(e) for label, e in hole.items()}
            slots[name] = {label: label for label in hole}
    joins = [Join(j, legacy) for j in spec['rows'].get('join', [])]
    source = spec['rows']['from']
    where = compile_expr(spec['rows']['where']) if 'where' in spec['rows'] else None
    keys = [compile_expr(k) for k in spec['rows']['key']]
    group = compile_expr(spec['rows'].get('group', spec['rows']['key'][0]))
    features = {n: compile_expr(e) for n, e in spec.get('features', {}).items()}
    formula_code = compile_expr(spec['formula'])
    join_holes = sorted({j.as_of[5:] for j in joins if j.as_of and j.as_of.startswith('hole:')})
    variants = [{}]
    for h in join_holes:
        variants = [{**v, h: label} for v in variants for label in expression_holes[h]]
    sample = spec.get('sample')  # percent of the policies, to keep a large target quick
    rows = []
    for anchor in read_rows(source, legacy, targets):
        if where and not evaluate(where, anchor):
            continue
        key = tuple(str(evaluate(k, anchor)) for k in keys)
        if key not in expected or (sample and zlib.crc32(str(evaluate(group, anchor)).encode()) % 100 >= sample):
            continue
        spaces = {}
        for variant in variants:  # one namespace per value of the holes that decide a join
            ns = dict(anchor)
            for j in joins:
                when = None
                if j.as_of:
                    hole = j.as_of[5:] if j.as_of.startswith('hole:') else None
                    when = evaluate(expression_holes[hole][variant[hole]] if hole else compile_expr(j.as_of), ns)
                match = j.lookup(ns, when)
                ns.update(match or {})
            spaces[tuple(variant.get(h) for h in join_holes)] = ns
        base = next(iter(spaces.values()))
        rows.append({'policy': str(evaluate(group, base)), 'key': key, 'holdout': is_holdout(str(evaluate(group, base))),
                     'target': expected[key], 'spaces': spaces, 'join_holes': join_holes,
                     'features': {n: feature(c, base) for n, c in features.items()}})

    def formula(row, choice):
        """The spec formula with the chosen bricks, on the namespace of the chosen join variant."""
        ns = dict(row['spaces'][tuple(choice[h] for h in row['join_holes'])])
        for name, options in expression_holes.items():
            ns[name] = evaluate(options[choice[name]], ns)
        for name in slots:
            if name not in expression_holes:
                ns[name] = choice[name]
        return evaluate(formula_code, ns)

    return (rows, slots, formula, spec.get('name', Path(spec_path).stem), spec.get('description', ''),
            spec.get('nrexcp'), spec.get('depth', 2))
