"""t6: figures that make the hidden rules of Neuron visible.   .venv/bin/python tools/figures.py [names...]

Each figure shows one rule the search found, with the data that decides it; they go to figures/*.png and
figures/README.md explains them. Tooling only: matplotlib is used here, never in my_solution (standard library).
Reads legacy/ and the train targets. A figure shows values of our calculation or shares and counts of the
comparison with the targets, never a target value itself (tools/target_leaks.py).
"""
import csv
import datetime as dt
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal as D
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'vocabulary'), str(ROOT / 'my_solution')]
LEGACY, TARGETS, OUT = str(ROOT / 'legacy'), str(ROOT / 'targets'), ROOT / 'figures'
EXTRACT = dt.date(2026, 6, 30)
COBOL, NG, GREY, RED = '#8c6d31', '#1f6fb4', '#9a9a9a', '#c0392b'
plt.rcParams.update({'figure.dpi': 150, 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titlesize': 10, 'axes.titleweight': 'bold'})


def read(name):
    with open(Path(TARGETS) / f'{name}.csv', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f'{name}.png')
    plt.close(fig)
    print('figures/' + name + '.png')


def offers():
    """The t2 offers of years 1 and 2 (the era case) and the rules found."""
    import rules
    from cases import era
    rows, _, formula = era.build(LEGACY, TARGETS)
    return rows, formula, rules


def era_change():
    """(a) Share of exact offers by application half-year under the COBOL and the Neuron NG rules."""
    rows, formula, rules = offers()
    hits = defaultdict(lambda: [0, 0, 0])
    for row in rows:
        when = row['features']['application date']
        half = dt.date(when.year, 1 if when.month < 7 else 7, 1)
        for i in (0, 1):
            c = {'rounding': rules.ERA_ROUNDING[i], 'entry age': rules.ERA_AGE[i], 'birth date': rules.BIRTH_DATE}
            hits[half][i] += formula(row, c) == row['target']
        hits[half][2] += 1
    halves = sorted(hits)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    for i, (label, colour) in enumerate((('COBOL rules (truncate, age = days / 365)', COBOL),
                                         ('Neuron NG rules (half up, nearest birthday)', NG))):
        ax.plot(halves, [100 * hits[h][i] / hits[h][2] for h in halves], marker='o', ms=3, color=colour, label=label)
    ax.axvline(rules.ERA_CUTOFF, color=RED, lw=1, ls='--')
    ax.text(rules.ERA_CUTOFF, 50, f'  {rules.ERA_CUTOFF}: the day of all\n  946 events 800 (system conversion)',
            color=RED, va='center')
    ax.set_ylabel('offers matched exactly, %')
    ax.set_ylim(0, 105)
    ax.set_title('The rules change on the application date 2007-08-11\n(offer values of policy years 1 and 2, t2, '
                 'share matched exactly per half-year of application)')
    ax.legend(loc='lower left', frameon=False)
    save(fig, 'a_era_change_point')


def next_birthday(birth, start):
    """Days from the start date to the next birthday (a 29 February counts on 28 February)."""
    for year in (start.year, start.year + 1):
        day = dt.date(year, birth.month, min(birth.day, 28 if birth.month == 2 else 31))
        if day >= start:
            return (day - start).days
    return 0


def birthday():
    """(b) Misses of the 'last birthday' age against the days from the start to the next birthday."""
    from conventions import AGES
    rows, formula, rules = offers()
    late = [r for r in rows if r['features']['application date'] >= rules.ERA_CUTOFF]
    bins = defaultdict(lambda: [0, 0, 0])
    for row in late:
        birth = rules.BIRTH_DATE(row['person']['PS_BIRTH'])
        days = next_birthday(birth, row['start']) // 15 * 15
        for i, age in enumerate((AGES['last birthday'], AGES['nearest birthday'])):
            c = {'rounding': rules.ERA_ROUNDING[1], 'entry age': age, 'birth date': rules.BIRTH_DATE}
            bins[days][i] += formula(row, c) != row['target']
        bins[days][2] += 1
    x = sorted(bins)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.bar([d + 7 for d in x], [100 * bins[d][0] / bins[d][2] for d in x], width=13, color=GREY,
           label='age = completed years (last birthday)')
    ax.plot([d + 7 for d in x], [100 * bins[d][1] / bins[d][2] for d in x], color=NG, marker='o', ms=3,
            label='age = nearest birthday (the rule found)')
    ax.axvline(182.5, color=RED, lw=1, ls='--')
    ax.text(186, 92, 'half a year', color=RED)
    ax.set_xlabel('days from the start date to the next birthday')
    ax.set_ylabel('offers missed, %')
    ax.set_title(f'Neuron NG rounds the entry age to the nearest birthday ({len(late):,} offers from 2007-08-11)')
    ax.legend(frameon=False, loc='center right')
    save(fig, 'b_entry_age_birthday')


def collection_calendar():
    """(c) Calendar of the shift from due date to collection date of the direct debits (LS), as we calculate
    it (it matches all 15,028 train dates)."""
    import submission
    from tables import grouped, version
    from conventions_holidays import holidays, TICINO, EASTER_TICINO
    policies = grouped(LEGACY, 'NRPOLH', 'PH_POLNR')
    shift = defaultdict(int)
    for (pid, _), (due, collection) in submission.t1_next_due_dates(LEGACY, EXTRACT).items():
        if version(policies[pid], EXTRACT, 'PH')['PH_PAYMT'] == 'LS':
            shift[due] = max(shift[due], (collection - due).days)
    first = dt.date(2026, 6, 29)  # the Monday of the week of the extract date
    free = holidays(2026, TICINO, EASTER_TICINO) | holidays(2027, TICINO, EASTER_TICINO)
    fig, ax = plt.subplots(figsize=(10, 2.6))
    colours = {0: '#d9ead3', 1: '#f6c26b', 2: '#e69138', 3: '#b45f06', 4: '#783f04'}
    for i in range(7 * 53):
        when = first + dt.timedelta(i)
        week, weekday = i // 7, when.weekday()
        colour = colours.get(shift.get(when), '#f3f3f3') if when in shift else 'white'
        ax.add_patch(plt.Rectangle((week, 6 - weekday), 0.92, 0.92, color=colour, lw=0))
        if when in free and weekday < 5:
            ax.text(week + 0.46, 6.46 - weekday, 'H', ha='center', va='center', fontsize=6, weight='bold')
        if when.day == 1:
            ax.text(week, 7.3, when.strftime('%b %Y' if when.month in (7, 1) else '%b'), fontsize=7)
    ax.set_xlim(0, 53)
    ax.set_ylim(0, 8)
    ax.set_yticks([6.46 - k for k in range(7)], ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], fontsize=7)
    ax.set_xticks([])
    for side in ('left', 'bottom'):
        ax.spines[side].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colours.values()]
    ax.legend(handles, [f'+{k} days' for k in colours], ncol=5, frameon=False, loc='upper center',
              bbox_to_anchor=(0.5, -0.02), fontsize=7)
    ax.set_title('t1: a direct debit (LS) is collected on the next business day of Ticino\n'
                 '(colour: days from due date to collection; H: a Ticino holiday, with Easter Monday, Ascension, '
                 'Whit Monday, Corpus Christi)', fontsize=8)
    save(fig, 'c_collection_calendar')


