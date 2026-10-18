"""t7: the NRTAXR row of a tax: by country and tax type, valid on the day and known as rules.py T7_RATE_KNOWN says.

The region's own row wins over the row for all regions (church tax: 8 % in Bavaria and Baden-Wuerttemberg, 9 %
elsewhere), then the highest version. A version entered later is a correction booked on its own (the Italian stamp
duty of 2017-2019, raised on 2019-07-15 and booked by run TAXFIX19).
"""
from functools import cache
import rules
from tables import table
from tax_gain import known


@cache
def rows_of(folder):
    """{(country, tax type): rows} of NRTAXR."""
    result = {}
    for row in table(folder, 'NRTAXR'):
        result.setdefault((row['TX_CNTRY'], row['TX_TAXTP']), []).append(row)
    return result


def row_of(folder, country, kind, date, processed, region):
    """The NRTAXR row that applies, or None: the region's own row if one is valid and known, else the row for
    all regions (tax_versions.known picks the highest valid version of either)."""
    rows = rows_of(folder).get((country, kind), [])
    own = known([r for r in rows if region and r['TX_REGIO'] == region], date, 'TX', rules.T7_RATE_KNOWN(processed))
    return own or known([r for r in rows if not r['TX_REGIO']], date, 'TX', rules.T7_RATE_KNOWN(processed))
