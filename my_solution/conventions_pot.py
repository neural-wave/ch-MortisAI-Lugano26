"""Where a premium goes (t3): the pot of its units and the rows of the allocation set that count.

A premium buys initial units (pot 1) before the end of the initial months of the product (PD_INIMON), or also
on that day; the pot of all 407,636 PRM bookings of the train policies follows "before the end" on the money
date (rules.py, T3_POT_BOUNDARY). Within the allocation set valid on the money date, a fund row counts if its
own validity covers the date, or always: no train premium tells them apart (T3_ALLOCATION_ROWS notes the tie).

What a premium buys under the terms of its date (ledger.rule): the pot (NRPROD) and the funds (NRALLO).
"""
from tables import day, version
from conventions_dates import add_months


def before_the_end(date, end):
    """Pot 1 strictly before the end of the initial months."""
    return date < end


def up_to_the_end(date, end):
    """Pot 1 up to and including the end of the initial months."""
    return date <= end


def valid_on_the_date(row, date):
    """A row of the allocation set counts if its own validity covers the date."""
    return day(row['AL_VLDFR']) <= date <= day(row['AL_VLDTO'])


def the_whole_set(row, date):
    """Every row of the allocation set counts."""
    return True


ALLOCATION_ROWS = {'rows valid on the date': valid_on_the_date, 'the whole set': the_whole_set}
POT_BOUNDARIES = {'before the end of the initial months': before_the_end, 'up to the end': up_to_the_end}


def pot(ledger, date):
    """Premiums of the first PD_INIMON months (NRPROD) buy initial units, pot 1; later ones base units, pot 2.

    `date` is the day rule.T3_POT_DATE names, the boundary is rule.T3_POT_BOUNDARY. The pot matters for
    the management charge: CG_AMCP1 and CG_AMCP2 are separate rates.
    """
    initial_end = add_months(ledger.start, int(ledger.product['PD_INIMON']))
    return '1' if ledger.rule.T3_POT_BOUNDARY(date, initial_end) else '2'


def shares(ledger, date):
    """The fund shares (NRALLO rows) of the allocation set valid on `date` (rule.T3_ALLOCATION_DATE).

    An allocation set is one AL_VRSNR, and its AL_PCTG add up to 1; within the set, a row counts as
    rule.T3_ALLOCATION_ROWS says (its own validity covers the date).
    """
    current = version(ledger.allocations, date, 'AL')['AL_VRSNR']
    for share in ledger.allocations:
        if share['AL_VRSNR'] == current and ledger.rule.T3_ALLOCATION_ROWS(share, date):
            yield share