def statement_example():
    """A public policy (no target: its values cannot be target values) with every kind of charge in 2015 and a
    start before the system change: (policy, year, our statement row)."""
    import submission
    from tables import grouped, day
    train = {r['policy_id'] for r in read('t4_annual_statement')}
    policies = grouped(LEGACY, 'NRPOLH', 'PH_POLNR')
    for (pid, year), row in sorted(submission.t4_annual_statement(LEGACY).items()):
        start = min(day(v['PH_BEGDT']) for v in policies[pid])
        if pid not in train and year == 2015 and all(row[:5]) and start < dt.date(2007, 8, 11):
            return pid, year, row


def waterfall():
    """(d) Waterfall of one annual statement (t4) as we calculate it: the premiums less each charge."""
    pid, year, ours = statement_example()
    steps = [('premiums', ours[0])] + [(name, -amount) for name, amount in zip(
        ('entry charges', 'admin fees', 'management', 'risk charges'), ours[1:5])]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    level = D(0)
    for i, (name, amount) in enumerate(steps):
        bottom = level if amount > 0 else level + amount
        ax.bar(i, abs(amount), bottom=bottom, color=NG if amount > 0 else RED, width=0.6)
        ax.text(i, level + max(amount, D(0)) + 15, f'{amount:+,.2f}', ha='center', fontsize=8)
        level += amount
    ax.bar(len(steps), level, color=GREY, width=0.6)
    ax.text(len(steps), level + 15, f'{level:,.2f}', ha='center', fontsize=8)
    ax.set_xticks(range(len(steps) + 1), [name for name, _ in steps] + ['premiums less\ncharges'])
    ax.set_title(f'Annual statement of {pid}, {year} (t4), as we calculate it\n'
                 f'(a public policy: no target; on train all six columns match in 99.94 % of the rows)')
    ax.set_ylabel('CHF')
    save(fig, 'd_statement_waterfall')


