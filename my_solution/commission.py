"""t0: the commission a broker earns on every premium received.

The received amount PR_AMTRC times the NRCOMR rate of the broker tier and the premium type. Which date
selects the broker and the rate, and how the amount is rounded, is chosen in rules.py (found by the search:
the money date; half up, and truncation before the conversion, see rules.py). Each policy is calculated on its own (guard.per_policy), so one bad policy costs
only its rows.
"""
from tables import table, grouped, by_key, scaled, version, received
from rules import T0_DATE, T0_ERA_DATE, T0_ROUNDING
from eras import by_era
from tariff import parameters
from commission_rates import commission_rate
from guard import per_policy


def commissions(folder):
    """{(policy, due nr): commission} for every received, not reversed premium (tables.received).

    PR_AMTRC times the rate, rounded by the T0_ROUNDING of the system live on T0_ERA_DATE. The broker is the one
    of the policy version valid on T0_DATE (the money date PR_RCVDT), so a late broker change counts from then.
    Matches 225,848 of 225,858 train rows; the other 10 are manual corrections (t5 outliers).
    Before the 2007-08-11 conversion no train row tells half up from truncation (none of the 29,469 has a
    third decimal of 5 or more), so the rounding of the COBOL years is the simplest option, not a finding.
    """
    return per_policy('t0_commission', by_key(received(folder), 'PR_POLNR').items(),
                      lambda pid, premiums: policy_commissions(folder, pid, premiums))


def policy_commissions(folder, pid, premiums):
    """{(policy, due nr): commission} of the received premiums of one policy."""
    history = grouped(folder, 'NRPOLH', 'PH_POLNR')[pid]
    risks, _, brokers, _ = parameters(folder)
    rates = table(folder, 'NRCOMR')
    kind = risks[pid]['RK_TARKEY'][5]  # premium type at tariff key position 6
    result = {}
    for premium in premiums:
        date = T0_DATE(premium, history)
        tier = brokers[version(history, date, 'PH')['PH_BRKNR']]
        amount = scaled(premium['PR_AMTRC'], 2) * commission_rate(rates, tier, kind, date)
        result[pid, int(premium['PR_DUENR'])] = by_era(T0_ROUNDING, T0_ERA_DATE(premium, history))(amount, date)
    return result
