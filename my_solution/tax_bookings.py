"""t7: Neuron's tax bookings (NRTAXB): which tax it booked on which event, when, and by which user.

The amount and the remittance date are empty in the extract: they are what t7 calculates. The yearly Italian stamp
duty (batch TAXBATCH) and its 2019 correction (TAXFIX19) have event 0; a payout's taxes carry its event number.
"""
from collections import defaultdict, namedtuple
from functools import cache
from tables import table, day
from tax_times import timestamp

Booking = namedtuple('Booking', 'policy event kind date processed user')


@cache
def bookings(folder):
    """{(policy, event): {tax type: [Booking]}}."""
    result = defaultdict(dict)
    for row in table(folder, 'NRTAXB'):
        b = Booking(row['TB_POLNR'], int(row['TB_EVTNR']), row['TB_TAXTP'], day(row['TB_EFFDT']),
                    timestamp(row['TB_CHGTS']), row['TB_USRID'])
        result[b.policy, b.event].setdefault(b.kind, []).append(b)
    return result


def booked(folder, policy, event, kind):
    """The bookings of one tax at one event, oldest first (empty if Neuron booked none)."""
    return sorted(bookings(folder).get((policy, event), {}).get(kind, []), key=lambda b: b.processed)
