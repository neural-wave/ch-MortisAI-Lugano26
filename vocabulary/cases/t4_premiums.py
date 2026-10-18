"""t4 premiums of a statement year: which items count and by which date they fall into a year.

Target: the premiums column of the annual statement. Holes: the item set (received and not
reversed, all paid items, or all items at their amount due) and the date that decides the year
(money date, due date, or the effective date of the booking event).
"""
from collections import defaultdict
from decimal import Decimal as D
from engine import is_holdout
from cases.common import read, money

ITEMS = ('received, not reversed', 'state P (paid)', 'all items, amount due')
YEAR_OF = ('money date', 'due date', 'booking event date')


def build(legacy, targets):
    from tables import table, received, day, scaled, stream
    events = {(r['EV_POLNR'], r['EV_EVTNR']): day(r['EV_EFFDT']) for r in stream(legacy, 'NREVNT') if r['EV_EVTTP'] == '110'}
    sets = {'received, not reversed': received(legacy),
            'state P (paid)': [r for r in table(legacy, 'NRPREM') if r['PR_STATE'] == 'P'],
            'all items, amount due': table(legacy, 'NRPREM')}
    totals = {}
    for label, items in sets.items():
        column = 'PR_AMTDU' if label == 'all items, amount due' else 'PR_AMTRC'
        for year_of in YEAR_OF:
            sums = defaultdict(D)
            for r in items:
                date = {'money date': day(r['PR_RCVDT']) if int(r['PR_RCVDT']) else None, 'due date': day(r['PR_DUEDT']),
                        'booking event date': events.get((r['PR_POLNR'], r['PR_EVTNR']))}[year_of]
                if date:
                    sums[r['PR_POLNR'], date.year] += scaled(r[column], 2)
            totals[label, year_of] = sums
    rows = [{'policy': r['policy_id'], 'holdout': is_holdout(r['policy_id']), 'key': (r['policy_id'], int(r['year'])),
             'target': money(r['premiums']), 'totals': totals, 'features': {'year': int(r['year'])}}
            for r in read(targets, 't4_annual_statement')]
    return rows, {'items': {i: i for i in ITEMS}, 'year by': {y: y for y in YEAR_OF}}, formula


def formula(row, c):
    return row['totals'][c['items'], c['year by']].get(row['key'], D(0))
