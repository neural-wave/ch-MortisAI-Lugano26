"""t2 offer projection without any era brick in the dictionary.

The same holes as t2_offer, but only plain roundings and ages. No single combination fits,
so the diagnosis has to find on its own that the rule changes with the application date,
and the search per segment recovers the COBOL rule before and the Neuron NG rule after.
"""
import json
from bricks import ROUNDINGS, GROWTH
from cases import t2_offer
from engine import search, by_group

PLAIN_ROUNDING = {k: ROUNDINGS[k] for k in ('half up', 'truncate', 'half even')}
PLAIN_AGES = {k: v for k, v in t2_offer.AGE_RULES.items() if 'before' not in k}


def build(legacy, targets):
    rows, slots, formula = t2_offer.build(legacy, targets)
    slots = {'rounding': PLAIN_ROUNDING, 'entry age': PLAIN_AGES, 'growth': GROWTH, 'management rate': t2_offer.AMC}
    return rows, slots, formula


def extra_report(rows, formula, slots, out):
    """Change point: exact matches per application year of the best rule with plain half-up rounding."""
    plain = next(r for r in search(rows, formula, slots, top=0) if r['choice']['rounding'] == 'half up')
    curve = by_group(rows, plain['ok'], lambda r: r['features']['application year'])
    (out / 't2_offer_plain_change_point.json').write_text(json.dumps(curve))
    return ['', 'Change point: exact matches per application year with plain half-up rounding:', '',
            ' '.join(f'{y}: {100 * v:.3f} %' for y, v in curve.items())]
