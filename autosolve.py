"""One button: find the rules of Neuron in the data and write them into my_solution/rules.py.

    python3 autosolve.py --legacy legacy --targets targets       # every target autosolve knows
    python3 autosolve.py --verify       # only check that my_solution/rules.py is what the search writes
    python3 autosolve.py --verify --cached   # the same, from the last search if no input changed since
    python3 autosolve.py --demo         # a live show in about a minute: the era, t0 and t1, compared with rules.py

For each case of vocabulary/cases (in the order of CASES), the rule search fills its holes with the bricks of
my_solution/conventions.py, scores every combination by exact matches on the train targets and checks the
winner on held-out policies (vocabulary/solve.py says how ties, eras and splits become rules). The winners
are written to my_solution/rules.py (vocabulary/emit.py), the official check.py scores the solution, and
results/autosolve/report.md records what was found and how long it took. No language model, no hand-made choice.
"""
import argparse
import ast
import hashlib
import json
import pickle
import importlib
import subprocess
import sys
import time
import zlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / 'vocabulary'), str(ROOT / 'my_solution')]
from engine import Journal, discover, score  # noqa: E402
from emit import Section, rules_text  # noqa: E402
from solve import ranked, ties, choose, landmarks, cut, snap, descend  # noqa: E402

CASES = ['era', 't0_commission', 't1_collection', 't1_schedule', 't3_trade', 't3_amounts', 't3_units_premium',
         't3_units_charges', 't3_entry', 't3_charges', 't3_value', 't3_valuation', 't3_surrender', 't4_end_year',
         't2_offer_years', 't7_tax', 't7_structure']  # t2 uses the risk rate found on the t3 charges  # in the order of their dependencies: the era comes first
DEMO = ['era', 't0_commission', 't1_collection', 't1_schedule']  # the cases a live show runs (about a minute)
RULES = ROOT / 'my_solution' / 'rules.py'
CACHE = ROOT / '.cache' / 'autosolve.json'
SECTIONS = ROOT / '.cache' / 'autosolve_sections.pkl'  # the sections of the last full search, for --only  # the fingerprint of the inputs of the last search and the text it wrote


def fingerprint(args):
    """A hash of everything the search reads: the code of the search and of the solution (not rules.py), and the
    name, size and modification time of every data file."""
    digest = hashlib.sha256()
    code = [ROOT / 'autosolve.py', *sorted((ROOT / 'vocabulary').rglob('*.py')), *sorted((ROOT / 'my_solution').glob('*.py'))]
    for path in code:
        if path != RULES:
            digest.update(path.read_bytes())
    for folder in (args.legacy, args.targets):
        for path in sorted(Path(folder).glob('*.csv')):
            stat = path.stat()
            digest.update(f'{path.name}:{stat.st_size}:{stat.st_mtime_ns}'.encode())
    return digest.hexdigest()


def cached_verdict(args):
    """True or False if the last search saw the same inputs (rules.py is or is not its text), None otherwise."""
    if not CACHE.exists():
        return None
    cache = json.loads(CACHE.read_text(encoding='utf-8'))
    if cache['fingerprint'] != fingerprint(args):
        return None
    return RULES.exists() and hashlib.sha256(RULES.read_bytes()).hexdigest() == cache['rules']
ERAS = ('COBOL', 'Neuron NG')


def pct(share):
    return f'{100 * share:.4f} %'


def exact(result):
    """'99.9951 % of the search rows, 99.9976 % held out' for a scored combination."""
    return f"{pct(result['train'])} of the search rows, {pct(result['test'])} held out"


def left(n):
    """'1 row left over', '9 rows left over'."""
    return f"{n} {'row' if n == 1 else 'rows'} left over"


