"""Death benefit option of the tariff (RK_TARKEY position 7) and the sum at risk it puts on the fund.

Dated tariff rates (NRCHRG charges, NRENTC entry charge); tables.version picks the valid row.
"""
from decimal import Decimal as D
from tables import table, version, scaled


def risk_amount(value, insured, option):
    """Sum at risk by option. A pays 101 % of the fund value: 1 % is at risk. B pays the higher of
    sum insured and value: the excess of the sum insured, never below 0. C pays value plus sum insured:
    the sum insured."""
    if option == 'A':
        return value * D('.01')
    return max(D(0), insured - value) if option == 'B' else insured


def charge_parameters(folder, tariff, date):
    """NRCHRG row valid on `date`: admin fee, management charges, smoker factor, mortality table.

    Keyed by tariff family (RK_TARKEY positions 1-2) and generation (4-5); the sex basis does not matter.
    """
    family, generation = tariff[:2], tariff[3:5]
    rows = [r for r in table(folder, 'NRCHRG') if r['CG_TARFAM'] == family and r['CG_TARGEN'] == generation]
    return version(rows, date, 'CG')


def entry_rate(folder, tier, date):
    """NRENTC entry charge rate of the broker tier valid on `date`: A pays 5 % and C 2 % throughout,
    B fell from 4 % to 3 % on 2021-07-01, so pass the premium's date."""
    rows = [r for r in table(folder, 'NRENTC') if r['EC_TIER'] == tier]
    return scaled(version(rows, date, 'EC')['EC_RATE'])
