"""The order of the charges and the trades of one day of the fund accounting (t3): a charge sees the units
before a trade of the same day, or after it (the valuation of the day: conventions_valuation). Neuron charges
first (rules.py, T3_DAY_ORDER): 3,709 premiums buy units on a charge day, and their units are not charged that day.

The calendar of one policy: its monthly charge dates up to the extract, and its last statement year (t4).
"""
import datetime as dt


def charges_before_trades():
    """Sort keys of a day: charges first, then trades."""
    return {'charge': 0, 'trade': 1}


def charges_after_trades():
    """Sort keys of a day: trades first, then charges."""
    return {'trade': 0, 'charge': 1}


DAY_ORDERS = {'charges before the trades': charges_before_trades, 'charges after the trades': charges_after_trades}


EXTRACT_DATE = dt.date(2026, 6, 30)  # the day of the Neuron extract; later anniversaries were not charged yet
LAST_STATEMENT = 2025  # the last complete statement year before the extract


def anniversaries(ledger):
    """(previous anniversary, anniversary) of every monthly charge up to the extract date (rule.T3_SCHEDULE)."""
    return ledger.rule.T3_SCHEDULE(ledger.start, ledger.end, EXTRACT_DATE)


def last_year(ledger):
    """Statements run until the year of a surrender or death (rule.T4_END_YEAR), at the latest 2025."""
    ended = ledger.rule.T4_END_YEAR(ledger.history)
    return min(LAST_STATEMENT, ended or LAST_STATEMENT)