def recording(charges, units):
    """Let every Ledger note its charges by date and its units on every valuation; returns the original methods."""
    from ledger import Ledger
    cancel, value = Ledger.cancel, Ledger.value

    def noted_cancel(ledger, date, kind, amounts):
        charges[date] += sum(amounts.values(), D(0))
        return cancel(ledger, date, kind, amounts)

    def noted_value(ledger, date):
        units[date] = sum(ledger.units.values(), D(0))
        return value(ledger, date)
    Ledger.cancel, Ledger.value = noted_cancel, noted_value
    return cancel, value


def timeline():
    """(e) One policy over its life, as our replay calculates it: premiums, monthly charges, units and value."""
    from tables import received, day, scaled
    from accounts_replay import replay
    from orders import customer_orders
    from ledger import Ledger
    pid = statement_example()[0]
    premiums = [p for p in received(LEGACY) if p['PR_POLNR'] == pid]
    months, when = [], min(day(p['PR_RCVDT']) for p in premiums)
    while when <= EXTRACT:
        months.append(when)
        when = (when.replace(day=1) + dt.timedelta(32)).replace(day=1)
    charges, held = defaultdict(D), {}
    original = recording(charges, held)
    _, values = replay(LEGACY, pid, premiums, customer_orders(LEGACY)[pid], months)
    Ledger.cancel, Ledger.value = original
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True, height_ratios=(2, 1))
    top.plot(sorted(values), [values[d] for d in sorted(values)], color=NG, label='policy value (blue), units held (brown)')
    top.set_ylabel('CHF')
    top.set_title(f'{pid} (a public policy) as our replay calculates it:\npremiums buy units, charges cancel '
                  f'units every month, the value follows the prices')
    units = top.twinx()
    units.plot(sorted(held), [held[d] for d in sorted(held)], color=COBOL, lw=1)
    units.set_ylabel('units held', color=COBOL)
    units.spines['top'].set_visible(False)
    top.axvline(dt.date(2007, 8, 11), color=RED, lw=0.8, ls='--')
    top.legend(loc='upper left', frameon=False)
    bottom.bar([day(p['PR_RCVDT']) for p in premiums], [scaled(p['PR_AMTRC'], 2) for p in premiums], width=20,
               color=NG, label='premium received')
    bottom.bar(sorted(charges), [-charges[d] for d in sorted(charges)], width=20, color=RED,
               label='monthly charges (admin, management, risk)')
    bottom.set_ylabel('CHF')
    bottom.legend(loc='lower left', frameon=False, ncol=2, fontsize=7)
    save(fig, 'e_policy_timeline')


