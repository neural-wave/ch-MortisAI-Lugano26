"""t3 and t4: the fund accounting of every policy, its surrender values and its annual statements.

Both tasks read the same replay of the policies (see ledger.Ledger), so
the replay is cached and run once per set of valuation dates.
"""
from tables import grouped, by_key, received
from orders import customer_orders
from accounts_replay import replay
from accounts_tables import surrender_table, yearly_rows
from guard import per_policy

# (folder, valuation dates) -> replay, filled by `accounts`. The replay is
# the slow part of t3 and t4, so it runs once per folder, not once per task.
REPLAYS = {}


def accounts(folder, dates):
    """Replay every policy once: {policy: (ledger, {valuation date: policy value})}.

    `dates` is a tuple; a policy is valued only on the dates from its start on.
    Valuing a policy does not change its units, so any replay of the folder
    serves the statements too, and t4 after t3 costs no second replay.
    A policy whose replay fails is left out of both tasks (guard.per_policy).
    """
    if (folder, dates) not in REPLAYS:
        orders, premiums = customer_orders(folder), by_key(received(folder), 'PR_POLNR')
        REPLAYS[folder, dates] = per_policy(
            't3_surrender_value/t4_annual_statement', grouped(folder, 'NRPOLH', 'PH_POLNR').items(),
            lambda pid, _: {pid: replay(folder, pid, premiums[pid], orders[pid], dates)})
    return REPLAYS[folder, dates]


def any_replay(folder):
    """A replay of the folder that was already run, or a new one without valuation dates."""
    done = [result for (replayed, _), result in REPLAYS.items() if replayed == folder]
    return done[0] if done else accounts(folder, ())


def surrender_values(folder, dates):
    """{(policy, valuation date): surrender value}; the penalty rules are in accounts_surrender."""
    return surrender_table(folder, accounts(folder, tuple(dates)))


def statements(folder):
    """{(policy, year): (premiums, entry, admin, management, risk, total charges)}.

    Any replay of the folder will do: the yearly totals do not depend on the valuation dates.
    """
    return yearly_rows(any_replay(folder))
