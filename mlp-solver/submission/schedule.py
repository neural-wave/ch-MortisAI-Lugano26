"""t1: the premium due dates of the next year and the days the money is collected."""
from tables import grouped, version
from conventions_steps import FREQUENCY, premium_paying  # noqa: F401 (FREQUENCY re-exported)
from schedule_cycle import upcoming, collection
from guard import per_policy


def due_dates(folder, extract_date):
    """{(policy, n): (due date, collection date)} for the year after the extract date.

    Only the policy version valid on the extract date (NRPOLH) decides; n counts from 1 per policy.
    Matches all 15,028 train rows of 1,648 policies.
    """
    premiums = grouped(folder, 'NRPREM', 'PR_POLNR')
    return per_policy('t1_next_due_dates', grouped(folder, 'NRPOLH', 'PH_POLNR').items(),
                      lambda pid, history: policy_dates(pid, history, premiums[pid], extract_date))


def policy_dates(pid, history, premiums, extract_date):
    """{(policy, n): (due date, collection date)} of one policy; none unless it pays premiums on the extract date."""
    policy = version(history, extract_date, 'PH')
    if not premium_paying(policy):
        return {}
    dates = upcoming(policy, premiums, extract_date)
    return {(pid, n): (date, collection(policy, date)) for n, date in enumerate(dates, 1)}
