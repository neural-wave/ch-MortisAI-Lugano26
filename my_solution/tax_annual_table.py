"""t7: the yearly table being filled: per (policy, year) the seven columns of t7_tax_annual.

    ch_stp  ch_vst  it_sos  it_bol  de_kst  de_sol  de_kis
A cell adds every amount of its tax and year; a year with no amount at all is not listed (the task).

t7: the day a withheld tax reached the tax office: by the country of residence (rules.py T7_REMITTANCE), shifted
when the office is closed (T7_REMITTANCE_SHIFT). The only evidence is the first example of the task: a German payout
of 17 July 2006 was remitted on 10 August; a country without its own rule takes that one.
"""
from collections import defaultdict
from decimal import Decimal as D
import rules
from conventions_tax_remit import tenth_of_next_month


COLUMNS = ('STP', 'VST', 'SOS', 'BOL', 'KST', 'SOL', 'KIS')


def empty_table():
    """{(policy, year): [seven amounts]}, every cell 0.00 until something is added."""
    return defaultdict(lambda: [D('0.00')] * len(COLUMNS))


def put(table, policy, year, kind, amount):
    """Add an amount to one cell (nothing for a zero)."""
    if amount:
        table[policy, year][COLUMNS.index(kind)] += amount


def remittance(country, day):
    """The day a tax withheld on `day` from a holder living in `country` reached the tax office."""
    return rules.T7_REMITTANCE_SHIFT(rules.T7_REMITTANCE.get(country, tenth_of_next_month)(day), country)
