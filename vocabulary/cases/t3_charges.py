"""t3: the monthly charges ADM, AMC and RSK of each slot (the amounts of their bookings in t3_booking.csv).

Each charge day of a policy is calculated on its own: the units held on that day are the sum of all earlier
bookings of the policy (the PRM and charge units of t3_booking.csv, the customer orders of NRBOOK), so a miss
stays on its day and every hole can be tried on every day. The formula is the solution's
charges.monthly_charges on a light ledger with a trial of choices; its pieces are compared per type with the
bookings of the day (a zero piece is not booked). 18 holes by coordinate search per era on a sample.
"""
import datetime as dt
from collections import defaultdict
from decimal import Decimal as D
from functools import cache
from conventions import (TARIFF_DAYS, CLOSINGS, ADMIN_CAPS, MANAGEMENT_BASES, RISK_BASES, SPLIT_RESTS, ROUNDINGS,
                         AMC_AGREEMENTS, DAY_COUNTS, CHARGE_AGES, LOADINGS, MONTHLY_RATES, DAY_ORDERS, SLOT_VALUES, SCHEDULES)
from engine import is_holdout
from conventions_valuation import after_every_booking
from conventions_rounding import on_the_day, on_the_application_date
from cases.t3_common import applied, bookings, trial

TITLE, TASK, NEEDS_FOUND, DESCENT, SAMPLE = 't3 monthly charges', 't3_surrender_value', True, True, 34
ERA_DATES, ERA_RULE = {'charge date': on_the_day, 'application date': on_the_application_date}, 'T3_CHARGES_ERA_DATE'
ERA_HOLES = ('piece rounding', 'day count', 'management rounding', 'risk rounding', 'value rounding')
POLICIES = 3  # percent of the train policies read (the search uses SAMPLE percent of them, the check all)
RULES = {'tariff day': 'T3_TARIFF_DAY', 'closed': 'T3_CLOSED', 'admin cap': 'T3_ADMIN_CAP',
         'management base': 'T3_MANAGEMENT_BASE', 'risk base': 'T3_RISK_BASE', 'split rest': 'T3_SPLIT_REST',
         'piece rounding': 'T3_PIECE_ROUNDING', 'management rate': 'T3_AMC_RATE', 'day count': 'T3_DAY_COUNT',
         'management rounding': 'T3_AMC_ROUNDING', 'charge age': 'T3_CHARGE_AGE', 'risk rounding': 'T3_RISK_ROUNDING',
         'loading': 'RISK_LOADING', 'monthly rate': 'RISK_MONTHLY_RATE', 'day order': 'T3_DAY_ORDER',
         'slot value': 'T3_SLOT_VALUE', 'value rounding': 'T3_VALUE_ROUNDING', 'schedule': 'T3_SCHEDULE'}
NOTES = {'tariff day': 'the NRCHRG row of this day', 'risk base': 'the values the risk charge is taken on',
         'split rest': 'who takes the rounding rest of a split', 'day order': 'charges and trades of the same day'}
# Ties that no train policy decides, settled by what the business means (rules.py and the README say so).
PREFER = {'closed': ('closed on the day', 'business meaning: a surrendered or claimed policy is a closed contract, '
                     'worth 0 by the task, so nothing is charged from it'),
          'schedule': ('monthly, before maturity', 'business meaning: on the maturity day the value is paid out and '
                       'no new policy month begins, so no charge falls on it')}
KINDS = {2: 'ADM', 3: 'AMC', 4: 'RSK'}
# The full replay needs the time of a valuation in the day, searched later on the units it gives (t3_valuation);
# it does not change the charge totals (no valuation is replayed here), and autosolve checks the later search agrees.
ASSUMES = {'T3_VALUATION_TIME': after_every_booking}
EXTRACT = dt.date(2026, 6, 30)
DAYS = {}  # (policy, day, trial) -> {type: booked pieces}


def holdings(legacy, targets, pid, prm, charges):
    """The policy's unit movements as (date, kind, fund, pot, units): kind 0 a charge, 1 a trade."""
    from orders import customer_orders
    moves = [(b['trade'], 1, b['fund'], b['pot'], b['units']) for b in prm.get(pid, [])]
    moves += [(b['trade'], 0, b['fund'], b['pot'], b['units']) for b in charges[pid]]
    moves += [(date, 1, fund, pot, units) for date, fund, pot, units in customer_orders(legacy)[pid]]
    return sorted(moves, key=lambda m: m[:2])


def units_on(moves, day, with_trades):
    """{(fund, pot): units} before the charges of `day`, with or without the trades of that day."""
    units = defaultdict(D)
    for date, kind, fund, pot, amount in moves:
        if date < day or (date == day and kind == 1 and with_trades):
            units[fund, pot] += amount
    return units


