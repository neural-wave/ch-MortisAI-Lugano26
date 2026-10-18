"""Quality gate of the Neuron solution: accuracy per task, maintainability, run time, purity.

    .venv/bin/python tools/quality_gate.py                       # all tasks, compared with the baseline
    .venv/bin/python tools/quality_gate.py --tasks t0_commission t5_outlier_detection
    .venv/bin/python tools/quality_gate.py --save-baseline       # this run becomes the baseline

Runs the official starter_kit/check.py on my_solution with the interpreter of this script (it needs radon
for the maintainability index), the vocabulary self-tests and a static purity check of my_solution.
Every run is appended to logs/quality.jsonl; the raw output of check.py is in logs/quality_last.txt.
The exit code is 1 if a gate fails.

Gates, each against tools/quality_baseline.json:
- accuracy: per task, no fewer exact rows than the baseline;
- t5: the same number of flagged outliers (a change has to be looked at before it is accepted);
- maintainability: not below the baseline index;
- time: the sum of the task times at most 20 % above the baseline (only when all tasks run, because
  t4 and t5 reuse the replay of t3 within one run);
- tests: vocabulary/tests/run_tests.py and tests/*.py pass, and rules.py is what autosolve writes (from its cache
  unless --full, which runs the whole search: required before a merge to main);
- no target value in a tracked file (tools/target_leaks.py: code, docs, reports, prompts);
- skipped policies: no train policy skipped by guard.per_policy (named on stderr; public ones are reported);
- purity: my_solution imports the standard library only (or what requirements.txt lists), no network or
  processes, no float, no policy numbers, and only t5 touches the target files.
"""
import argparse
import ast
import datetime as dt
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT, SOLUTION, LOGS = ROOT / 'starter_kit', ROOT / 'my_solution', ROOT / 'logs'
BASELINE = ROOT / 'tools' / 'quality_baseline.json'
TIME_MARGIN = 1.2  # run time may grow by 20 %
MAX_FILES = 100  # the upload limit of the leaderboard

# Lines printed by check.py (its format is official and does not change).
TASK_LINE = re.compile(r'^(t\d_\w+)\s+(\d+) /\s+(\d+) =\s+[\d.]+%\s+([\d.]+)s$')
T5_LINE = re.compile(r'^t5_outlier_detection\s+(\d+) outliers\s+([\d.]+)s\s+(\{.*\})$')
MI_LINE = re.compile(r'^maintainability index: ([\d.]+)')
FILE_LINE = re.compile(r'^  (\S+\.py)\s+([\d.]+)$')
SKIP_LINE = re.compile(r'^(.+?): skipped policy (\S+) \((.*)\)$', re.M)  # printed by my_solution/guard.py
TESTS = {'vocabulary self-tests': 'vocabulary/tests/run_tests.py',
         'robustness of my_solution': 'tests/test_skipped_policies.py',
         'charge split': 'tests/test_charges.py',
         'rules.py generator': 'tests/test_autosolve.py',
         't7 examples and rows': 'tests/test_t7.py',
         'era from the extract': 'tests/test_eras.py',
         'rules.py = search result': 'autosolve.py --verify --cached --out .cache/autosolve-verify',
         'no target value in git': 'tools/target_leaks.py'}

# Purity: modules that reach the network or other programs, and the shape of a policy number.
FORBIDDEN = {'urllib', 'http', 'socket', 'ssl', 'ftplib', 'smtplib', 'xmlrpc', 'subprocess', 'requests', 'httpx'}
POLICY_ID = re.compile(r'\b[A-Z]{2}\d{8}\b')
T5_MODULES, T5_FUNCTION = 'outliers', 't5_outlier_detection'  # the only code allowed to read targets


def parse(output):
    """The numbers printed by check.py: exact rows and seconds per task, t5 flags, maintainability."""
    run = {'tasks': {}, 't5': None, 'mi': None, 'mi_files': {}}
    for line in output.splitlines():
        if match := TASK_LINE.match(line):
            name, correct, total, seconds = match.groups()
            run['tasks'][name] = {'correct': int(correct), 'total': int(total), 'seconds': float(seconds)}
        elif match := T5_LINE.match(line):
            run['t5'] = {'count': int(match[1]), 'seconds': float(match[2]), 'per_task': ast.literal_eval(match[3])}
        elif match := MI_LINE.match(line):
            run['mi'] = float(match[1])
        elif match := FILE_LINE.match(line):
            run['mi_files'][match[1]] = float(match[2])
    return run