def settle(segment, results, families, prefer, tied=None):
    """{hole: label} of one segment: the tied options of each hole settled by the principle, plus the notes."""
    chosen, notes = {}, []
    for hole, labels in (tied or ties(results)).items():
        chosen[hole], reason = choose(hole, labels, families[hole], prefer.get(hole))
        if reason:
            notes.append(f"Not distinguishable on train{segment}: {hole} {' = '.join(labels)}; chosen {chosen[hole]} ({reason}).")
    match = next(r for r in results if r['choice'] == chosen)
    if match['hits'] != results[0]['hits']:
        raise ValueError(f'{segment}: the settled options {chosen} do not reach the best score together')
    return chosen, match, notes


def wider(case, rows, formula, slots):
    """(slots, notes): the case's EXTRA holes join the search when its fixed options explain less than half of the
    rows (another client: the era cannot be found on rows that fail for other reasons)."""
    best = ranked(rows, formula, slots)[0][0]
    if best['train'] >= 0.5 or not hasattr(case, 'EXTRA'):
        return slots, []
    return {**slots, **case.EXTRA}, [f"The fixed options fit {exact(best)}: {', '.join(case.EXTRA)} searched as well."]


def find_era(case, rows, formula, slots, args, state):
    """The cut-off: where the diagnosis splits the best single rule, moved onto a landmark of the export."""
    results, _ = ranked(rows, formula, slots)
    found = cut(rows, results)
    if found is None:
        raise ValueError(f'{case.TITLE}: no date splits the best single rule ({exact(results[0])}): no era to find')
    feature, when, below = found
    state['cutoff'], kind = snap(when, below, landmarks(args.legacy))
    state['feature'] = feature
    landmark = f' moved onto {state["cutoff"]}, the only day of all events {kind} (NREVNT).' if kind else ' no landmark in the gap.'
    notes = [f'{len(rows):,} rows; the best single rule fits {exact(results[0])}.',
             f'The diagnosis splits on {feature} < {when} (the last value before it: {below});' + landmark]
    return notes, [('ERA_CUTOFF', state['cutoff'], 'the first day of Neuron NG; before it the COBOL system')]


ERA_NOTE = 'the day whose system (COBOL or Neuron NG) applies the pairs of this calculation'
ERA_DAY = 'the day of the calculation itself: so it is wherever the data decide, as in the charges'


def era_date(case, rows, formula, bricks, cutoff):
    """The candidate of case.ERA_DATES whose day, put against the cut-off, lets the rules of each era (`bricks`, a
    {hole: brick} for COBOL and one for Neuron NG) match most rows; a tie goes to the first candidate, the day of
    the calculation itself. Returns the label and the notes: each candidate's exact rows and the rows it puts in
    the other era (the rows that decide)."""
    sides, exact = {}, {}
    for label in case.ERA_DATES:
        sides[label] = [r['features'][label] >= cutoff for r in rows]
        parts = [[r for r, late in zip(rows, sides[label]) if late == (i == 1)] for i in (0, 1)]
        exact[label] = sum(hits['train'] + hits['test'] for hits, _ in map(score, parts, (formula, formula), bricks))
    label = next(name for name in case.ERA_DATES if exact[name] == max(exact.values()))
    moved = {name: sum(a != b for a, b in zip(sides[name], sides[label])) for name in case.ERA_DATES if name != label}
    tied = [name for name in moved if exact[name] == exact[label] and moved[name]]  # 0 rows moved: the same day here
    notes = [f"The day of the era ({case.ERA_RULE}): {label} ({exact[label]:,} exact rows); "
             + '; '.join(f'{name}: {exact[name]:,} ({moved[name]:,} rows in the other era)' for name in moved) + '.']
    if tied:
        notes.append(f"Not distinguishable on train: the day of the era {' = '.join([label, *tied])}; chosen {label} "
                     f"({ERA_DAY}).")
    return label, notes


def era_bricks(case, brick):
    """[{hole: brick} of COBOL, of Neuron NG] for the chosen labels; brick(era, hole) looks one up."""
    return [{hole: brick(era, hole) for hole in case.RULES} for era in ERAS]


