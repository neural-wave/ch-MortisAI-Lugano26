"""Reading the Neuron extract of 2026-06-30 (SCHEMA.md, "Conventions"): one UTF-8 file `<TABLE>.csv` per table,
separated by `;`, with a header row; an empty field means no value. Values come back as trimmed strings:
`C` columns are fixed-length and padded with blanks ('BL10000001  '), so a policy number only joins across
tables once trimmed. Dates and numbers are decoded by the callers (tables_formats, tables_numbers).

Neuron's `N(scale)` columns (SCHEMA.md, "Conventions"): integers whose last `scale` digits are decimals.
N(2) for amounts (123456 is 1234.56), N(6) for rates, shares and fund units (12500 is 0.0125). They are
decoded into Decimal, never float, so every fee and unit comes out to the cent the legacy system booked.

The row of a versioned table valid on a day (SCHEMA.md, "Conventions"). Eleven tables have a validity period
`_VLDFR` to `_VLDTO`, both days included; in the five with a `_VRSNR` (NRPOLH, NRHOLD, NRADDR, NRALLO, NRTAXR)
the highest version wins when several rows are valid.
"""
import csv
from pathlib import Path
from functools import cache
from decimal import Decimal as D
from tables_formats import legacy


def _file(folder, name):
    """The open file of one table; the caller closes it with `with`."""
    return (Path(folder) / f'{name}.csv').open(encoding='utf-8')


def stream(folder, name):
    """The rows of one table as dicts keyed by column name, read lazily; an empty field becomes ''.

    csv.DictReader fills the fields missing at the end of a short row with None; they become '' as well."""
    with _file(folder, name) as handle:
        for row in csv.DictReader(handle, delimiter=';'):
            yield {k: (v or '').strip() for k, v in row.items()}


def matching(folder, name, column, values):
    """Only the rows whose `column` is one of `values`, as `stream` gives them.

    NRBOOK (6.8 million rows) and NREVNT are read for a few thousand rows each; testing the column
    before building the dict makes that about ten times faster."""
    with _file(folder, name) as handle:
        rows = csv.reader(handle, delimiter=';')
        header = next(rows)
        index = header.index(column)
        for row in rows:
            if row[index].strip() in values:
                yield {k: v.strip() for k, v in zip(header, row)}


@cache  # the same rates and fees are decoded every month for every policy
def scaled(value, scale=6):
    """An `N(scale)` column as an exact Decimal; N(6), the default, is the scale of rates and units."""
    return D(value) / (10 ** scale)


def _valid_on(row, n, prefix):
    """Whether the validity period of `row` contains the CYYMMDD day `n`, both ends included."""
    return int(row[prefix + '_VLDFR']) <= n <= int(row[prefix + '_VLDTO'])


def version(rows, date, prefix):
    """The row of `rows` valid on `date`, or None. Rows without `_VRSNR` (agreements, charges, rates) count as
    version 0, so max() keeps the first valid row in file order."""
    n = legacy(date)
    valid = [r for r in rows if _valid_on(r, n, prefix)]
    return max(valid, key=lambda r: int(r.get(prefix + '_VRSNR', 0))) if valid else None