def run_check(tasks, legacy, targets):
    """Run the official check.py once; its parsed numbers plus the wall time of the whole run."""
    command = [sys.executable, str(KIT / 'check.py'), '--submission', str(SOLUTION),
               '--legacy', str(legacy), '--targets', str(targets), *(['--tasks', *tasks] if tasks else [])]
    started = time.time()
    done = subprocess.run(command, capture_output=True, text=True, cwd=KIT)
    (LOGS / 'quality_last.txt').write_text(done.stdout + done.stderr, encoding='utf-8')
    if done.returncode:
        sys.exit(f'check.py failed with exit code {done.returncode}, see logs/quality_last.txt')
    return {**parse(done.stdout), 'skipped': skipped(done.stderr, targets),
            'wall_seconds': round(time.time() - started, 1)}


def train_policies(targets):
    """The policy ids of the scored target files: the train policies."""
    ids = set()
    for path in Path(targets).glob('t[0-4]_*.csv'):
        with open(path, encoding='utf-8') as handle:
            ids |= {line.split(',', 1)[0] for line in handle}
    return ids


def skipped(stderr, targets):
    """The policies guard.per_policy skipped in this run, split into train and public ones."""
    pids, train = {match[2] for match in SKIP_LINE.finditer(stderr)}, train_policies(targets)
    return {'train': sorted(pids & train), 'public': sorted(pids - train)}


def tests():
    """{test name: passed or not, and its last line} for the test scripts in TESTS."""
    results = {}
    for name, script in TESTS.items():
        script, *options = script.split()
        done = subprocess.run([sys.executable, str(ROOT / script), *options], capture_output=True, text=True, cwd=ROOT)
        lines = (done.stdout + done.stderr).strip().splitlines()
        results[name] = {'ok': done.returncode == 0, 'summary': lines[-1] if lines else 'no output'}
    return results


def requirements():
    """Top-level package names listed in my_solution/requirements.txt (comments and versions dropped)."""
    path = SOLUTION / 'requirements.txt'
    lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
    names = (re.split(r'[\s<>=!~\[;#]', line.strip(), maxsplit=1)[0] for line in lines)
    return {name.lower().replace('-', '_') for name in names if name}


def docstrings(tree):
    """The string constants that are docstrings: examples in them are documentation, not data."""
    owners = [n for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef))]
    return {id(n.body[0].value) for n in owners
            if n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)
            and isinstance(n.body[0].value.value, str)}


class Purity(ast.NodeVisitor):
    """The purity findings of one module of my_solution, as (line, text)."""

    def __init__(self, tree, module, known):
        self.found, self.known, self.skip = [], known, docstrings(tree)
        self.in_t5 = module.startswith(T5_MODULES)
        self.visit(tree)

    def add(self, node, text):
        self.found.append((node.lineno, text))

    def imported(self, node, name):
        top = name.split('.')[0]
        if top in FORBIDDEN:
            self.add(node, f'imports {top}: no network or other programs')
        elif top not in sys.stdlib_module_names and top not in self.known:
            self.add(node, f'imports {top}: not in the standard library nor in requirements.txt')

    def visit_Import(self, node):
        for alias in node.names:
            self.imported(node, alias.name)

    def visit_ImportFrom(self, node):
        if node.level == 0:
            self.imported(node, node.module)

    def visit_FunctionDef(self, node):
        outer, self.in_t5 = self.in_t5, self.in_t5 or node.name == T5_FUNCTION
        self.generic_visit(node)
        self.in_t5 = outer

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'float':
            self.add(node, 'calls float(): money stays Decimal')
        self.generic_visit(node)

    def named(self, node, name):
        if 'target' in name.lower() and not self.in_t5:
            self.add(node, f'{name}: only t5 may use the target files')

    def visit_Name(self, node):
        self.named(node, node.id)

    def visit_arg(self, node):
        self.named(node, node.arg)

    def visit_Constant(self, node):
        if isinstance(node.value, float):
            self.add(node, f'float literal {node.value!r}: money stays Decimal')
        elif isinstance(node.value, str) and id(node) not in self.skip:
            if POLICY_ID.search(node.value):
                self.add(node, f'policy number in a string: {node.value!r}')
            self.named(node, node.value)