def era_section(case, rows, formula, slots, args, state, feature=None):
    """Rules of a case that depends on the era: the cut-off (if the case finds it), the day that decides the era
    and a pair per era hole. If another day than the first one tried fits better, the search runs again on it."""
    finder = getattr(case, 'ERA_FINDER', False)
    slots, widened = wider(case, rows, formula, slots) if finder and not feature else (slots, [])
    cut_off = find_era(case, rows, formula, slots, args, state) if finder and not feature else ([], [])
    cut_off = (widened + cut_off[0], cut_off[1])
    notes, assignments = list(cut_off[0]), list(cut_off[1])
    tried, feature = feature, feature or (state['feature'] if finder else next(iter(case.ERA_DATES)))
    parts = {era: [r for r in rows if (r['features'][feature] >= state['cutoff']) == (i == 1)] for i, era in enumerate(ERAS)}
    ranking = {era: ranked(part, formula, slots) for era, part in parts.items()}
    families = {era: ranking[era][1] for era in ERAS}
    tied = {era: ties(ranking[era][0]) for era in ERAS}
    for hole in case.RULES:  # a hole outside the era needs one option that is among the best in both eras
        if hole not in case.ERA_HOLES:
            both = [label for label in tied[ERAS[1]][hole] if label in tied[ERAS[0]][hole]]
            tied[ERAS[0]][hole] = tied[ERAS[1]][hole] = both or tied[ERAS[1]][hole]
    chosen = {}
    for i, era in enumerate(ERAS):
        consistent = {h: (state['era'][id(families[era][h])][i], 'the rule of the same era in the other calculations')
                      for h in case.ERA_HOLES if id(families[era][h]) in state['era']}
        chosen[era], match, tie_notes = settle(f' ({era})', ranking[era][0], families[era],
                                               {**getattr(case, 'PREFER', {}), **consistent}, tied[era])
        notes += [f'{era} ({feature} {"<" if i == 0 else ">="} {state["cutoff"]}): {len(parts[era]):,} rows, {exact(match)}; '
                  f"{left(len(parts[era]) - sum(match['hits']))} (t5).", *tie_notes]
    for hole, name in case.RULES.items():
        bricks = tuple(families[era][hole][chosen[era][hole]] for era in ERAS)
        if hole in case.ERA_HOLES and finder:
            state['era'][id(families[ERAS[0]][hole])] = tuple(chosen[era][hole] for era in ERAS)
        if hole not in case.ERA_HOLES and bricks[0] is not bricks[1]:
            raise ValueError(f'{hole}: not an era hole, but the eras choose {chosen}')
        assignments.append((name, bricks if hole in case.ERA_HOLES else bricks[0], case.NOTES.get(hole, '')))
    label, date_notes = era_date(case, sampled(case, rows), formula,
                                 era_bricks(case, lambda era, hole: families[era][hole][chosen[era][hole]]),
                                 state['cutoff'])
    if label != feature:
        if tried:
            raise ValueError(f'{case.TITLE}: the day of the era does not settle ({tried} -> {label})')
        section, chosen = era_section(case, rows, formula, slots, args, state, label)
        return Section(case.TITLE, cut_off[0] + section.notes, cut_off[1] + section.assignments), chosen
    assignments.insert(len(assignments) - len(case.RULES), (case.ERA_RULE, case.ERA_DATES[label], ERA_NOTE))
    return Section(case.TITLE, notes + date_notes, assignments), chosen


def sampled(case, rows):
    """The rows of `case.SAMPLE` percent of the policies (all rows without a SAMPLE)."""
    share = getattr(case, 'SAMPLE', 100)
    return [r for r in rows if zlib.crc32(r['policy'].encode()) % 100 < share]


def confirmed(rows, formula, bricks):
    """'x % of the search rows, y % held out; n rows left over' of a rule on all rows."""
    hits, _ = score(rows, formula, bricks)
    return (f"{pct(hits['train'] / max(1, hits['train_n']))} of the search rows, "
            f"{pct(hits['test'] / max(1, hits['test_n']))} held out; {left(len(rows) - hits['train'] - hits['test'])} (t5)")


