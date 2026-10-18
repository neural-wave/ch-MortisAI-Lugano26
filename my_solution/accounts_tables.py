"""The t3 and t4 result tables, read from a replay of all policies (see accounts.accounts).

t4 has one row per policy and calendar year, from the start year to the
year of a surrender or death claim, at the latest 2025 (Ledger.last_year);
years without any booking still get a row of zeros.
"""
from accounts_surrender import surrender_value


def surrender_table(folder, replays):
    """{(policy, valuation date): surrender value} for every value of the replay."""
    result = {}
    for pid, (ledger, values) in replays.items():
        for date, value in values.items():
            result[pid, date] = surrender_value(folder, ledger, date, value)
    return result


def yearly_rows(replays):
    """{(policy, year): (premiums, entry, admin, management, risk, total charges)}.

    Ledger.annual[year] holds the first five as booked; total charges is
    the sum of the four charges, without the premiums.
    """
    result = {}
    for pid, (ledger, _) in replays.items():
        for year in range(ledger.start.year, ledger.last_year() + 1):
            premiums, *charges = ledger.annual[year]
            result[pid, year] = (premiums, *charges, sum(charges))
    return result
