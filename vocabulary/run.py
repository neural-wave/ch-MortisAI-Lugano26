"""Run the rule finder and write the journal and a Markdown report.

    python3 vocabulary/run.py --solution my_solution                  # the built-in cases
    python3 vocabulary/run.py --spec vocabulary/specs/t0_commission.json  # a target declared in JSON, no Python

A spec (see spec.py) needs no Python and no solution folder. The built-in cases (cases/) cover the
targets that need a simulation (t2, t3, t4); they use the solution folder only to load the tables.
"""
import argparse
import csv
import importlib
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / 'my_solution'))  # the tables and the conventions
from engine import Journal, discover_with_proposals, expand  # noqa: E402
import learned  # noqa: E402

SYSTEM = ('Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until '
          '2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.')
CASES = ['t0_commission', 't1_collection', 't2_offer', 't2_offer_plain', 't3_units', 't3_penalty', 't4_premiums']


def pct(x):
    """0.99995 -> '99.995 %'."""
    return f'{100 * x:.3f} %'


def report_lines(name, doc, rows, slots, report, journal):
    """The Markdown section of one case: the parts of the rule, what is left over, the runner-ups."""
    combos = 1
    for s in slots.values():
        combos *= len(s)
    md = [f'## {name}', '', doc.strip(), '',
          f'{len(rows)} rows, {combos} combinations of {", ".join(f"{k} ({len(v)})" for k, v in slots.items())}.', '',
          '| Segment | Rule | Search | Held out |', '|---|---|---|---|']
    for part in report:
        rule = '; '.join(f'{k}: **{v}**' for k, v in part['rule'].items())
        md.append(f"| {part['segment']} | {rule} | {pct(part['train'])} | {pct(part['test'])} |")
        print(f"  {part['segment']:45s} {pct(part['train']):>9s} {pct(part['test']):>9s}  {part['rule']}", flush=True)
        if part.get('leaf') and part['unexplained']:
            n = len(part['unexplained'])
            md.append(f"| ↳ left over | {n} {'row' if n == 1 else 'rows'} the rule does not explain"
                      f"{' (prompt for an LLM written)' if part.get('prompt') else ' (candidates for manual corrections, t5)'} | | |")
        if 'fails_where' in part:
            w = part['fails_where']
            md.append(f"| ↳ misses concentrate where `{w['test']}` | {pct(w['miss_if_true'])} missed if true, "
                      f"{pct(w['miss_if_false'])} if false | | |")
    kept = [(e, tag) for e in journal.entries if e['case'] == name for tag in e.get('accepted') or []]
    for e, tag in kept:  # the source of every proposed brick in the final rule, so a person can judge it
        md += ['', f"Brick proposed by the model and kept ({e['step']}; {e['note']}): **{tag}**", '',
               '```python', e['proposals'][tag].strip(), '```']
    top = journal.entries[[e['case'] for e in journal.entries].index(name)]['tried'][:5]
    md += ['', 'Runners-up on all rows:', '', '| Rule | Search | Held out |', '|---|---|---|']
    md += [f"| {'; '.join(f'{k}: {v}' for k, v in r['choice'].items())} | {pct(r['train'])} | {pct(r['test'])} |" for r in top]
    return md


def known_corrections(legacy, target):
    """Policies with a listed manual correction (NREXCP) of `target`, e.g. 't0_commission'."""
    with open(Path(legacy) / 'NREXCP.csv', encoding='utf-8') as f:
        return {r['EX_POLNR'].strip() for r in csv.DictReader(f, delimiter=';') if r['EX_TARGET'].startswith(target)}


def left_over_lines(name, report, rows, nrexcp, legacy, out, left_over):
    """Write what the rules leave over (outliers.csv, prompts) and compare it with NREXCP."""
    md, missed, prompts = [], set(), []
    for part in report:
        if part.get('prompt'):
            prompts.append(part['prompt'])
        for row, calc in part.get('unexplained', []):
            left_over.append([name, part['segment'], row.get('key', row['policy']), row['target'], calc])
            missed.add(row['policy'])
    if prompts:  # one file per case, one section per unexplained part
        (out / f'{name}_prompt.md').write_text('\n\n---\n\n'.join(prompts) + '\n', encoding='utf-8')
    if nrexcp:
        listed = known_corrections(legacy, nrexcp) & {r['policy'] for r in rows}
        found = listed & missed
        verdict = ('all of them are listed corrections' if missed and missed <= listed else
                   f'{len(missed - listed)} are not listed corrections' if missed else 'nothing')
        md += ['', f'Left over: {len(missed)} policies ({verdict}). The rows contain {len(listed)} policies with a '
                   f'listed manual correction (NREXCP {nrexcp}); {len(found)} of them are left over.']
        print(f'  left over: {len(missed)} policies, {len(missed & listed)} of them listed in NREXCP '
              f'(listed found: {len(found)}/{len(listed)})', flush=True)
    elif missed:
        print(f'  left over: {len(missed)} policies', flush=True)
    return md


