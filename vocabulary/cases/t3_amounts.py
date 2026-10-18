"""t3: the amount a premium invests in each fund (the amount_pc of each PRM booking of t3_booking.csv).

Holes: the day of the entry rate (broker tier or ENT agreement) and of the allocation set, which rows of the
set count, how a fund's amount is split and rounded (conventions_premium), and the rounding of each era by
the trade date. The formula is the solution's ledger_parts.premium_parts with a trial of choices.
"""
from conventions import PREMIUM_DATES, ALLOCATION_ROWS, SPLITS, ROUNDINGS
from engine import is_holdout
from conventions_rounding import on_the_day, on_the_money_date, on_the_application_date
from cases.t3_common import applied, bookings, premium_items, trial

TITLE, TASK, NEEDS_FOUND, DESCENT, SAMPLE = 't3 amount of a premium per fund', 't3_surrender_value', True, True, 10
ERA_HOLES, ERA_RULE = ('amount rounding',), 'T3_AMOUNT_ERA_DATE'
ERA_DATES = {'trade date': on_the_day, 'money date': on_the_money_date, 'application date': on_the_application_date}
RULES = {'entry date': 'T3_ENTRY_DATE', 'allocation date': 'T3_ALLOCATION_DATE', 'allocation rows': 'T3_ALLOCATION_ROWS',
         'split': 'T3_SPLIT', 'amount rounding': 'T3_AMOUNT_ROUNDING'}
NOTES = {'entry date': 'the entry rate (broker tier, ENT agreement) is taken on this day',
         'allocation date': 'the allocation set of this day is invested'}
PARTS = {}  # (booking, trial) -> {fund: amount}


def build(legacy, targets, found):
    items, rows = premium_items(legacy), []
    for key, b in bookings(legacy, targets, ('PRM',), 100).items():
        rows.append({'policy': b['policy'], 'key': key, 'holdout': is_holdout(b['policy']), 'target': b['amount'],
                     'item': items[b['policy'], b['event']], 'fund': b['fund'], 'legacy': legacy, 'found': found,
                     'features': {'trade date': b['trade'], 'money date': b['money'], 'application date': applied(legacy, b['policy']),
                                  'fund': b['fund']}})
    slots = {'entry date': PREMIUM_DATES, 'allocation date': PREMIUM_DATES, 'allocation rows': ALLOCATION_ROWS,
             'split': SPLITS, 'amount rounding': ROUNDINGS}
    return rows, slots, formula


def formula(row, c):
    from ledger_parts import premium_parts
    choice = {RULES[h]: c[h] for h in RULES}
    choice['T3_AMOUNT_ROUNDING'] = (c['amount rounding'], c['amount rounding'])  # one era per search part
    key = (row['key'], *choice.values())
    if key not in PARTS:
        ledger = trial(row['legacy'], row['policy'], row['found'], choice, RULES)
        PARTS[key] = {fund: amount for fund, _, _, _, amount, _ in premium_parts(ledger, row['item'])}
    return PARTS[key].get(row['fund'])
