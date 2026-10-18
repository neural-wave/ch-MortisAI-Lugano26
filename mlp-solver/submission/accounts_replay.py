"""The replay of one policy on a fresh ledger, from its premiums grouped once for the whole folder
(tables.received grouped by PR_POLNR, in NRPREM order)."""
import rules
from ledger import Ledger


def replay(folder, pid, premiums, orders, dates):
    """One policy: its ledger after the replay, and its values on the dates from its start on."""
    ledger = Ledger(folder, pid, rules)
    # The t3 valuation dates are those of all policies together (see
    # scoring.arguments), so each policy keeps only those from its start.
    return ledger, ledger.run(premiums, orders, [d for d in dates if d >= ledger.start])
