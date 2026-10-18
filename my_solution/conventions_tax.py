"""t7: how Neuron's tax module reads its own records: which tax it booked, which versions it knew, which day rounds.

NRTAXB lists every tax Neuron booked (without the amount); NRHOLD, NRADDR and NRTAXR are versioned twice: valid from
and to a day, and entered at a time (`_CHGTS`). Neuron could only use what it had been told when it processed a
payout, so a move or a rate entered later counts only from then (a later rate is booked as a correction, TAXFIX19).
"""


def as_booked(found, rule, processed):
    """NRTAXB decides: taxed if Neuron booked the tax, at the time of its first booking (its mistakes included)."""
    return bool(found), found[0].processed if found else processed


def by_the_rules(found, rule, processed):
    """The rules found in the data decide (for an extract without NRTAXB), at the time the payout was processed."""
    return rule(), processed


def when_processed(at):
    """The versions entered by the time Neuron processed the payout or booked the tax."""
    return at


def as_known_today(at):
    """Every version, as the extract knows them today."""
    return None


TAX_PRESENCE = {'as booked in NRTAXB': as_booked, 'by the rules found': by_the_rules}
KNOWN_VERSIONS = {'as known when processed': when_processed, 'as known today': as_known_today}