def plausible_splits(legacy):
    """test text -> bool: a split on a date is made at once only on a business date of the export (a day of
    events of one kind for many policies, the start of a parameter row) or on a 1 January; any other date waits
    until a language model was asked about the whole part (engine.discover_with_proposals)."""
    import datetime as dt
    from solve import landmarks
    from tables import table, day
    dates = set(landmarks(legacy))
    for name, prefix in (('NRCHRG', 'CG'), ('NRENTC', 'EC'), ('NRCOMR', 'CR'), ('NRILLU', 'IL'), ('NRWAIV', 'WV')):
        dates |= {day(r[prefix + '_VLDFR']) for r in table(str(legacy), name)}

    def plausible(test):
        if ' < ' not in test:
            return True
        try:
            when = dt.date.fromisoformat(test.split(' < ')[1])
        except ValueError:
            return True  # a number, not a date
        return when in dates or (when.month, when.day) == (1, 1)
    return plausible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--legacy', default='legacy')
    ap.add_argument('--targets', default='targets')
    ap.add_argument('--solution', help='solution folder, only to load tables for the built-in cases')
    ap.add_argument('--out', default=str(HERE / 'results'))
    ap.add_argument('--cases', nargs='*', default=None, help='built-in cases to run (default: all)')
    ap.add_argument('--spec', nargs='*', default=[], help='JSON specs to run instead of / besides the cases')
    ap.add_argument('--llm', action='store_true', help='ask llm.propose for new bricks where a part stays unexplained')
    a = ap.parse_args()
    cases = a.cases if a.cases is not None else ([] if a.spec else CASES)
    if cases and not a.solution:
        ap.error('the built-in cases need --solution (the folder with tables.py, e.g. my_solution); specs do not')
    if a.solution:
        sys.path.insert(1, str(Path(a.solution).resolve()))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    journal = Journal(out / 'journal.jsonl')
    md = ['# Rule finder report', '']
    jobs = [('case', c) for c in cases] + [('spec', s) for s in a.spec]
    proposer = None
    if a.llm:
        import llm
        llm.LOG = str(out / 'llm_proposals.jsonl')
        proposer = llm.propose
    plausible = plausible_splits(a.legacy)
    left_over = []
    for kind, item in jobs:
        t = time.time()
        if kind == 'case':
            case = importlib.import_module(f'cases.{item}')
            rows, slots, formula = case.build(a.legacy, a.targets)
            name, doc, nrexcp, depth = item, case.__doc__ or '', getattr(case, 'NREXCP', None), 2
        else:
            from spec import build
            rows, slots, formula, name, doc, nrexcp, depth = build(item, a.legacy, a.targets)
        print(f'== {name}: {len(rows)} rows', flush=True)
        slots = {hole: ({**options, **learned.bricks(name, hole)} if isinstance(options, dict) else options)
                 for hole, options in slots.items()}  # bricks a model proposed in an earlier run of this case
        report = discover_with_proposals(name, rows, formula, slots, journal, depth=depth, proposer=proposer,
                                         context=f'{SYSTEM}\nTarget: {doc.strip()}', plausible=plausible)
        if a.llm and report[0]['learned']:
            learned.save(name, report[0]['learned'], llm.MODEL)
        md += report_lines(name, doc, rows, expand(rows, slots), report, journal)
        md += left_over_lines(name, report, rows, nrexcp, a.legacy, out, left_over)
        if kind == 'case' and hasattr(case, 'extra_report'):  # e.g. the change point of t2_offer_plain
            md += case.extra_report(rows, formula, slots, out)
        md += ['', f'_{time.time() - t:.0f} s_', '']
    with open(out / 'outliers.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['case', 'segment', 'key', 'expected', 'calculated'])
        w.writerows(left_over)
    (out / 'report.md').write_text('\n'.join(md), encoding='utf-8')
    print('report:', out / 'report.md')


if __name__ == '__main__':
    main()
