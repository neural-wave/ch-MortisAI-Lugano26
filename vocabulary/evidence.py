"""Choosing among the options of a hole when the answers are hidden: by evidence, from the strongest to the weakest.

t7 has no local targets. Each option of each hole is measured with the other holes at the options of the best confirmed
build (the incumbent), and the evidence decides level by level; a level keeps only the options it prefers and the next
level looks at what is left:

    (a) checks       hard facts no answer can break: the examples of the task to the cent, amounts in whole cents
    (t) targets      the exact rows on each sample of known answers: an option replaces the current one only if it is
                     no worse on every sample (found on one sample, held on the other), then the most rows in all
    (b) bookings     the record of what Neuron did without amounts (NRTAXB): fewer contradictions are better
    (c) consistency  the answers agree with each other (the yearly table holds the taxes of the payouts)
    (d) leaderboard  on one sample of the evaluation a higher score is better; samples are never compared with each
                     other; the latest sample that tried at least two of the options left decides
    (d') incumbent   an option no sample could compare stays as the best confirmed build has it: its score is known
    (e) tie          the case's stated meaning, else the first option of the family (Neuron's, the simplest)

Every choice gets its reason: the level that decided and what it dropped.
"""


def flatten(config):
    """A build's choices with a choice per value ({hole: {key: option}}) spread into holes 'hole key'."""
    flat = {}
    for hole, option in config.items():
        if isinstance(option, dict):
            flat.update({f'{hole} {key}': value for key, value in option.items()})
        else:
            flat[hole] = option
    return flat


def scored(ledger, table):
    """[(sample, score, flat choices)] of the full builds scored in `table` ('payout' or 'annual'), latest first."""
    found = [(s['sample'], s[table][0] / s[table][1], flatten(s['switches'])) for s in ledger
             if s.get(table) and not s.get('diagnostic') and s.get('switches')]
    return list(reversed(found))


def incumbent(ledger, table, defaults):
    """The choices of the best confirmed build on the latest sample (by `table`), else the defaults."""
    builds = scored(ledger, table)
    if not builds:
        return dict(defaults)
    latest = [b for b in builds if b[0] == builds[0][0]]
    return {**defaults, **max(latest, key=lambda b: b[1])[2]}


def by_leaderboard(hole, options, builds):
    """(options kept, reason): per sample, latest first, the options of `hole` with the best score among the builds
    of that sample, when that sample tried at least two of `options`."""
    for sample in dict.fromkeys(b[0] for b in builds):
        best = {}
        for name, score, flat in builds:
            if name == sample and flat.get(hole) in options:
                best[flat[hole]] = max(score, best.get(flat[hole], -1))
        if len(best) >= 2:
            top = max(best.values())
            kept = [o for o in options if best.get(o) == top]
            tried = ', '.join(f'{o} {100 * s:.0f} %' for o, s in best.items())
            return kept, f'(d) leaderboard, sample {sample}: {tried}'
    return options, ''


def by_targets(options, profile, base):
    """(options kept, reason): those no worse than the reference on every sample (the current option, else the best
    in all), and of them the most exact rows in all; nothing to say when every option scores the same."""
    rows = {o: profile[o].get('samples', {}) for o in options}
    if len({tuple(sorted(r.items())) for r in rows.values()}) < 2:
        return options, ''
    ref = base if base in options else max(options, key=lambda o: sum(rows[o].values()))
    safe = [o for o in options if all(rows[o][s] >= rows[ref][s] for s in rows[ref])]
    top = max(sum(rows[o].values()) for o in safe)
    kept = [o for o in safe if sum(rows[o].values()) == top]
    tried = ', '.join(f"{o} {'/'.join(str(rows[o][s]) for s in sorted(rows[o]))}" for o in options)
    return kept, f'(t) exact rows on {"/".join(sorted(rows[ref]))}: {tried}; {confirmed(kept, options, rows)}'


def confirmed(kept, options, rows):
    """Which samples prefer the option kept to the best of the others: both, one, or none (a tie on the samples)."""
    others = [o for o in options if o not in kept]
    if not others:
        return 'every option scores the same'
    rival = max(others, key=lambda o: sum(rows[o].values()))
    better = [s for s in sorted(rows[kept[0]]) if rows[kept[0]][s] > rows[rival][s]]
    if len(better) == len(rows[kept[0]]):
        return 'confirmed by both samples'
    return f"confirmed by {' and '.join(better)} only" if better else 'no sample prefers it'


def decide(hole, options, profile, builds, base, meaning=None):
    """(option, reason) of one hole. `profile` maps each option to its measures: {'checks': failing check or '',
    'contradictions': int, 'inconsistent': int}; `base` is the incumbent's option."""
    notes, left = [], list(options)
    failing = {o: profile[o]['checks'] for o in left if profile[o]['checks']}
    if failing and len(failing) < len(left):
        left = [o for o in left if o not in failing]
        notes.append('(a) ' + '; '.join(f'{o} breaks {why}' for o, why in failing.items()))
    left, why = by_targets(left, profile, base)
    notes += [why] if why else []
    fewest = min(profile[o]['contradictions'] for o in left)
    if any(profile[o]['contradictions'] > fewest for o in left):
        notes.append('(b) NRTAXB contradictions ' + ', '.join(f"{o} {profile[o]['contradictions']}" for o in left))
        left = [o for o in left if profile[o]['contradictions'] == fewest]
    if any(profile[o]['inconsistent'] for o in left) and not all(profile[o]['inconsistent'] for o in left):
        notes.append('(c) payout and annual disagree with ' + ', '.join(o for o in left if profile[o]['inconsistent']))
        left = [o for o in left if not profile[o]['inconsistent']]
    if len(left) > 1:
        left, why = by_leaderboard(hole, left, builds)
        notes += [why] if why else []
    if len(left) > 1 and base in left:
        left, why = [base], "(d') kept as the best confirmed build has it (no sample compared the options left)"
        notes.append(why)
    if len(left) > 1:
        chosen = meaning[0] if meaning and meaning[0] in left else left[0]
        notes.append(f'(e) tie: {meaning[1]}' if meaning and meaning[0] in left else '(e) tie: the first option')
        left = [chosen]
    return left[0], '; '.join(n for n in notes if n) or 'the only option'
