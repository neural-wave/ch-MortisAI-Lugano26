"""Self-tests of the rule finder, no data needed:  python3 vocabulary/tests/run_tests.py

1. The bricks give the known answers (Easter, holidays of Ticino, ages, roundings, month ends).
2. Planted rules: synthetic data made with a known rule, including a rule that changes on a
   cut-off date, must be found back exactly by the engine (a red-team test of the search).
3. The JSON spec path: a tiny export, target and spec must give the same planted rule.
4. The edge case: a rule that is NOT in the dictionary (rate 3.7 %, half even to 3 decimals).
   The fixed dictionary must fail honestly (left-over rows and an LLM prompt, no false 100 %);
   the generated families (fitted constant, every precision) must find it; a proposed brick
   (the LLM hook) must be kept when it is right and rejected when it is wrong.
5. A missing input: a feature that is None on some rows must not stop the diagnosis.
6. The LLM path end to end: llm.py talks to a fake OpenAI-compatible server that proposes the
   missing Easter holidays (and one wrong brick); the engine must keep the right one and reach 100 %.
"""
import datetime as dt
import random
import sys
import tempfile
from decimal import Decimal as D, ROUND_HALF_EVEN
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bricks as b  # noqa: E402
from engine import discover, discover_with_proposals, is_holdout, Journal, Fit  # noqa: E402

FAILED = []
TMP = Path(tempfile.mkdtemp())


def check(name, got, expected):
    if got != expected:
        FAILED.append(f'{name}: got {got!r}, expected {expected!r}')


def test_bricks():
    for year, day in [(2000, (4, 23)), (2019, (4, 21)), (2026, (4, 5)), (2027, (3, 28))]:
        check(f'easter {year}', b.easter(year), dt.date(year, *day))
    ticino = b.SHIFTS['next business day (Ticino, with Easter)']
    check('Christmas 2026 (Fri) -> Mon 28', ticino(dt.date(2026, 12, 25)), dt.date(2026, 12, 28))
    check('Sat before Easter Monday 2027 -> Tue 30', ticino(dt.date(2027, 3, 27)), dt.date(2027, 3, 30))
    check('San Giuseppe 2027 (Fri) -> Mon 22', ticino(dt.date(2027, 3, 19)), dt.date(2027, 3, 22))
    check('Ascension 2027 -> Fri 7 May', ticino(dt.date(2027, 5, 6)), dt.date(2027, 5, 7))
    check('plain Tuesday stays', ticino(dt.date(2026, 7, 7)), dt.date(2026, 7, 7))
    check('previous business day', b.SHIFTS['previous business day (Ticino)'](dt.date(2026, 8, 1)), dt.date(2026, 7, 31))
    check('add_months 31 Jan + 1', b.add_months(dt.date(2024, 1, 31), 1), dt.date(2024, 2, 29))
    birth = dt.date(1980, 3, 10)
    check('age last birthday', b.age_last_birthday(birth, dt.date(2020, 3, 9)), 39)
    check('age nearest birthday', b.age_nearest_birthday(birth, dt.date(2020, 1, 1)), 40)
    check('age nearest birthday (early)', b.age_nearest_birthday(birth, dt.date(2019, 9, 1)), 39)
    check('age days/365', b.age_days_365(birth, dt.date(2020, 3, 9)), 40)
    r = b.ROUNDINGS
    check('half up', r['half up'](D('1.005')), D('1.01'))
    check('truncate', r['truncate'](D('1.009')), D('1.00'))
    check('half even', r['half even'](D('1.005')), D('1.00'))
    check('5 Rappen', r['5 Rappen'](D('1.03')), D('1.05'))
    era = r['truncate before 2007-08-11, then half up']
    check('era before', era(D('1.005'), dt.date(2007, 8, 10)), D('1.00'))
    check('era on the day', era(D('1.005'), dt.date(2007, 8, 11)), D('1.01'))