def differences():
    """(f) Our values against the targets: exact, or off by how many cents (days for t1)."""
    import submission
    ours = {
        't0': (submission.t0_commission(LEGACY), {(r['policy_id'], int(r['due_nr'])): D(r['amount'])
                                                    for r in read('t0_commission')}),
        't2': (submission.t2_projected_maturity_value(LEGACY), {r['policy_id']: D(r['maturity_value'])
                                                                 for r in read('t2_projected_maturity_value')}),
    }
    surrender = read('t3_surrender_value')
    dates = sorted({dt.date.fromisoformat(r['valuation_date']) for r in surrender})
    ours['t3'] = (submission.t3_surrender_value(LEGACY, dates), {
        (r['policy_id'], dt.date.fromisoformat(r['valuation_date'])): D(r['surrender_value']) for r in surrender})
    ours['t4'] = ({k: v[5] for k, v in submission.t4_annual_statement(LEGACY).items()}, {
        (r['policy_id'], int(r['year'])): D(r['total_charges']) for r in read('t4_annual_statement')})
    bins = ['exact', '1 cent', '2–9 cents', '10–99 cents', '1–99 CHF', '100 CHF or more', 'missing']
    fig, ax = plt.subplots(figsize=(8, 3.2))
    width = 0.2
    for i, (task, (got, expected)) in enumerate(ours.items()):
        counts = Counter()
        for key, value in expected.items():
            if key not in got:
                counts['missing'] += 1
                continue
            cents = abs(got[key] - value) * 100
            counts[next(b for b, limit in zip(bins, (0, 1, 9, 99, 9999, 10 ** 12)) if cents <= limit)] += 1
        ax.bar([k + (i - 1.5) * width for k in range(len(bins))], [counts[b] for b in bins], width, label=task)
        for k, b in enumerate(bins):
            if counts[b] and b != 'exact':
                ax.text(k + (i - 1.5) * width, counts[b] * 1.15, str(counts[b]), ha='center', fontsize=6)
    ax.set_yscale('log')
    ax.set_xticks(range(len(bins)), bins)
    ax.set_ylabel('train values (log scale)')
    ax.set_title('The misses are no rounding noise: no value is a cent off; the rest are manual corrections (t5)')
    ax.legend(frameon=False, ncol=4)
    save(fig, 'f_cent_differences')


def llm_ablations():
    """(g) Ablations: a brick removed from the dictionary, and what the model brought back."""
    found = {}
    for line in open(ROOT / 'vocabulary' / 'results_llm_step10' / 'journal.jsonl', encoding='utf-8'):
        entry = json.loads(line)
        if entry['step'].endswith('proposals for collection') or entry['step'].endswith('proposals for entry age'):
            numbers = entry['note'].split('exact rows (search, held out) ')[1]
            before, after = (sum(map(int, part.strip(' ()').split(', '))) for part in numbers.split('->'))
            found[entry['case']] = (before, after, entry['note'].startswith('kept'))
    labels = {'ablation_t1_no_easter_holidays': ('t1 collection\nwithout the Easter holidays', 15028),
              'ablation_era_age': ('offers (era)\nwithout the COBOL age rule', 3019)}
    fig, ax = plt.subplots(figsize=(7, 3))
    for i, (case, (label, n)) in enumerate(labels.items()):
        before, after, kept = found[case]
        ax.bar(i - 0.18, 100 * before / n, 0.34, color=GREY,
               label='the dictionary without the brick (best rules, after splits)' if i == 0 else None)
        ax.bar(i + 0.18, 100 * after / n, 0.34, color=NG, label='+ one brick written by Qwen 27B' if i == 0 else None)
        ax.text(i - 0.18, 100 * before / n + 0.05, f'{100 * before / n:.2f} %', ha='center', fontsize=8)
        ax.text(i + 0.18, 100 * after / n + 0.05, f'{100 * after / n:.2f} %', ha='center', fontsize=8)
    ax.set_ylim(99, 100.6)
    ax.set_xticks(range(len(labels)), [label for label, _ in labels.values()])
    ax.set_ylabel('rows matched exactly, %')
    ax.set_title('A language model finds a removed rule again\n(the engine keeps a brick only if no row gets worse)')
    ax.legend(frameon=False, loc='upper center', ncol=2, fontsize=7)
    save(fig, 'g_llm_ablations')


