"""Tariff parameters of a policy: risks, persons, broker tiers and mortality, read once per folder.
Dated rates (tariff_rates) and the risk charge (tariff_risk, tariff_benefit) are re-exported."""
from functools import cache
from tables import table, scaled
from tariff_rates import charge_parameters, entry_rate  # noqa: F401 (re-exported)
from tariff_risk import risk_rate  # noqa: F401 (re-exported)
from tariff_rates import risk_amount  # noqa: F401 (re-exported)


def main_risks(folder):
    """NRRISK rows by policy number, main risk (RK_RSKNR = 1) only.

    The extract holds no riders (all 4,011 rows are risk 1); the filter guards a later extract.
    """
    return {r['RK_POLNR']: r for r in table(folder, 'NRRISK') if r['RK_RSKNR'] == '1'}


def mortality_rates(folder):
    """NRMORT qx keyed by (MO_TABID, MO_SEX, MO_AGE); tables M94U and M12U, ages 0 to 110."""
    return {(r['MO_TABID'], r['MO_SEX'], int(r['MO_AGE'])): scaled(r['MO_QX']) for r in table(folder, 'NRMORT')}


@cache
def parameters(folder):
    """(main risks, NRPERS persons, NRBROK broker tiers A/B/C, qx); callers unpack this order."""
    persons = {r['PS_PERNR']: r for r in table(folder, 'NRPERS')}
    tiers = {r['BR_BRKNR']: r['BR_TIER'] for r in table(folder, 'NRBROK')}
    return main_risks(folder), persons, tiers, mortality_rates(folder)
