"""Reading the t5 target files back into the key and value types that t0..t4 return, so each target
can be compared value by value with the rules. Amounts become Decimal, never float, so cents stay exact."""
import csv
import datetime as dt
from decimal import Decimal


def read_targets(path, keys, values):
    """Target file -> {key: value} in the types the task functions return.

    keys and values are column counts from outliers.COLUMNS. Columns after the value columns
    (policy_value in t3_surrender_value.csv) are not checked.
    """
    with open(path, encoding='utf-8') as handle:
        rows = list(csv.reader(handle))[1:]  # after the header row; columns are taken by position
    return {parse(row[:keys]): parse(row[keys:keys + values]) for row in rows}


def parse(cells):
    """One cell becomes a value, several cells a tuple (the key/value shape of the task results)."""
    values = tuple(convert(cell) for cell in cells)
    return values[0] if len(values) == 1 else values


def convert(cell):
    """Numbers, ISO dates and amounts in their Python types; anything else (policy ids) stays text.

    The order matters: int first, so '2' is a due number and not Decimal('2');
    then dates ('2031-01-15'); then amounts ('12.34'). A policy id like 'BL00000000' fails all three.
    """
    for kind in (int, dt.date.fromisoformat, Decimal):
        try:
            return kind(cell)
        except (ValueError, ArithmeticError):
            continue
    return cell.strip()
