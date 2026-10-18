"""t3 surrender value: the policy value less a penalty for early surrender, by the choices of ledger.rule.

The penalty rate comes from NRSURR by the product's surrender scale (NRPROD.PD_SRPSCL) and the policy years
counted as rule.T3_PENALTY_YEARS says (completed policy years); it falls each year (scale 1: 50 % in year 0
down to 10 % in year 4) and is nil once the scale has no row for the year. In a waiver period of NRWAIV
(rule.T3_WAIVER: financial crisis 2008, COVID-19 2020) no penalty applies: 2,392 of the 2,399 train valuations
in those periods equal their policy value. The result is rounded by rule.T3_SURRENDER_ROUNDING of the era.

The last year of the annual statements (t4): the year a policy ends by surrender or death, at the latest 2025.

The policy ends in the year of the first version in state 60 or 70 (its validity start PH_VLDFR), or in the
year that version was processed (PH_CHGTS). Checked on the years of every train policy in t4_annual_statement.csv.
"""
from decimal import Decimal as D
from tables import table, scaled
from tables import day
from conventions_schedule import CLOSED


def penalty_rate(folder, ledger, date):
    """The NRSURR rate (6 implied decimals) for the policy years on `date`, else 0."""
    years = ledger.rule.T3_PENALTY_YEARS(ledger.start, date)
    rows = [r for r in table(folder, 'NRSURR')
            if r['SR_SCALE'] == ledger.product['PD_SRPSCL'] and int(r['SR_YEAR']) == years]
    return scaled(rows[0]['SR_RATE']) if rows else D(0)


def surrender_value(folder, ledger, date, value):
    """Policy value less the penalty, never negative: the one train policy whose charges exceed its units has 0."""
    rule = ledger.rule
    rate = D(0) if rule.T3_WAIVER(folder, date) else penalty_rate(folder, ledger, date)
    rounding = ledger.era(rule.T3_SURRENDER_ROUNDING, rule.T3_SURRENDER_ERA_DATE, date)
    return max(D(0), rounding(value * (1 - rate), date))


def first_closed_version(history):
    """The year of the earliest PH_VLDFR of a version in state 60 or 70, or None."""
    years = [day(r['PH_VLDFR']).year for r in history if r['PH_STATE'] in CLOSED]
    return min(years) if years else None


def closed_version_processed(history):
    """The year the first closed version was processed (PH_CHGTS), or None."""
    years = [int(r['PH_CHGTS'][:4]) for r in history if r['PH_STATE'] in CLOSED]
    return min(years) if years else None


END_YEARS = {'the first closed version': first_closed_version, 'its processing year': closed_version_processed}
