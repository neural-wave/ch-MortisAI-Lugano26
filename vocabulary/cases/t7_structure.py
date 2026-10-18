"""t7: which payouts carry which tax, found by the decision tree of the engine on NRTAXB (no amounts needed).

NRTAXB lists every tax Neuron booked at a payout; it is the only local record of t7, so it serves as the target of
"booked or not". Each payout gets the facts the law might use (country and reporting status of the holder, church,
the kind of payout, the gain, the Swiss threshold, the German regime, open Italian stamp duty), and the engine
splits where "never" stops fitting. The solution reads NRTAXB itself (T7_PRESENCE); these trees are the rules that
explain it, with their agreement, and the fallback (by the rules found) for an extract without it.
"""
import sys
import types
from pathlib import Path
from engine import is_holdout

TITLE = 't7 taxes at a payout: the rules NRTAXB shows (decision tree of the engine, 20 % of the policies held out)'
NEEDS_FOUND, STRUCTURE = True, ('VST', 'SOS', 'KST', 'SOL', 'KIS', 'BOC')
DEPENDS = {'SOL': 'KST', 'KIS': 'KST'}  # a surcharge of another tax: whether that one was booked is a fact for it


def never(row):
    """No tax."""
    return False


def always(row):
    """The tax."""
    return True


SLOTS = {'booked': {'never': never, 'always': always}}


def install(found):
    """The rules found so far as the module `rules` the solution's t7 code reads (rules.py may not exist yet)."""
    space = sys.modules.get('rules')
    if not isinstance(space, types.SimpleNamespace):  # one namespace, changed in place: modules imported see it
        space = sys.modules['rules'] = types.SimpleNamespace()
    vars(space).update(found)


def facts(legacy, key, detail):
    """The features of one payout."""
    from tax_gain import gain
    from tax_money import convert
    from tax_premiums import era
    from tax_residence import threshold
    from tax_germany_regime import regime
    from tax_stamp import accrued
    p, country, _, _, home = detail
    chf = convert(legacy, p.amount, p.currency, 'CHF', p.date, era(p))
    duty = [b for b, amount in accrued(legacy, p.policy, p.currency) if amount and b.processed <= p.processed]
    return {'country': country, 'reporting status': home.reporting, 'church member': home.church, 'payout kind': p.kind,
            'gain above zero': gain(legacy, p, 'EUR') > 0, 'above the Swiss threshold': chf > threshold(legacy, 'CH', 'VST', p.date),
            'German regime': regime(legacy, p, home) if country == 'DE' else '', 'Italian stamp duty accrued': bool(duty),
            'payout date': p.date}


def build(legacy, targets, found):
    """Rows: one payout each, its facts and its NRTAXB bookings (the target is set per tax by autosolve); none for an
    extract without the tax module (a client may come without it)."""
    if not (Path(legacy) / 'NRTAXB.csv').exists():
        return [], SLOTS, lambda row, c: c['booked'](row)
    install(found)
    from tax_payout import payout_details
    from tax_bookings import bookings
    rows = []
    for key, detail in sorted(payout_details(legacy).items()):
        booked = set(bookings(legacy).get(key, {}))
        rows.append({'policy': key[0], 'key': key, 'holdout': is_holdout(key[0]), 'booked': booked,
                     'features': facts(legacy, key, detail)})
    return rows, SLOTS, lambda row, c: c['booked'](row)