def plain_section(case, rows, formula, slots):
    """Rules of a case with one rule for all rows: the best combination, its ties settled by the principle."""
    sample = sampled(case, rows)
    results, families = ranked(sample, formula, slots)
    chosen, match, tie_notes = settle('', results, families, getattr(case, 'PREFER', {}))
    bricks = {hole: families[hole][label] for hole, label in chosen.items()}
    notes = [f"{len(rows):,} rows; every one of {len(results)} combinations tried on {getattr(case, 'SAMPLE', 100)} % of "
             f"the policies ({len(sample):,} rows); confirmed on all rows: {confirmed(rows, formula, bricks)}.", *tie_notes]
    assignments = [(name, families[hole][chosen[hole]], case.NOTES.get(hole, '')) for hole, name in case.RULES.items()]
    return Section(case.TITLE, notes, assignments), chosen


def descent_section(case, rows, formula, slots):
    """Rules of a case with many holes: a coordinate search on a sample of the policies, confirmed on all rows."""
    sample = [r for r in rows if zlib.crc32(r['policy'].encode()) % 100 < case.SAMPLE]
    labels, best, evaluations, tied, families = descend(sample, formula, slots)
    chosen, notes = {}, []
    for hole, options in tied.items():
        chosen[hole], reason = choose(hole, options, families[hole], getattr(case, 'PREFER', {}).get(hole))
        if reason:
            notes.append(f"Not distinguishable on train: {hole} {' = '.join(options)}; chosen {chosen[hole]} ({reason}).")
    bricks = {hole: families[hole][label] for hole, label in chosen.items()}
    hits, _ = score(sample, formula, bricks)
    if (hits['train'], hits['test']) != best:
        raise ValueError(f'{case.TITLE}: the settled options {chosen} do not reach the best score together')
    hits, _ = score(rows, formula, bricks)
    notes = [f"{len(rows):,} rows; a coordinate search from the simplest options on {case.SAMPLE} % of the policies "
             f"({len(sample):,} rows, {evaluations} trials); confirmed on all rows: "
             f"{pct(hits['train'] / hits['train_n'])} of the search rows, {pct(hits['test'] / hits['test_n'])} held out; "
             f"{left(len(rows) - hits['train'] - hits['test'])} (t5).", *notes]
    assignments = [(name, bricks[hole], case.NOTES.get(hole, '')) for hole, name in case.RULES.items()]
    return Section(case.TITLE, notes, assignments), chosen