def build(legacy, targets, found):
    charges, prm = defaultdict(list), defaultdict(list)
    for b in bookings(legacy, targets, ('ADM', 'AMC', 'RSK'), POLICIES).values():
        charges[b['policy']].append(b)
    for b in bookings(legacy, targets, ('PRM',), 100).values():
        if b['policy'] in charges:
            prm[b['policy']].append(b)
    rows = []
    for pid, booked in charges.items():
        moves, days = holdings(legacy, targets, pid, prm, charges), defaultdict(lambda: defaultdict(list))
        for b in booked:
            days[b['trade']][b['type']].append((b['fund'], b['pot'], b['amount']))
        for day, by_type in sorted(days.items()):
            units = (units_on(moves, day, False), units_on(moves, day, True))
            for kind in KINDS.values():
                rows.append({'policy': pid, 'key': (pid, day, kind), 'holdout': is_holdout(pid), 'day': day, 'kind': kind,
                             'target': tuple(sorted(by_type.get(kind, []))), 'units': units, 'legacy': legacy,
                             'found': found, 'features': {'charge date': day, 'application date': applied(legacy, pid), 'type': kind}})
    slots = {'tariff day': TARIFF_DAYS, 'closed': CLOSINGS, 'admin cap': ADMIN_CAPS, 'management base': MANAGEMENT_BASES,
             'risk base': RISK_BASES, 'split rest': SPLIT_RESTS, 'piece rounding': ROUNDINGS, 'management rate': AMC_AGREEMENTS,
             'day count': DAY_COUNTS, 'management rounding': ROUNDINGS, 'charge age': CHARGE_AGES, 'risk rounding': ROUNDINGS,
             'loading': LOADINGS, 'monthly rate': MONTHLY_RATES, 'day order': DAY_ORDERS, 'slot value': SLOT_VALUES,
             'value rounding': ROUNDINGS, 'schedule': SCHEDULES}
    return rows, slots, formula


def day_charges(row, c):
    """{type: sorted booked pieces} of the row's policy and day under the trial choices."""
    from charges import monthly_charges
    choice = {RULES[h]: (c[h], c[h]) if h in ERA_HOLES else c[h] for h in RULES}  # one era per search part
    ledger = trial(row['legacy'], row['policy'], row['found'], choice, RULES)
    previous = dict((d, p) for p, d in c['schedule'](ledger.start, ledger.end, EXTRACT)).get(row['day'])
    if previous is None:
        return {}
    ledger.units = defaultdict(D, row['units'][c['day order']()['trade'] < c['day order']()['charge']])
    booked, cancel = defaultdict(list), ledger.cancel

    def record(date, kind, amounts):
        booked[KINDS[kind]] += [(fund, pot, amount) for (fund, pot), amount in amounts.items() if amount]
        cancel(date, kind, amounts)
    ledger.cancel = record
    monthly_charges(ledger, row['day'], previous)
    return {kind: tuple(sorted(pieces)) for kind, pieces in booked.items()}


def formula(row, c):
    key = (row['policy'], row['day'], *(c[h] for h in RULES))
    if key not in DAYS:
        DAYS[key] = day_charges(row, c)
    return DAYS[key].get(row['kind'], ())


@cache
def expected_totals(legacy, targets):
    """{policy: {(type, day): booked total}} of every ADM, AMC and RSK booking of the train policies."""
    totals = defaultdict(lambda: defaultdict(D))
    for b in bookings(legacy, targets, ('ADM', 'AMC', 'RSK'), 100).values():
        totals[b['policy']][b['type'], b['trade']] += b['amount']
    return totals


def replayed_totals(legacy, pid, found, choice, premiums, orders):
    """{(type, day): charged total} of one policy replayed by the solution's code with the choices."""
    from ledger_run import replay
    ledger, totals = trial(legacy, pid, found, {**ASSUMES, **choice}, RULES), defaultdict(D)
    ledger.units, ledger.annual, cancel = defaultdict(D), defaultdict(lambda: [D(0)] * 5), ledger.cancel

    def record(date, kind, amounts):
        totals[KINDS[kind], date] += sum(amounts.values())
        cancel(date, kind, amounts)
    ledger.cancel = record
    replay(ledger, premiums, orders, [])
    return totals


def confirm(legacy, targets, found, choices):
    """For each full choice ({rule name: brick or pair}): how many charge totals (policy, type, day) of all train
    policies it matches, every policy replayed with the solution's own code (ledger_run.replay)."""
    from tables import received, by_key
    from orders import customer_orders
    expected, premiums, orders = expected_totals(legacy, targets), by_key(received(legacy), 'PR_POLNR'), customer_orders(legacy)
    scores = []
    for choice in choices:
        matched = 0
        for pid, booked in expected.items():
            totals = replayed_totals(legacy, pid, found, choice, premiums.get(pid, []), orders[pid])
            keys = set(booked) | {key for key, value in totals.items() if value}
            matched += sum(totals.get(key, 0) == booked.get(key, 0) for key in keys)
        scores.append(matched)
    return scores