def test_planted_rules():
    """A commission-like target: half up after 2015-06-01, truncate before; the engine must find the cut."""
    random.seed(7)
    rows = []
    for i in range(3000):
        when = dt.date(2010, 1, 1) + dt.timedelta(days=random.randrange(3650))
        amount = D(random.randrange(100, 900000)) / 1000
        mode = b.ROUNDINGS['half up'] if when >= dt.date(2015, 6, 1) else b.ROUNDINGS['truncate']
        pid = f'P{i // 3}'
        rows.append({'policy': pid, 'holdout': is_holdout(pid), 'amount': amount, 'date': when,
                     'target': mode(amount * D('0.035')), 'features': {'date': when, 'kind': random.choice('ab')}})
    slots = {'rate': {'3 %': D('0.03'), '3.5 %': D('0.035'), '4 %': D('0.04')},
             'rounding': {k: b.ROUNDINGS[k] for k in ('half up', 'truncate', 'half even')}}
    formula = lambda row, c: c['rounding'](row['amount'] * c['rate'], row['date'])  # noqa: E731
    report = discover('planted', rows, formula, slots, Journal(TMP / 'planted.jsonl'))
    check('planted: global rate', report[0]['rule']['rate'], '3.5 %')
    check('planted: cut found', report[0].get('fails_where', {}).get('test'), 'date < 2015-06-01')
    check('planted: before the cut', report[1]['rule'], {'rate': '3.5 %', 'rounding': 'truncate'})
    check('planted: after the cut', report[2]['rule'], {'rate': '3.5 %', 'rounding': 'half up'})
    check('planted: segments exact', [round(p['test'], 6) for p in report[1:]], [1.0, 1.0])


def test_spec():
    """A tiny export + target + JSON spec in a temp folder: the spec path must find the planted rule too."""
    import json
    import tempfile
    from spec import build
    folder = Path(tempfile.mkdtemp())
    (folder / 'NRDEMO.csv').write_text('DM_ID;DM_AMT;DM_DATE\n' + ''.join(
        f'X{i};{1000 + 37 * i};{1060101 + (i % 3) * 20000}\n' for i in range(200)))
    with open(folder / 'demo.csv', 'w') as f:
        f.write('id,value\n')
        for i in range(200):
            amount, cobol = D(1000 + 37 * i) / 100, (i % 3) == 0  # 2006 rows truncate, 2008/2010 rows half up
            mode = b.ROUNDINGS['truncate'] if cobol else b.ROUNDINGS['half up']
            f.write(f'X{i},{mode(amount * D("0.035"))}\n')
    spec = {'target': {'file': 'demo', 'keys': ['id'], 'value': 'value'},
            'rows': {'from': 'NRDEMO', 'key': ['DM_ID']},
            'holes': {'rate': {'3 %': 'D("0.03")', '3.5 %': 'D("0.035")'},
                      'rounding': {'family': 'ROUNDINGS', 'only': ['half up', 'truncate', 'truncate before 2007-08-11, then half up']}},
            'formula': 'rounding(num(DM_AMT, 2) * rate, date(DM_DATE))', 'features': {'year': 'date(DM_DATE).year'}}
    (folder / 'demo.json').write_text(json.dumps(spec))
    rows, slots, formula, name, _, _, _ = build(folder / 'demo.json', folder, folder)
    report = discover(name, rows, formula, slots, Journal(str(folder / 'journal.jsonl')))
    check('spec: rows', len(rows), 200)
    check('spec: rule', report[0]['rule'], {'rate': '3.5 %', 'rounding': 'truncate before 2007-08-11, then half up'})
    check('spec: exact', round(report[0]['train'], 6), 1.0)