def era_descent_section(case, rows, formula, slots, state, feature=None):
    """Rules of a case with many holes in two eras: a coordinate search per era, era holes become pairs and the
    other holes must have one option among the best of both eras. The day that decides the era is compared last;
    if another day than the first one tried fits better, the search runs again on it."""
    cutoff, notes, runs, tried = state['cutoff'], [], {}, feature
    feature = feature or next(iter(case.ERA_DATES))
    state['found'][case.ERA_RULE] = case.ERA_DATES[feature]  # the full replay of case.confirm calculates on this day
    for i, era in enumerate(ERAS):
        part = [r for r in rows if (r['features'][feature] >= cutoff) == (i == 1)]
        runs[era] = (part, *descend(sampled(case, part), formula, slots))
    families = runs[ERAS[1]][5]
    chosen = {era: {} for era in ERAS}
    for hole in case.RULES:
        if hole not in case.ERA_HOLES:
            both = [label for label in runs[ERAS[1]][4][hole] if label in runs[ERAS[0]][4][hole]]
            runs[ERAS[0]][4][hole] = runs[ERAS[1]][4][hole] = both or runs[ERAS[1]][4][hole]
    for i, era in enumerate(ERAS):
        part, labels, best, evaluations, tied, _ = runs[era]
        consistent = {h: (state['era'][id(families[h])][i], 'the rule of the same era in the other calculations')
                      for h in case.ERA_HOLES if id(families[h]) in state['era']}
        prefer, tie_notes = {**getattr(case, 'PREFER', {}), **consistent}, []
        for hole, options in tied.items():
            chosen[era][hole], reason = choose(hole, options, families[hole], prefer.get(hole))
            if reason:
                tie_notes.append(f"Not distinguishable on train ({era}): {hole} {' = '.join(options)}; "
                                 f"chosen {chosen[era][hole]} ({reason}).")
        bricks = {hole: families[hole][label] for hole, label in chosen[era].items()}
        notes += [f"{era} ({feature} {'<' if i == 0 else '>='} {cutoff}): {len(part):,} rows, coordinate search on "
                  f"{getattr(case, 'SAMPLE', 100)} % of the policies ({evaluations} trials); confirmed: "
                  f"{confirmed(part, formula, bricks)}.", *tie_notes]
    if hasattr(case, 'confirm'):
        replay_notes, decided = escalate(case, families, chosen, runs, state)
        notes = [n for n in notes if not any(n.startswith(f'Not distinguishable on train ({era}): {hole} ')
                                             for era in ERAS for hole in decided)] + replay_notes
    label, date_notes = era_date(case, sampled(case, rows), formula,
                                 era_bricks(case, lambda era, hole: families[hole][chosen[era][hole]]), cutoff)
    if label != feature:
        if tried:
            raise ValueError(f'{case.TITLE}: the day of the era does not settle ({tried} -> {label})')
        return era_descent_section(case, rows, formula, slots, state, label)
    assignments = [(case.ERA_RULE, case.ERA_DATES[label], ERA_NOTE)]
    for hole, name in case.RULES.items():
        pair = tuple(families[hole][chosen[era][hole]] for era in ERAS)
        if hole not in case.ERA_HOLES and pair[0] is not pair[1]:
            raise ValueError(f'{case.TITLE}: {hole} is not an era hole, but the eras choose {chosen}')
        assignments.append((name, pair if hole in case.ERA_HOLES else pair[0], case.NOTES.get(hole, '')))
    return Section(case.TITLE, notes + date_notes, assignments), chosen


def full_choice(case, families, chosen):
    """{rule name: brick, or (COBOL, Neuron NG) pair for an era hole} of per-era labels."""
    return {name: tuple(families[hole][chosen[era][hole]] for era in ERAS) if hole in case.ERA_HOLES
            else families[hole][chosen[ERAS[1]][hole]] for hole, name in case.RULES.items()}


def escalate(case, families, chosen, runs, state):
    """Ties settled as merely the simplest are tried again on all train policies (case.confirm, a full replay):
    per hole, the option that matches most there is kept. Updates `chosen`; returns the notes and the holes the
    full data decided (their sample ties are no ties)."""
    weak = sorted({hole for era in ERAS for hole, options in runs[era][4].items() if len(options) > 1
                   and hole not in case.ERA_HOLES})
    trials = [(hole, label) for hole in weak for label in runs[ERAS[1]][4][hole] if label != chosen[ERAS[1]][hole]]
    if not trials:
        return [], set()
    variants = [full_choice(case, families, {era: {**chosen[era], hole: label} for era in ERAS}) for hole, label in trials]
    base, *scores = case.confirm(state['args'].legacy, state['args'].targets, state['found'],
                                 [full_choice(case, families, chosen), *variants])
    notes, decided = [], set()
    for hole in weak:
        counts = {chosen[ERAS[1]][hole]: base, **{label: n for (h, label), n in zip(trials, scores) if h == hole}}
        best = max(counts.values())
        winners = [label for label, n in counts.items() if n == best]
        if len(winners) == 1:
            decided.add(hole)
            for era in ERAS:
                chosen[era][hole] = winners[0]
        listed = '; '.join(f'{label}: {n:,}' for label, n in counts.items())
        notes.append(f"All train policies, a full replay ({hole}): charge totals matched by {listed}"
                     + ('.' if len(winners) == 1 else ' (still not distinguishable).'))
    return notes, decided


