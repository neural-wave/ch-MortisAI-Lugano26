"""t7 (The Tax Audit): the conventions of Neuron's tax module, chosen by evidence (vocabulary/evidence.py).

Each option of each hole is measured with the other holes as the current choice has them: (a) the two examples of the
task to the cent and every amount in whole cents (scoring_t7 compares exactly), (t) the exact rows on the samples of
the answers the leaderboard scored us on (targets_t7/sample_*, vocabulary/t7_targets.py; an option replaces the
current one only if it is no worse on every sample), (b) the contradictions with NRTAXB, the record of the taxes
Neuron booked (which payouts carry a tax, the country of every Italian stamp duty), (c) the yearly table against the
payouts, (d) the leaderboard log logs/t7_evidence.json (one sample at a time), (e) a tie. The passes repeat until no
choice changes (the holes act together). rules.py gets the choice and the evidence of each hole.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from decimal import Decimal as D
from evidence import decide as choose, incumbent, scored
from conventions_tax import TAX_PRESENCE, KNOWN_VERSIONS
from conventions_tax_bases import UNTAXED_BASES, REPORTED_VST
from conventions_tax_remit import REMITTANCE_DAYS, REMITTANCE_SHIFTS, NO_REMITTANCE
from conventions_tax_share import BOL_SHARES
from conventions_tax_payout import PAYOUT_AMOUNTS, DEATH_AMOUNTS
from conventions_tax_premium import PREMIUM_AMOUNTS, BASIS_SHARES
from conventions_tax_rows import LOSS_BASES, BOC_DATES, FIRST_YEARS
from conventions_tax_found import (SOS_RULES, SOS_EARLIER, ANNUAL_YEARS, BOL_PAYOUT_AMOUNTS, SURCHARGE_ROUNDINGS,
                                   PREMIUM_ROUNDINGS, BOL_CORRECTIONS)
import t7_targets
from conventions_tax_share import BOL_VALUES, BOC_SHARES
from conventions_tax_germany import KST_CHURCH, TFS_WITH_HEV, TFS

TITLE = 't7 taxes (no targets: each choice by evidence, the strongest first; vocabulary/evidence.py)'
SLOTS = {'payout amount': PAYOUT_AMOUNTS, 'death claim amount': DEATH_AMOUNTS, 'premium amount': PREMIUM_AMOUNTS,
         'paid back share': BASIS_SHARES, 'base of a loss': LOSS_BASES, 'stamp duty alone': BOC_DATES,
         'stamp duty first year': FIRST_YEARS, 'presence': TAX_PRESENCE, 'residence known': KNOWN_VERSIONS, 'rate known': KNOWN_VERSIONS,
         'untaxed Swiss base': UNTAXED_BASES, 'reported withholding': REPORTED_VST,
         'remittance': REMITTANCE_DAYS, 'remittance shift': REMITTANCE_SHIFTS, 'no remittance': NO_REMITTANCE, 'stamp duty share': BOL_SHARES,
         'stamp duty value': BOL_VALUES, 'stamp duty collected': BOC_SHARES, 'church tax': KST_CHURCH,
         'exemption with half income': TFS_WITH_HEV, 'exemption': TFS, 'Italian substitute tax': SOS_RULES,
         'earlier withdrawals in the periods': SOS_EARLIER, 'year in the yearly table': ANNUAL_YEARS,
         'stamp duty at a payout': BOL_PAYOUT_AMOUNTS, 'German surcharges': SURCHARGE_ROUNDINGS,
         'premium rounding': PREMIUM_ROUNDINGS, 'the 2019 correction': BOL_CORRECTIONS}
RULES = {'payout amount': 'T7_PAYOUT_AMOUNT', 'death claim amount': 'T7_DEATH_AMOUNT', 'premium amount': 'T7_PREMIUM_AMOUNT',
         'paid back share': 'T7_BASIS_SHARE', 'base of a loss': 'T7_LOSS_BASE', 'stamp duty alone': 'T7_BOC_DATED',
         'stamp duty first year': 'T7_BOL_FIRST_YEAR', 'presence': 'T7_PRESENCE', 'residence known': 'T7_RESIDENCE_KNOWN', 'rate known': 'T7_RATE_KNOWN',
         'untaxed Swiss base': 'T7_CH_UNTAXED_BASE',
         'reported withholding': 'T7_REPORTED_VST', 'remittance': 'T7_REMITTANCE', 'remittance shift': 'T7_REMITTANCE_SHIFT',
         'no remittance': 'T7_NO_REMITTANCE',
         'stamp duty share': 'T7_BOL_SHARE', 'stamp duty value': 'T7_BOL_VALUE', 'stamp duty collected': 'T7_BOC_SHARE',
         'church tax': 'T7_KST_CHURCH', 'exemption with half income': 'T7_TFS_WITH_HEV',
         'exemption': 'T7_TFS', 'Italian substitute tax': 'T7_SOS', 'earlier withdrawals in the periods': 'T7_SOS_EARLIER',
         'year in the yearly table': 'T7_ANNUAL_YEAR', 'stamp duty at a payout': 'T7_BOL_PAYOUT_AMOUNT',
         'German surcharges': 'T7_SURCHARGE_ROUNDING', 'premium rounding': 'T7_PREMIUM_ROUNDING',
         'the 2019 correction': 'T7_BOL_CORRECTION'}
NOTES = {'payout amount': 'what a withdrawal or a surrender paid', 'death claim amount': 'what a death claim paid',
         'premium amount': 'the premiums a payout pays back', 'paid back share': 'the premiums a withdrawal pays back',
         'base of a loss': 'the base of a payout at a loss in Italy and Germany',
         'stamp duty alone': 'whether stamp duty collected alone gives a remittance date',
         'stamp duty first year': 'the yearly stamp duty of the first policy year', 'presence': 'whether a tax was booked', 'residence known': 'the NRHOLD and NRADDR versions Neuron used',
         'rate known': 'the NRTAXR versions Neuron used',
         'untaxed Swiss base': 'the base of a Swiss payout without withholding tax',
         'reported withholding': 'withholding tax of status M in the yearly table',
         'remittance': 'the day a withheld tax reaches the tax office, by country of residence',
         'remittance shift': 'a remittance day the office is closed',
         'no remittance': 'the remittance date of a payout without tax',
         'stamp duty share': 'the share of a payout year the Italian stamp duty is due for',
         'stamp duty value': 'the value the yearly Italian stamp duty is taken on',
         'stamp duty collected': 'the open stamp duty a withdrawal collects',
         'church tax': 'the capital gains tax with church tax', 'exemption with half income': 'TFS for an HEV payout',
         'exemption': 'the German partial exemption of 2018 (TFS) of a payout taxed in full',
         'Italian substitute tax': 'the rates of the Italian substitute tax on the gain',
         'earlier withdrawals in the periods': 'earlier withdrawals in the rate periods of the Italian gain',
         'year in the yearly table': "the year of a payout's tax in the yearly table",
         'stamp duty at a payout': 'what the Italian stamp duty at a payout is taken on',
         'German surcharges': 'the rounding of German SOL and KIS',
         'premium rounding': 'the day whose system rounds a converted premium',
         'the 2019 correction': 'the 2019 correction of the Italian stamp duty (TAXFIX19)'}
COUNTRIES = ('DE', 'IT', 'CH', 'LU')  # the remittance day is a choice per country of residence
BY_COUNTRY = {f'remittance {c}' for c in COUNTRIES}
ANNUAL = {'reported withholding', 'stamp duty value', 'stamp duty first year', 'stamp duty share'}  # scored in annual
EVIDENCE = Path(__file__).resolve().parents[2] / 'logs' / 't7_evidence.json'
EXAMPLES = {  # the two rows the task shows
    't7_tax_payout': (('BL10000086', 121), ('DE', D('5628.16'), D('1407.04'), D('77.38'), D('0.00'), '2006-08-10')),
    't7_tax_annual': (('BL10000044', 2019), (D('0.00'), D('0.00'), D('0.00'), D('616.11'), D('0.00'), D('0.00'), D('0.00'))),
}


def holes():
    """{hole: family}, the remittance day spread into one hole per country."""
    flat = {h: f for h, f in SLOTS.items() if h != 'remittance'}
    return {**flat, **{f'remittance {c}': SLOTS['remittance'] for c in COUNTRIES}}


def values(config):
    """{rule name: brick} of a flat choice of options."""
    out = {RULES[h]: SLOTS[h][o] for h, o in config.items() if h not in BY_COUNTRY}
    out['T7_REMITTANCE'] = {c: SLOTS['remittance'][config[f'remittance {c}']] for c in COUNTRIES}
    return out


def use(found, config):
    """The rules the solution's t7 code reads: the rules found so far and the choices of `config` (one namespace,
    changed in place, so modules already imported see it); the caches of the t7 modules are emptied."""
    space = sys.modules.get('rules')
    if not isinstance(space, SimpleNamespace):
        space = sys.modules['rules'] = SimpleNamespace()
    vars(space).update({**found, **values(config)})
    for module in list(sys.modules.values()):
        if getattr(module, '__name__', '').startswith('tax_'):
            for item in vars(module).values():
                if hasattr(item, 'cache_clear'):
                    item.cache_clear()


def cents(rows):
    """Amounts with a fraction of a cent: no answer of Neuron has one, scoring_t7 compares exactly."""
    return sum(1 for v in rows.values() for x in v if isinstance(x, D) and x != x.quantize(D('0.01')))


def checks(payout, annual):
    """The first hard fact the answers break, or ''."""
    for task, rows in (('t7_tax_payout', payout), ('t7_tax_annual', annual)):
        key, row = EXAMPLES[task]
        got = tuple(str(x) if hasattr(x, 'isoformat') else x for x in rows.get(key, ()))
        if got != row:
            return f'the example of {task}'
        if cents(rows):
            return f'whole cents in {task} ({cents(rows)} amounts)'
    return ''


def contradictions(legacy):
    """Rules of which payouts carry a tax against NRTAXB (Swiss VST: status E above the threshold; Italian SOS: a gain,
    no death claim; German KST: a gain, not the old regime, no death claim), and Italian stamp duties of a holder Neuron
    did not see in Italy."""
    from tax_payout import payout_details
    from tax_bookings import bookings
    from tax_gain import gain
    from tax_money import convert
    from tax_premiums import era
    from tax_residence import threshold, residence
    from tax_germany_regime import regime
    found = 0
    for (pid, ev), (p, country, _, _, home) in payout_details(legacy).items():
        booked = set(bookings(legacy).get((pid, ev), {}))
        if country == 'CH':
            chf = convert(legacy, p.amount, p.currency, 'CHF', p.date, era(p))
            found += (home.reporting == 'E' and chf > threshold(legacy, 'CH', 'VST', p.date)) != ('VST' in booked)
        elif country in ('IT', 'DE'):
            profit, kind = gain(legacy, p, 'EUR') > 0, 'SOS' if country == 'IT' else 'KST'
            regular = country == 'IT' or regime(legacy, p, home) != 'old'
            found += (profit and regular and p.kind != 'death') != (kind in booked)
    stamps = [b for kinds in bookings(legacy).values() for b in kinds.get('BOL', [])]
    return found + sum(residence(legacy, b.policy, b.date, b.processed).country != 'IT' for b in stamps)


def inconsistent(payout, annual, legacy):
    """Policy years whose yearly taxes of payouts (VST, SOS, KST, SOL, KIS) differ from the sum of their payouts; a
    payout's tax counts in the year rules.py T7_ANNUAL_YEAR gives it (the remittance date, when it has one)."""
    from tax_payout import payout_details
    import rules
    totals = {}
    for key, (p, *_) in payout_details(legacy).items():
        total = sum(payout[key][2:4], D(0))
        remitted = payout[key][5] if hasattr(payout[key][5], 'year') else p.date
        if total:
            year = rules.T7_ANNUAL_YEAR(p.date, remitted)
            totals[p.policy, year] = totals.get((p.policy, year), D(0)) + total
    return sum(1 for k, t in totals.items() if sum(annual.get(k, (0,) * 7)[i] for i in (1, 2, 4, 5, 6)) != t)


