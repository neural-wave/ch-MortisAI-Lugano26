"""t2 offer projection, every policy year: which version and tariff day, the order of a month, every rounding.

Rows: each policy year of t2_projection_year.csv, started from the expected value of the year before (so a
miss stays in its own year), and the maturity value of t2_projected_maturity_value.csv, started from the last
whole year inside the term. The formula is the solution's own code (projection_offer.offer, projection_month
.advance) run with a trial of choices. 14 holes are too many for every combination: a coordinate search
starts from the simplest options on a sample of the policies, and the result is confirmed on all rows.
"""
from decimal import Decimal as D, ROUND_HALF_UP
from types import SimpleNamespace
from conventions import (OFFER_VERSIONS, OFFER_DATES, TERMS, ROUNDING_STEPS, GROWTH, ORDERS, ADMIN_MONTHS, FLOORS,
                         AMC_RATES, AMC_PERIODS, ATTAINED_AGES)
from engine import is_holdout
from cases.common import read, money

TITLE, TASK = 't2 offer projection', 't2_projected_maturity_value'
DESCENT, NEEDS_FOUND, SAMPLE = True, True, 10  # coordinate search on 10 % of the policies, confirmed on all
RULES = {'version': 'T2_VERSION', 'parameter date': 'T2_PARAMETER_DATE', 'age at': 'T2_AGE_AT', 'term': 'T2_TERM',
         'net premium rounding': 'T2_NET_ROUNDING', 'growth': 'T2_GROWTH', 'order': 'T2_ORDER',
         'admin months': 'T2_ADMIN_MONTHS', 'floor': 'T2_FLOOR', 'management rate': 'T2_AMC_RATE',
         'management period': 'T2_AMC_PERIOD', 'charge rounding': 'T2_CHARGE_ROUNDING',
         'growth rounding': 'T2_GROWTH_ROUNDING', 'attained age': 'T2_ATTAINED_AGE'}
NOTES = {'version': 'the policy version the offer belongs to', 'parameter date': 'NRCHRG, NRILLU and NRENTC are taken on it',
         'age at': 'the entry age is the age on this day', 'order': 'the steps of one month'}
PREFER = {'floor': ('never below zero', 'consistent with the fund accounting of t3, where no charge takes the value '
                     'below zero: the admin fee is at most the value (charges.py) and no negative piece is booked '
                     '(conventions_rest, step 2)')}
OFFER_HOLES = ('version', 'parameter date', 'age at', 'term', 'net premium rounding', 'growth')
OFFERS = {}  # (policy, offer choices) -> Offer


def build(legacy, targets, found):
    from tables import grouped
    years, maturity = {}, {r['policy_id']: money(r['maturity_value']) for r in read(targets, 't2_projected_maturity_value')}
    for r in read(targets, 't2_projection_year'):
        years.setdefault(r['policy_id'], {})[int(r['policy_year'])] = money(r['value'])
    rows = []
    for pid, history in grouped(legacy, 'NRPOLH', 'PH_POLNR').items():
        if pid not in years:
            continue
        base = {'policy': pid, 'holdout': is_holdout(pid), 'history': history, 'folder': legacy, 'found': found,
                'years': years[pid]}
        for year, value in sorted(years[pid].items()):
            rows.append({**base, 'key': (pid, year), 'target': value, 'year': year,
                         'features': {'policy year': year, 'kind': 'year'}})
        rows.append({**base, 'key': (pid, 'maturity'), 'target': maturity[pid], 'year': None,
                     'features': {'policy year': 0, 'kind': 'maturity'}})
    slots = {'version': OFFER_VERSIONS, 'parameter date': OFFER_DATES, 'age at': OFFER_DATES, 'term': TERMS,
             'net premium rounding': ROUNDING_STEPS, 'growth': GROWTH, 'order': ORDERS, 'admin months': ADMIN_MONTHS,
             'floor': FLOORS, 'management rate': AMC_RATES, 'management period': AMC_PERIODS,
             'charge rounding': ROUNDING_STEPS, 'growth rounding': ROUNDING_STEPS, 'attained age': ATTAINED_AGES}
    return rows, slots, formula


def formula(row, c):
    from projection_offer import offer
    from projection_month import advance
    rule, found = SimpleNamespace(**{**row['found'], **{RULES[hole]: c[hole] for hole in RULES}}), row['found']
    key = (row['policy'], *(c[hole] for hole in OFFER_HOLES))
    if key not in OFFERS:
        OFFERS[key] = offer(row['folder'], row['history'], rule, lambda date: tuple(
            found[name][date >= found['ERA_CUTOFF']] for name in ('ERA_ROUNDING', 'ERA_AGE')))
    terms, years = OFFERS[key], row['years']
    if row['year']:  # one policy year, from the expected value at the end of the year before
        first, last, value = 12 * (row['year'] - 1), 12 * row['year'], years.get(row['year'] - 1, D(0))
    else:  # the maturity value, from the last whole year inside the term
        whole = min(len(years), terms.months // 12)
        first, last, value = 12 * whole, terms.months, years.get(whole, D(0))
    for month in range(first, last):
        value = advance(value, month, terms, rule)
    return value if row['year'] else value.quantize(D('0.01'), rounding=ROUND_HALF_UP)