def tax_rates():
    """(h) The tax rates of NRTAXR by country and tax type over time (the version valid on each day, as entered last)."""
    from tables import table, day
    rows = defaultdict(list)
    for r in table(LEGACY, 'NRTAXR'):
        rows[f"{r['TX_CNTRY']} {r['TX_TAXTP']}{' ' + r['TX_REGIO'] if r['TX_REGIO'] else ''}"].append(r)
    fig, ax = plt.subplots(figsize=(9, 4))
    end = dt.date(2026, 6, 30)
    for name, items in sorted(rows.items()):
        if name.split()[1] in ('HEV', 'TFS'):
            continue  # shares of the gain, not rates of a tax
        points = []
        for r in sorted(items, key=lambda r: (r['TX_VLDFR'], int(r['TX_VRSNR']))):
            start, stop = day(r['TX_VLDFR']), min(day(r['TX_VLDTO']) or end, end)
            points += [(start, 100 * int(r['TX_RATE']) / 10 ** 6), (stop, 100 * int(r['TX_RATE']) / 10 ** 6)]
        ax.step([d for d, _ in points], [v for _, v in points], where='post', label=name)
    ax.set_yscale('log')
    ax.set_ylabel('rate, % (log scale)')
    ax.set_title('t7: the tax rates of NRTAXR by country and tax type over time\n(versions as entered last; '
                 'the bitemporal history is what Neuron knew when it booked)')
    ax.legend(frameon=False, fontsize=6, ncol=3, loc='lower right')
    save(fig, 'h_tax_rates')


def t7_uploads():
    """(i) The t7 scores of the uploads, by sample (the leaderboard log)."""
    log = json.loads((ROOT / 'logs' / 't7_evidence.json').read_text())['submissions']
    full = [s for s in log if s.get('payout') and not s.get('diagnostic')]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    for table, colour in (('payout', NG), ('annual', COBOL)):
        ax.plot([s['n'] for s in full], [100 * s[table][0] / s[table][1] for s in full], marker='o', color=colour,
                label=table)
    for s in full:
        ax.text(s['n'], 100 * s['payout'][0] / s['payout'][1] + 3, f"{s['payout'][0]}/{s['payout'][1]}", ha='center', fontsize=7)
    change = max(s['n'] for s in full if s['sample'] == 'A') + 0.5
    ax.axvline(change, color=GREY, ls='--', lw=0.8)
    ax.text(change + 0.05, 5, 'new sample', color=GREY, fontsize=7)
    ax.set_xticks([s['n'] for s in full], ['v22' if s['n'] == 0 else str(s['n']) for s in full])
    ax.set_xlabel('upload')
    ax.set_ylabel('rows right, %')
    ax.set_ylim(0, 100)
    ax.set_title('t7 on the leaderboard: the empty date (2), the tax net of the penalty (3)')
    ax.legend(frameon=False, loc='upper left')
    save(fig, 'i_t7_uploads')


FIGURES = {'a': era_change, 'b': birthday, 'c': collection_calendar, 'd': waterfall, 'e': timeline,
           'f': differences, 'g': llm_ablations, 'h': tax_rates, 'i': t7_uploads}

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for name in sys.argv[1:] or FIGURES:
        FIGURES[name]()