def purity():
    """All purity findings of my_solution as 'file:line: text'."""
    files = sorted(SOLUTION.rglob('*.py'))
    known = {p.stem for p in files} | requirements()
    found = []
    for path in files:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        found += [f'{path.relative_to(SOLUTION)}:{line}: {text}'
                  for line, text in Purity(tree, path.stem, known).found]
    return found


def commit():
    """The commit measured, marked '+changes' if my_solution differs from it."""
    head = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, cwd=ROOT)
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'my_solution'],
                           capture_output=True, text=True, cwd=ROOT)
    return head.stdout.strip() + ('+changes' if dirty.stdout.strip() else '')


def verdict(ok):
    return 'PASS' if ok else 'FAIL'


def gates(run, base, all_tasks):
    """[(gate, value now, baseline, status)] for the table and the log."""
    rows = []
    for name, now in run['tasks'].items():
        was = base['tasks'].get(name, now)
        rows.append((name, f"{now['correct']} / {now['total']} = {now['correct'] / now['total']:.4%}",
                     f"{now['correct'] - was['correct']:+d} rows", verdict(now['correct'] >= was['correct'])))
    if run['t5'] and base.get('t5'):
        change = run['t5']['count'] - base['t5']['count']
        rows.append(('t5 outliers', f"{run['t5']['count']} flags {run['t5']['per_task']}", f'{change:+d} flags',
                     verdict(change == 0)))
    rows.append(('maintainability', f"{run['mi']}", f"{(run['mi'] or 0) - base['mi']:+.1f}",
                 verdict(run['mi'] is not None and run['mi'] >= base['mi'])))
    if all_tasks:
        limit = base['task_seconds'] * TIME_MARGIN
        rows.append(('time of all tasks', f"{run['task_seconds']} s (wall {run['wall_seconds']} s)",
                     f"limit {limit:.1f} s", verdict(run['task_seconds'] <= limit)))
    lost = run['skipped']
    rows.append(('skipped policies', f"train {len(lost['train'])}, public {len(lost['public'])}", '',
                 verdict(not lost['train'])))
    rows += [(name, test['summary'], '', verdict(test['ok'])) for name, test in run['tests'].items()]
    rows.append(('purity of my_solution', f"{len(run['purity'])} findings", '', verdict(not run['purity'])))
    files = len([p for p in SOLUTION.iterdir() if p.name != '__pycache__'])
    rows.append(('files of my_solution', f'{files}', f'limit {MAX_FILES} (upload)', verdict(files <= MAX_FILES)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--tasks', nargs='*', help='tasks to check (default: all, including t5)')
    parser.add_argument('--legacy', default=ROOT / 'legacy')
    parser.add_argument('--targets', default=ROOT / 'targets')
    parser.add_argument('--label', default='', help='a note for the log, e.g. the step being checked')
    parser.add_argument('--save-baseline', action='store_true', help='store this run as the baseline')
    parser.add_argument('--full', action='store_true', help='check rules.py against a new search (before a merge to main)')
    args = parser.parse_args()
    LOGS.mkdir(exist_ok=True)
    run = run_check(args.tasks, args.legacy, args.targets)
    run['task_seconds'] = round(sum(t['seconds'] for t in run['tasks'].values())
                                + (run['t5']['seconds'] if run['t5'] else 0), 1)
    if args.full:
        TESTS['rules.py = search result'] = TESTS['rules.py = search result'].replace(' --cached', '')
    run.update(tests=tests(), purity=purity(), commit=commit(), label=args.label,
               when=dt.datetime.now().isoformat(timespec='seconds'), python=platform.python_version())
    if args.save_baseline:
        BASELINE.write_text(json.dumps(run, indent=1) + '\n', encoding='utf-8')
    base = json.loads(BASELINE.read_text(encoding='utf-8'))
    rows = gates(run, base, all_tasks=not args.tasks)
    run['gates'] = {gate: status for gate, _, _, status in rows}
    with open(LOGS / 'quality.jsonl', 'a', encoding='utf-8') as log:
        log.write(json.dumps(run) + '\n')
    print(f"quality gate at {run['commit']} against the baseline of {base['commit']} ({base['label']})")
    for gate, now, change, status in rows:
        print(f'  {status:4s}  {gate:28s} {now:60s} {change}')
    for finding in run['purity']:
        print(f'        purity: {finding}')
    failed = [gate for gate, _, _, status in rows if status == 'FAIL']
    print('FAILED: ' + ', '.join(failed) if failed else 'all gates passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
