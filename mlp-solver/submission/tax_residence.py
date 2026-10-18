"""t7: a tax rate and a threshold as numbers: TX_RATE has 6 implied decimals (25000 is 2.5 %), TX_THRSH 2 (500000
is 5000.00, the Swiss withholding tax). No row on the day (a tax not in force yet) means a rate of 0.

t7: where the policyholder lived when Neuron taxed a payout: the holder (NRHOLD), then the address (NRADDR).

The address gives the country, the region, the reporting status (M reported to the tax office, E objection) and the
church membership. The versions are those of rules.py T7_RESIDENCE_KNOWN (known when the payout was processed): then
all 5,919 Italian stamp duty bookings of NRTAXB find a holder in Italy; with the versions known today, 12 do not.
"""
from decimal import Decimal as D
from tables import scaled
from tax_rate_rows import row_of
from collections import namedtuple
from functools import cache
import rules
from tables import grouped
from tax_gain import known


def rate(folder, country, kind, date, processed=None, region=''):
    """The rate as a fraction (0.25 for 25 %), 0 when no row applies."""
    row = row_of(folder, country, kind, date, processed, region)
    return scaled(row['TX_RATE']) if row else D(0)


def threshold(folder, country, kind, date, processed=None):
    """The threshold in the tax currency, 0 when there is none."""
    row = row_of(folder, country, kind, date, processed, '')
    return scaled(row['TX_THRSH'] or 0, 2) if row else D(0)


Residence = namedtuple('Residence', 'person country region reporting church')
NOWHERE = Residence('', '', '', '', False)


@cache
def residence(folder, policy, date, processed=None):
    """The Residence of the policy's holder on `date`, as Neuron knew it at `processed`: first the holder version,
    then that person's address version, both as rules.py T7_RESIDENCE_KNOWN says."""
    at = rules.T7_RESIDENCE_KNOWN(processed)
    holder = known(grouped(folder, 'NRHOLD', 'HD_POLNR')[policy], date, 'HD', at)
    address = holder and known(grouped(folder, 'NRADDR', 'AD_PERNR')[holder['HD_PERNR']], date, 'AD', at)
    if not address:
        return NOWHERE
    return Residence(holder['HD_PERNR'], address['AD_CNTRY'], address['AD_REGIO'], address['AD_TAXST'],
                     address['AD_CHURCH'] == 'J')
