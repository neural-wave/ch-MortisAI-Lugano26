"""The tables looked up many times, read once per folder and kept in memory (see tables_read for the format).

Both functions are cached on their arguments (folder, table and key column): the policy loop asks for the
same table for every policy, and the file must be read once per run, not once per policy.
"""
from collections import defaultdict
from functools import cache

from tables_read import stream


@cache
def table(folder, name):
    """A whole table as a list of trimmed rows, in file order."""
    return list(stream(folder, name))


@cache
def grouped(folder, name, key):
    """The rows of a table grouped by one column, usually the policy number (e.g. 'PH_POLNR')."""
    return by_key(table(folder, name), key)


def by_key(rows, key):
    """Rows grouped by the value of column `key`; the rows of a group keep their order.

    A defaultdict, so a policy without rows in the table gets an empty list instead of a KeyError.
    """
    result = defaultdict(list)
    for row in rows:
        result[row[key]].append(row)
    return result