def era_rules(state):
    """The era found so far, for a case that calculates in it: era.of(date) -> (rounding, age rule), era.birth."""
    found, cutoff = state['found'], state['cutoff']
    return SimpleNamespace(birth=found['BIRTH_DATE'], of=lambda date: tuple(
        found[name][1] if date >= cutoff else found[name][0] for name in ('ERA_ROUNDING', 'ERA_AGE')))


def choice_section(case):
    """Rules of a case without targets (t7): each hole's chosen option and the evidence that chose it."""
    notes, assignments = [], []
    for hole, name in case.RULES.items():
        option, reason = case.CHOSEN[hole]
        family = case.SLOTS[hole]
        named = option if isinstance(option, str) else ', '.join(f'{key} {label}' for key, label in option.items())
        notes.append(f"{hole} ({' | '.join(family)}): {named}. Evidence: {reason}.")
        value = {key: family[label] for key, label in option.items()} if isinstance(option, dict) else family[option]
        assignments.append((name, value, case.NOTES.get(hole, '')))
    return Section(case.TITLE, notes, assignments), {hole: option for hole, (option, _) in case.CHOSEN.items()}


def structure_section(case, rows, formula, slots, journal):
    """Notes of a case that explains a record without amounts (t7, NRTAXB): per tax the decision tree of the engine
    on "booked or not", its parts and its agreement; nothing for rules.py to choose."""
    notes, found = [] if rows else ['This extract has no NRTAXB: nothing to explain.'], {}
    for kind in case.STRUCTURE if rows else ():
        depends = getattr(case, 'DEPENDS', {}).get(kind)  # never the tax itself: that would be its own answer
        part = [{**r, 'target': kind in r['booked'],
                 'features': {**r['features'], **({f'{depends} booked': depends in r['booked']} if depends else {})}}
                for r in rows]
        report = discover(f'{case.__name__.split(".")[-1]} {kind}', part, formula, slots, journal, depth=4)
        leaves = [p for p in report if p.get('leaf')]
        agree = sum(p['best']['functions']['booked'](r) == r['target'] for p in leaves for r in p['rows'])
        notes.append(f"{kind}: booked at {sum(r['target'] for r in part):,} of {len(part):,} payouts; the tree agrees "
                     f"with NRTAXB on {agree:,} ({pct(agree / len(part))}):")
        notes += [f"  {p['segment'].removeprefix('all rows / ')}: {p['rule']['booked']} ({p['n']:,} payouts, "
                  f"{pct(p['train'])} of the search rows, {pct(p['test'])} held out)" for p in leaves]
        found[kind] = f'{agree}/{len(part)}'
    return Section(case.TITLE, notes, []), found


def solved(case, args, state, journal):
    """(Section, choice) of one case, by the kind of search it needs."""
    if hasattr(case, 'decide'):  # no targets: the options are chosen by evidence (vocabulary/evidence.py)
        case.CHOSEN = case.decide(str(args.legacy), state['found'])
        if getattr(case, 'REPORT', None):  # counts only: the score on known answers and the misses by group
            lines = ['## Before the search', '', *case.REPORT['before'], '', '## After the search', '', *case.REPORT['after']]
            (Path(args.out) / f"{case.__name__.split('.')[-1]}_report.md").write_text(
                '\n'.join([f'# {case.TITLE}', '', *lines, '']), encoding='utf-8')
        return choice_section(case)
    extra = (era_rules(state),) if getattr(case, 'USES_ERA', False) else ()
    extra = (state['found'],) if getattr(case, 'NEEDS_FOUND', False) else extra
    rows, slots, formula = case.build(str(args.legacy), str(args.targets), *extra)
    if hasattr(case, 'STRUCTURE'):
        return structure_section(case, rows, formula, slots, journal)
    if hasattr(case, 'DESCENT') and hasattr(case, 'ERA_DATES'):
        return era_descent_section(case, rows, formula, slots, state)
    if hasattr(case, 'DESCENT'):
        return descent_section(case, rows, formula, slots)
    if hasattr(case, 'SPLIT'):
        return split_section(case, rows, formula, slots, journal)
    if hasattr(case, 'ERA_DATES'):
        return era_section(case, rows, formula, slots, args, state)
    return plain_section(case, rows, formula, slots)


