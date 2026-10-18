"""What the t3 cases share: the bookings of t3_booking.csv joined to NRBOOK, and a light ledger of a policy.

The PRM, ADM, AMC and RSK bookings of the train policies have their amount, price and units in t3_booking.csv
and their fund, pot and dates in NRBOOK. NRBOOK is a diagnostic here: the rules found are applied by the
solution without it. A light ledger has what the solution's booking functions read (ledger_premium,
ledger_units), with a trial of choices as its `rule`, so the search runs the solution's own code.
"""
import csv
import zlib
from collections import defaultdict
from decimal import Decimal as D
from functools import cache
from pathlib import Path
from types import SimpleNamespace

ERA_DATE_RULES = ('T3_AMOUNT_ERA_DATE', 'T3_UNITS_ERA_DATE', 'T3_CHARGE_UNITS_ERA_DATE', 'T3_CHARGES_ERA_DATE',
                  'T3_SURRENDER_ERA_DATE')


@cache
def bookings(legacy, targets, types, share):
    """{booking id: booking} of the given types, for `share` percent of the train policies (by policy)."""
    chosen = {}
    with open(Path(targets) / 't3_booking.csv', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            if row['booking_type'] in types and zlib.crc32(row['policy_id'].encode()) % 100 < share:
                chosen[row['booking_id']] = row
    from tables import day
    found = {}
    with open(Path(legacy) / 'NRBOOK.csv', encoding='utf-8') as handle:
        rows = csv.reader(handle, delimiter=';')
        header = next(rows)
        for raw in rows:
            target = chosen.get(raw[0])
            if target:
                b = dict(zip(header, (v.strip() for v in raw)))
                found[raw[0]] = {'policy': target['policy_id'], 'type': target['booking_type'], 'fund': b['BK_FNDID'],
                                 'pot': b['BK_POTCD'], 'event': b['BK_EVTNR'], 'trade': day(b['BK_TRDDT']),
                                 'money': day(b['BK_RCVDT']) if int(b['BK_RCVDT']) else None,
                                 'amount': D(target['amount_pc']), 'price': D(target['price']), 'units': D(target['units'])}
    return found


@cache
def premium_items(legacy):
    """{(policy, booking event): received premium item}: the NRPREM item a PRM booking invests."""
    from tables import received
    return {(r['PR_POLNR'], r['PR_EVTNR']): r for r in received(legacy)}


@cache
def applied(legacy, pid):
    """The application date of a policy (PH_APPDT of its first version): a candidate date of the era."""
    from tables import grouped, day
    return day(min(grouped(legacy, 'NRPOLH', 'PH_POLNR')[pid], key=lambda r: int(r['PH_VRSNR']))['PH_APPDT'])


@cache
def light_ledger(legacy, pid):
    """The policy data the booking functions read; `rule` and `era` are set per trial."""
    from tables import grouped, day
    from tariff import parameters
    from market import market
    history = grouped(legacy, 'NRPOLH', 'PH_POLNR')[pid]
    first = min(history, key=lambda r: int(r['PH_VRSNR']))
    risks, persons, brokers, mortality = parameters(legacy)
    return SimpleNamespace(folder=legacy, history=history, brokers=brokers, market=market(legacy),
                           agreements=grouped(legacy, 'NRAGRE', 'AG_POLNR')[pid],
                           allocations=grouped(legacy, 'NRALLO', 'AL_POLNR')[pid],
                           product=grouped(legacy, 'NRPROD', 'PD_PRDCD')[first['PH_PRDCD']][0],
                           start=day(first['PH_BEGDT']), end=day(first['PH_ENDDT']), applied=day(first['PH_APPDT']),
                           ccy=first['PH_CCY'], risk=risks[pid], tariff=risks[pid]['RK_TARKEY'], mortality=mortality,
                           person=persons[risks[pid]['RK_PERNR']], annual=defaultdict(lambda: [D(0)] * 5))


def trial(legacy, pid, found, choice, names):
    """The light ledger of a policy with the rules found so far plus the trial `choice` ({rule name: brick}),
    the entry age by the era of the offer, and the solution's own slots, agreements and cancel. A day of the
    era not found yet is the day of the calculation: a case searches one era at a time (pairs of one brick),
    so that day changes nothing until autosolve compares the candidates."""
    from ledger_value import fund_values
    from conventions_fx_dates import agreed
    from ledger_cancel import cancel_units
    from conventions_rounding import on_the_day
    ledger = light_ledger(legacy, pid)
    rule = SimpleNamespace(**{**{name: on_the_day for name in ERA_DATE_RULES}, **found, **choice})
    era = lambda pair, which, date, money=None: pair[1] if which(date, ledger, money) >= rule.ERA_CUTOFF else pair[0]  # noqa: E731
    first = min(ledger.history, key=lambda r: int(r['PH_VRSNR']))
    birth = rule.BIRTH_DATE(ledger.person['PS_BIRTH'])
    age_rule = rule.ERA_AGE[1] if rule.ERA_DATE(first) >= rule.ERA_CUTOFF else rule.ERA_AGE[0]
    trial = SimpleNamespace(**{**vars(ledger), 'rule': rule, 'era': era, 'birth': birth, 'age_rule': age_rule,
                               'age': age_rule(birth, ledger.start)})
    trial.slots = lambda date: fund_values(trial, date)
    trial.agreed = lambda kind, date, default: agreed(trial, kind, date, default)
    trial.cancel = lambda date, kind, amounts: cancel_units(trial, date, kind, amounts)
    return trial