def edge_rows():
    random.seed(11)
    rows = []
    for i in range(2000):
        amount = D(random.randrange(1000, 9000000)) / 100
        pid = f'E{i // 2}'
        rows.append({'policy': pid, 'key': i, 'holdout': is_holdout(pid), 'amount': amount, 'date': dt.date(2020, 1, 1),
                     'target': (amount * D('0.037')).quantize(D('0.001'), rounding=ROUND_HALF_EVEN),
                     'features': {'size': int(amount) // 10000}})
    return rows


def edge_formula(row, c):
    return c['rounding'](row['amount'] * c['rate'], row['date'])


def test_edge_case():
    rows, journal = edge_rows(), Journal(TMP / 'edge.jsonl')
    fixed = {'rate': {'3 %': D('0.03'), '3.5 %': D('0.035'), '4 %': D('0.04')}, 'rounding': b.ROUNDINGS}
    report = discover('edge fixed', rows, edge_formula, fixed, journal)
    leaves = [p for p in report if p.get('leaf')]
    check('edge: fixed dictionary does not claim the rule', max(p['train'] for p in report) < 0.5, True)
    check('edge: fixed dictionary reports what is left', all(p['unexplained'] and p['prompt'] for p in leaves), True)
    generated = {'rate': Fit(lambda r: r['amount']), 'rounding': b.roundings_any()}
    report = discover('edge generated', rows, edge_formula, generated, journal)
    check('edge: generated families find it', report[0]['rule'], {'rate': 'fitted 0.037', 'rounding': 'half even, 3 decimals'})
    check('edge: generated families exact', (report[0]['train'], report[0]['test']), (1.0, 1.0))
    good = "def brick(value, date=None):\n    return value.quantize(D('0.001'), rounding=ROUND_HALF_EVEN)"
    bad = "def brick(value, date=None):\n    return value.quantize(D('0.1'), rounding=ROUND_HALF_UP)"
    near = {'rate': {'3.7 %': D('0.037')}, 'rounding': b.ROUNDINGS}
    report = discover_with_proposals('edge llm good', rows, edge_formula, near, journal,
                                     proposer=lambda prompt, hole: {'half even to 3 decimals': good} if hole == 'rounding' else {})
    check('edge: a right proposal is kept', (report[0]['rule']['rounding'], report[0]['test']), ('proposed: half even to 3 decimals', 1.0))
    report = discover_with_proposals('edge llm bad', rows, edge_formula, near, journal,
                                     proposer=lambda prompt, hole: {'one decimal': bad} if hole == 'rounding' else {})
    check('edge: a wrong proposal is rejected', report[0]['rule']['rounding'].startswith('proposed'), False)
    check('edge: business days', b.business_days_after(dt.date(2026, 12, 24), 1, b.holidays(b.FIXED_HOLIDAYS_TI, b.EASTER_OFFSETS_TI)), dt.date(2026, 12, 28))
    check('edge: offsets family', b.offsets_any()['+3 days'](dt.date(2026, 7, 1)), dt.date(2026, 7, 4))


def test_missing_input():
    """Rate 2 % for kind 'a', 1 % otherwise; the kind is unknown (None) on a third of the 'a' rows."""
    random.seed(5)
    rows = []
    for i in range(1500):
        kind = 'a' if i == 0 else random.choice('ab')  # the first row has no kind
        amount = D(random.randrange(1000, 900000)) / 100
        rate = D('0.02') if kind == 'a' else D('0.01')
        pid = f'M{i}'
        shown = None if kind == 'a' and i % 3 == 0 else kind
        rows.append({'policy': pid, 'holdout': is_holdout(pid), 'amount': amount, 'date': dt.date(2020, 1, 1),
                     'target': b.ROUNDINGS['half up'](amount * rate), 'features': {'kind': shown, 'size': int(amount)}})
    slots = {'rate': {'1 %': D('0.01'), '2 %': D('0.02')}, 'rounding': {'half up': b.ROUNDINGS['half up']}}
    report = discover('missing', rows, edge_formula, slots, Journal(TMP / 'missing.jsonl'))
    leaves = [p for p in report if p.get('leaf')]
    check('missing input: the diagnosis still splits', len(leaves) > 1, True)
    check('missing input: each leaf is exact', all(p['train'] == 1 for p in leaves), True)


EASTER_BRICK = """```python
# name: the current rule plus Easter Monday, Ascension, Whit Monday and Corpus Christi
def brick(day):
    def easter(y):
        a, b, c = y % 19, y // 100, y % 100
        h = (19 * a + b - b // 4 - (b - (b + 8) // 25 + 1) // 3 + 15) % 30
        l = (32 + 2 * (b % 4) + 2 * (c // 4) - h - c % 4) % 7
        m = (a + 11 * h + 22 * l) // 451
        n = h + l - 7 * m + 114
        return dt.date(y, n // 31, n % 31 + 1)
    moving = lambda d: d in {easter(d.year) + dt.timedelta(k) for k in (1, 39, 50, 60)}
    result = best(day)
    while moving(result):
        result = best(result + dt.timedelta(1))
    return result
```"""
WRONG_BRICK = "```python\n# name: two days later\ndef brick(day):\n    return day + dt.timedelta(2)\n```"


def test_llm_end_to_end():
    import http.server
    import json
    import os
    import threading
    import llm
    from spec import build

    class Fake(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            ok = self.headers['Authorization'] == 'Bearer test-key' and 'hole to extend' in body['messages'][0]['content']
            answers = [EASTER_BRICK, WRONG_BRICK] if ok else []
            reply = json.dumps({'choices': [{'message': {'content': a}} for a in answers]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ['VAST_URL'], os.environ['VAST_TOKEN'] = f'http://127.0.0.1:{server.server_port}', 'test-key'
    llm.LOG = str(TMP / 'llm.jsonl')
    folder = TMP / 'llm'
    folder.mkdir()
    shift = b.SHIFTS['next business day (Ticino, with Easter)']
    days = [dt.date(2026, 7, 1) + dt.timedelta(i) for i in range(365)]
    (folder / 'NRDUE.csv').write_text('DU_ID;DU_DATE\n' + ''.join(f'D{i};{d.isoformat()}\n' for i, d in enumerate(days * 3)))
    (folder / 'due.csv').write_text('id,collection\n' + ''.join(f'D{i},{shift(d).isoformat()}\n' for i, d in enumerate(days * 3)))
    no_easter = ['same day', 'next weekday', 'next business day (Ticino, fixed only)']
    spec = {'target': {'file': 'due', 'keys': ['id'], 'value': 'collection', 'type': 'date'},
            'rows': {'from': 'NRDUE', 'key': ['DU_ID']},
            'holes': {'collection': {'family': 'SHIFTS', 'only': no_easter}},
            'formula': 'collection(iso(DU_DATE))', 'features': {'weekday': 'iso(DU_DATE).weekday()'}}
    (folder / 'spec.json').write_text(json.dumps(spec))
    rows, slots, formula, name, _, _, _ = build(folder / 'spec.json', folder, folder)
    journal = Journal(TMP / 'llm_journal.jsonl')
    without = discover(name, rows, formula, slots, journal)
    report = discover_with_proposals(name, rows, formula, slots, journal, proposer=llm.propose)
    server.shutdown()
    check('llm: without the model the rule is incomplete', without[0]['train'] < 1, True)
    check('llm: the right brick is kept', report[0]['rule']['collection'].startswith('proposed: the current rule'), True)
    check('llm: and explains every row', (report[0]['train'], report[0]['test']), (1.0, 1.0))
    check('llm: the source is in the journal', any(e.get('accepted') for e in journal.entries), True)


def test_sandbox_rejects_escapes():
    """Code from a model may not reach dunder attributes or import anything (a way out of the restricted builtins)."""
    from engine import compile_brick
    escapes = ["def brick(x):\n    return ().__class__.__bases__[0].__subclasses__()",
               "def brick(x):\n    import os\n    return os.listdir('.')",
               "def brick(x):\n    return getattr(x, '__class__')",
               "def brick(x):\n    return (y for y in ()).gi_frame.f_back.f_globals",
               "def brick(x):\n    return '{0.__class__}'.format(x)",
               "def brick(x):\n    return '{0.mro}'.format(x)",
               "def brick(x):\n    return x._private",
               "def brick(x):\n    return dt.sys"]
    for source in escapes:
        try:
            compile_brick(source)
            FAILED.append(f'sandbox: accepted {source.splitlines()[1].strip()!r}')
        except ValueError:
            pass
    check('sandbox: a plain brick still compiles', compile_brick("def brick(x):\n    return x + D('0.01')")(D(1)), D('1.01'))
    helper = "def brick(x):\n    def _cent(v):\n        return v + D('0.01')\n    return _cent(x)"
    check('sandbox: a helper with one underscore compiles', compile_brick(helper)(D(1)), D('1.01'))


def test_model_before_a_random_date_split():
    """A rule the dictionary lacks shows as misses after some date; a cut at that date is no business event, so
    the engine asks the model about the whole part first and keeps one rule instead of a split."""
    from engine import compile_brick
    shift = b.SHIFTS['next business day (Ticino, with Easter)']
    days = [dt.date(2026, 7, 1) + dt.timedelta(i) for i in range(365)]
    rows = [{'policy': f'P{i}', 'key': i, 'holdout': is_holdout(f'P{i}'), 'due': d, 'target': shift(d),
             'features': {'due date': d}} for i, d in enumerate(days * 3)]
    slots = {'collection': {k: b.SHIFTS[k] for k in ('same day', 'next business day (Ticino, fixed only)')}}
    formula = lambda row, c: c['collection'](row['due'])  # noqa: E731
    asked = []

    def proposer(prompt, hole):
        asked.append(prompt.splitlines()[0])
        return {'Easter holidays': EASTER_BRICK.split('```python\n')[1].split('```')[0]}
    plausible = lambda test: ' < ' not in test  # noqa: E731  (no date is a landmark here)
    report = discover_with_proposals('defer', rows, formula, slots, Journal(TMP / 'defer.jsonl'), proposer=proposer,
                                     plausible=plausible)
    leaves = [p for p in report if p.get('leaf')]
    check('defer: one part, no date split', len(leaves), 1)
    check('defer: the model was asked about all rows', asked[:1], ['# Rule search stalled: defer / all rows'])
    check('defer: exact', (leaves[0]['train'], leaves[0]['test']), (1.0, 1.0))


def test_learned_bricks_are_stored_and_sandboxed():
    """A kept brick is stored with where it comes from and comes back compiled through the sandbox."""
    import json
    import learned
    from conventions_calendar import next_business_day_ticino_fixed
    learned.STORE = TMP / 'learned.json'
    source = EASTER_BRICK.split('```python\n')[1].split('```')[0]
    learned.save('demo', {('collection', 'proposed: easter'): ((source, next_business_day_ticino_fixed), '(1, 2) -> (3, 4)')},
                 'test-model')
    brick = learned.bricks('demo', 'collection')['proposed: easter']
    check('learned: Easter Monday 2027 moves on', brick(dt.date(2027, 3, 29)), dt.date(2027, 3, 30))
    check('learned: provenance', json.loads(learned.STORE.read_text())[0]['extends'],
          'conventions_calendar.next_business_day_ticino_fixed')
    stored = json.loads(learned.STORE.read_text())
    stored[0]['source'] = "def brick(day):\n    return day.__class__"
    learned.STORE.write_text(json.dumps(stored))
    try:
        learned.bricks('demo', 'collection')
        FAILED.append('learned: a stored escape was compiled')
    except ValueError:
        pass


if __name__ == '__main__':
    test_learned_bricks_are_stored_and_sandboxed()
    test_model_before_a_random_date_split()
    test_sandbox_rejects_escapes()
    test_bricks()
    test_planted_rules()
    test_spec()
    test_edge_case()
    test_missing_input()
    test_llm_end_to_end()
    print('\n'.join(FAILED) if FAILED else 'all self-tests passed')
    sys.exit(1 if FAILED else 0)