def split_section(case, rows, formula, slots, journal):
    """Rules of a case whose rule differs by the value of one column: {value: brick} per split hole."""
    report = discover(case.__name__.split('.')[-1], rows, formula, slots, journal, depth=1)
    leaves = [p for p in report if p.get('leaf')]
    if len(leaves) == 1:  # one rule fits every value: the split column is kept, every value gets the same rule
        column = case.COLUMNS[0]
        notes = [f"{len(rows):,} rows; one rule fits every value of {column} ({pct(report[0]['train'])}): no split."]
    else:
        column = report[0]['fails_where']['test'].split(' == ')[0]
        notes = [f"{len(rows):,} rows; no single rule fits ({pct(report[0]['train'])}); the diagnosis splits on {column}."]
    by_value = {}
    for leaf in leaves:
        results, families = ranked(leaf['rows'], formula, slots)
        values = sorted({r['features'][column] for r in (leaf['rows'] if len(leaves) > 1 else rows)})
        segment = f" ({column} {' / '.join(values)})"
        chosen, match, tie_notes = settle(segment, results, families, getattr(case, 'PREFER', {}))
        notes += [f"{column} {' / '.join(values)}: {len(leaf['rows']):,} rows, {exact(match)}.", *tie_notes]
        by_value.update({v: {hole: families[hole][chosen[hole]] for hole in case.RULES} for v in values})
    assignments = []
    for hole, name in case.RULES.items():
        assignments += [(f'{name}_BY', column, 'the column whose value selects the rule'),
                        (name, {v: by_value[v][hole] for v in sorted(by_value)}, case.NOTES.get(hole, ''))]
    return Section(case.TITLE, notes, assignments), {v: {h: b.__name__ for h, b in r.items()} for v, r in by_value.items()}


def check(tasks, legacy, targets):
    """The official check.py on the tasks of the written rules: its score lines and the maintainability index."""
    command = [sys.executable, str(ROOT / 'starter_kit' / 'check.py'), '--submission', str(ROOT / 'my_solution'),
               '--legacy', str(Path(legacy).resolve()), '--targets', str(Path(targets).resolve()), '--tasks', *tasks]
    done = subprocess.run(command, capture_output=True, text=True, cwd=ROOT / 'starter_kit')
    return [line for line in (done.stdout + done.stderr).splitlines() if line.strip() and not line.startswith('  ')]


def demo_report(found, out, seconds):
    """Compare what the demo cases found with the committed rules.py, constant by constant, and print it."""
    import rules
    lines = [f'{name:22s} {"the same as rules.py" if getattr(rules, name, None) == value else "DIFFERS from rules.py"}'
             for name, value in found.items()]
    text = '\n'.join([f'Demo: {len(found)} rules found in {seconds:.0f} s, without any hand-made choice:', *lines])
    print(text)
    (out / 'demo.txt').write_text(text + '\n', encoding='utf-8')


class Gone:
    """A brick of the cached sections that the code no longer has (it was renamed or removed)."""

    def __init__(self, name):
        self.name = name


class Sections(pickle.Unpickler):
    """Unpickles the cached sections; a brick no longer in the code becomes Gone instead of failing."""

    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except AttributeError:
            return Gone(f'{module}.{name}')


