"""t2: the maturity value projected in the offer, by the rules found in the data (rules.py, T2_*).

The terms are read in projection_offer and each month is calculated in projection_month; both take the rules
as an argument, so the rule search runs the very same code with its trial choices. Results go to
t2_projected_maturity_value.csv and the diagnostic t2_projection_year.csv; 3,011 of the 3,019 expected
maturity values match to the cent, the other 8 are manual corrections (t5).
"""
from decimal import Decimal as D, ROUND_HALF_UP
from functools import cache
import rules
from tables import grouped, CENT
from eras import by_era
from projection_offer import offer
from projection_month import advance
from guard import per_policy


def era_of(date):
    """The rounding and the age rule of the system live on `date` (rules.ERA_ROUNDING, rules.ERA_AGE)."""
    return by_era(rules.ERA_ROUNDING, date), by_era(rules.ERA_AGE, date)


def project(folder, history):
    """Maturity value of one policy and its value at the end of every policy year."""
    terms = offer(folder, history, rules, era_of)
    value, months = D(0), []
    for month in range(terms.months):
        value = advance(value, month, terms, rules)
        months.append(value)
    return value.quantize(CENT, rounding=ROUND_HALF_UP), dict(enumerate(months[11::12], 1))


@cache
def projections(folder):
    """Maturity values by policy and the yearly values by (policy, policy year)."""
    offers = per_policy('t2_projected_maturity_value', grouped(folder, 'NRPOLH', 'PH_POLNR').items(),
                        lambda pid, history: {pid: project(folder, history)})
    values = {pid: value for pid, (value, _) in offers.items()}
    yearly = {(pid, year): amount for pid, (_, years) in offers.items() for year, amount in years.items()}
    return values, yearly
