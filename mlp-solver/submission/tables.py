"""Reading the Neuron export: one CSV per table, legacy number and date formats, versioned rows.

The other modules import everything from here; the code lives in smaller modules:
    tables_read      the CSV files, trimmed, read whole or filtered on one column
    tables_grouped   the tables kept in memory, whole or grouped by a key column (by_key for any rows)
    tables_formats   CYYMMDD dates
    tables_numbers   integers with implied decimals
    tables_versions  the row of a versioned table valid on a day
    tables_premium   the premium items that were paid and not reversed
"""
from decimal import Decimal as D
from tables_read import stream, matching
from tables_grouped import table, grouped, by_key
from tables_formats import day, legacy
from tables_read import scaled
from tables_read import version
from tables_premium import reversals, received

# Rounding steps for Decimal.quantize: amounts are kept in cents (N(2) columns, commission, projection),
# fund units to six decimals (MICRO, the precision of the units booked in the ledger).
CENT, MICRO = D('.01'), D('.000001')

__all__ = ['stream', 'matching', 'table', 'grouped', 'by_key', 'day', 'legacy', 'scaled', 'version', 'reversals', 'received',
           'CENT', 'MICRO']