def load_sections(only):
    """The sections of the last full search; a case searched again may cite bricks the code no longer has, a kept
    case may not (then a full search is needed)."""
    with SECTIONS.open('rb') as handle:
        kept = Sections(handle).load()
    for name, section in kept.items():
        stale = [v.name for _, v, _ in section.assignments if isinstance(v, Gone)]
        if stale and not name.startswith(tuple(only)):
            sys.exit(f'{name} uses bricks no longer in the code ({", ".join(stale)}): run a full search first')
    return kept


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--legacy', default=ROOT / 'legacy')
    parser.add_argument('--targets', default=ROOT / 'targets')
    parser.add_argument('--out', default=ROOT / 'results' / 'autosolve')
    parser.add_argument('--verify', action='store_true', help='compare rules.py with the search, write nothing')
    parser.add_argument('--cached', action='store_true', help='with --verify: use the last search if no input changed')
    parser.add_argument('--demo', action='store_true', help='run only the DEMO cases and compare them with rules.py')
    parser.add_argument('--only', nargs='+', help='search only the cases named so (e.g. t7); the others come from the '
                        'last full search (.cache/autosolve_sections.pkl), so rules.py is written whole')
    args = parser.parse_args()
    if args.verify and args.cached and (verdict := cached_verdict(args)) is not None:
        print('rules.py checked against the cached search (no input changed)')
        sys.exit(0 if verdict else 'rules.py differs from what the search writes (cached)')
    out, started = Path(args.out), time.time()
    out.mkdir(parents=True, exist_ok=True)
    journal, sections, found, state = Journal(out / 'journal.jsonl'), [], [], {'era': {}, 'args': args}
    kept = load_sections(args.only) if args.only else {}
    if args.only and set(kept) != set(CASES):
        sys.exit('--only needs one full search first (python3 autosolve.py)')
    for name in DEMO if args.demo else CASES:
        t = time.time()
        if args.only and not name.startswith(tuple(args.only)):
            sections.append(kept[name])
            state.setdefault('found', {}).update({n: value for n, value, _ in kept[name].assignments})
            continue
        case = importlib.import_module(f'cases.{name}')
        block, choice = solved(case, args, state, journal)
        sections.append(block)
        state.setdefault('found', {}).update({name: value for name, value, _ in block.assignments})
        found.append(f'| {case.TITLE} | {choice} | {time.time() - t:.0f} s |')
        print(f'{name}: {choice} ({time.time() - t:.0f} s)', flush=True)
    if args.demo:
        return demo_report(state['found'], out, time.time() - started)
    for name in [] if args.only else CASES:  # a case that assumed a rule found later must see that very rule found
        for rule, brick in getattr(importlib.import_module(f'cases.{name}'), 'ASSUMES', {}).items():
            if state['found'].get(rule) is not brick:
                sys.exit(f'{name} assumed {rule} = {brick.__name__}, the search found {state["found"].get(rule)}: run again')
    text = rules_text(sections)
    changed = not RULES.exists() or RULES.read_text(encoding='utf-8') != text
    if args.only:
        if not args.verify:
            RULES.write_text(text, encoding='utf-8')
        print(f"rules.py {'written anew' if changed else 'unchanged'} ({', '.join(args.only)} searched, the rest kept)")
        return
    CACHE.parent.mkdir(exist_ok=True)
    SECTIONS.write_bytes(pickle.dumps(dict(zip(CASES, sections))))
    CACHE.write_text(json.dumps({'fingerprint': fingerprint(args), 'rules': hashlib.sha256(text.encode()).hexdigest()}),
                     encoding='utf-8')
    if args.verify:
        sys.exit('rules.py differs from what the search writes' if changed else 0)
    RULES.write_text(text, encoding='utf-8')
    tasks = {getattr(importlib.import_module(f'cases.{n}'), 'TASK', None) for n in CASES} - {None}  # check.py has no t7
    scores = check(sorted(tasks), args.legacy, args.targets)
    print('\n'.join(scores))
    (out / 'report.md').write_text('\n'.join([
        '# autosolve report', '', f"Run {time.strftime('%Y-%m-%d %H:%M')}, {time.time() - started:.0f} s; "
        f"my_solution/rules.py {'written anew' if changed else 'unchanged (the same bytes as before)'}.", '',
        '| Case | Rules found (per era or per value) | Search time |', '|---|---|---|', *found, '',
        'Official check.py on the targets of the written rules:', '', '```', *scores, '```', '']), encoding='utf-8')


if __name__ == '__main__':
    main()
