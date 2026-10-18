"""No value of targets/ in the repository:   .venv/bin/python tools/target_leaks.py

The targets of the train policies may be read by the search and by t5, but no value of them may be written into a
tracked file (code, docs, reports of the search, prompts sent to a model). A value counts as leaked when a line
names a policy and holds one of that policy's target values, or when a target value follows the word "expected"
(a row of a report or of a prompt). Two passes: the tracked files give the few candidates, then the target files
are streamed once (t3_booking has five million rows). Pictures are not read: tools/figures.py draws our values.
The known answers of t7 (targets_t7/sample_*, the leaderboard's samples) are scanned the same way, and more strictly
for the solution: no policy of a sample may be named anywhere in my_solution/ (rules.py included, tracked or not);
such a finding names only the place, never the row.
Exit code 1 and one line per finding if anything leaked.
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = re.compile(r'BL\d{8}')
VALUE = re.compile(r'\d{4}-\d{2}-\d{2}|-?\d+\.\d+')
EXPECTED = re.compile(r'expected\W+([^a-z]*)')  # the values right after "expected", up to the next word
KEYS = {'policy_id', 'booking_id', 'n', 'due_nr', 'year', 'policy_year', 'fund_id', 'pot', 'booking_type',
        'valuation_date', 'event_nr'}  # columns that identify a row; the others are target values


def tracked_lines():
    """(file, line number, text) of every tracked text file but pictures."""
    files = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    for name in files:
        path = ROOT / name
        if path.suffix in ('.png', '.pdf') or not path.is_file():
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            yield name, number, line


def candidates():
    """{(policy, value): [places]} of values next to a policy number, {value: [places]} of values after 'expected'."""
    paired, after = {}, {}
    for name, number, line in tracked_lines():
        place = f'{name}:{number}'
        for policy in set(POLICY.findall(line)):
            for value in set(VALUE.findall(line)):
                paired.setdefault((policy, value), []).append(place)
        for match in EXPECTED.finditer(line):
            for value in VALUE.findall(match.group(1)):
                after.setdefault(value, []).append(place)
    return paired, after


def leaks(targets):
    """'file:line: value' of every candidate that is a target value."""
    paired, after = candidates()
    found = set()
    for path in sorted(Path(targets).glob('*.csv')):
        with open(path, encoding='utf-8') as handle:
            for row in csv.DictReader(handle):
                for column, value in row.items():
                    if column in KEYS or not value.strip('0.-'):
                        continue
                    for place in paired.get((row['policy_id'], value), []) + after.get(value, []):
                        found.add(f'{place}: {value} ({path.stem} {row["policy_id"]})')
    return sorted(found)


def sample_policies():
    """The policies of the rows of targets_t7/sample_*."""
    found = set()
    for path in sorted((ROOT / 'targets_t7').glob('sample_*/*.csv')):
        with open(path, encoding='utf-8') as handle:
            found |= {row['policy_id'] for row in csv.DictReader(handle)}
    return found


def in_solution(policies):
    """'file:line' of every line of my_solution/ that names a policy of the samples."""
    found = []
    for path in sorted((ROOT / 'my_solution').glob('*.py')):
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if set(POLICY.findall(line)) & policies:
                found.append(f'my_solution/{path.name}:{number}: a policy of targets_t7')
    return found


def main():
    folders = [Path(sys.argv[1])] if len(sys.argv) > 1 else [ROOT / 'targets', *sorted((ROOT / 'targets_t7').glob('sample_*'))]
    found = [f for folder in folders for f in leaks(folder)] + in_solution(sample_policies())
    print('\n'.join(found) if found else 'no target value in the tracked files')
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