def measure(legacy, found, config):
    """{'checks', 'contradictions', 'inconsistent'} of one choice of options."""
    use(found, config)
    from tax_payout import payout_taxes
    from tax_annual import annual_taxes
    payout, annual = payout_taxes(legacy), annual_taxes(legacy)
    answers = {'t7_tax_payout': payout, 't7_tax_annual': annual}
    return {'checks': checks(payout, annual), 'contradictions': contradictions(legacy),
            'inconsistent': inconsistent(payout, annual, legacy),
            'samples': {name: s[0] + s[2] for name, s in t7_targets.score(answers, TARGETS).items()},
            'answers': answers}


def ledger():
    """The leaderboard log: every scored submission with its choices (empty without the log)."""
    return json.loads(EVIDENCE.read_text())['submissions'] if EVIDENCE.exists() else []


TARGETS = t7_targets.samples()
PASSES = 4  # a pass measures every option once; the passes stop when none changes a choice
REPORT = {}  # the counts of the last search for the report of autosolve: score before and after, misses by group


def one_pass(legacy, found, base, log, families, table):
    """{hole: (option, reason)} of one pass from the choices `base`; a choice made is the base of the next holes."""
    chosen, base, at_base = {}, dict(base), measure(legacy, found, base)
    for hole, family in families.items():
        profile = {o: at_base if o == base[hole] else measure(legacy, found, {**base, hole: o}) for o in family}
        chosen[hole] = choose(hole, list(family), profile, scored(log, table[hole]), base[hole])
        if chosen[hole][0] != base[hole]:
            base[hole], at_base = chosen[hole][0], profile[chosen[hole][0]]
        print(f'  {hole}: {chosen[hole][0]} ({chosen[hole][1]})', flush=True)
    return chosen, at_base


def decide(legacy, found):
    """{hole: (option, reason)}: every option of every hole measured against the current choice, then
    evidence.decide; again from the new choices until a pass changes none."""
    log, families = ledger(), holes()
    defaults = {h: next(iter(f)) for h, f in families.items()}
    table = {h: 'annual' if h in ANNUAL else 'payout' for h in families}
    base = {h: incumbent(log, table[h], defaults)[h] for h in families}
    start = measure(legacy, found, base)
    REPORT['before'] = t7_targets.report(start['answers'], TARGETS)
    for n in range(PASSES):
        chosen, last = one_pass(legacy, found, base, log, families, table)
        moved = {h: o for h, (o, _) in chosen.items() if o != base[h]}
        print(f'  pass {n + 1}: {len(moved)} choices changed', flush=True)
        base = {h: o for h, (o, _) in chosen.items()}
        if not moved:
            break
    REPORT['after'] = t7_targets.report(last['answers'], TARGETS)
    use(found, base)
    remittance = {c: chosen.pop(f'remittance {c}') for c in COUNTRIES}
    chosen['remittance'] = ({c: o for c, (o, _) in remittance.items()},
                            '; '.join(f'{c}: {why}' for c, (_, why) in remittance.items()))
    return chosen
