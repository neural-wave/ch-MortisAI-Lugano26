"""The monthly risk charge per unit at risk; the sum at risk itself is in tariff_benefit.
Called per policy month by the ledger (charges_risk) and the offer (projection_month)."""
from decimal import Decimal as D
from tables import scaled

# Tariff key position 3 -> MO_SEX (1 male, 2 female); U = unisex is absent: the person's PS_SEX applies.
SEX_BASIS = {'M': '1', 'W': '2'}
# PS_SMOKE is documented as Y/N, but the extract stores the German 'J' (749 of 4,330 persons).
SMOKER = ('J', 'Y')
LAST_AGE = 110  # last age of NRMORT; older insured persons keep the qx of age 110


def risk_rate(risk, person, charges, mortality, age, rule):
    """Monthly risk charge per unit at risk: the qx of table CG_MORTTB, loaded by rule.RISK_LOADING (medical
    loading RK_LOAD and, for a smoker, CG_SMKFAC) and made monthly by rule.RISK_MONTHLY_RATE.

    A missing qx counts as 0. The rate stays unrounded; charges and projection round the charge."""
    sex = SEX_BASIS.get(risk['RK_TARKEY'][2], person['PS_SEX'])
    qx = mortality.get((charges['CG_MORTTB'], sex, min(LAST_AGE, age)), D(0))
    factor = scaled(charges['CG_SMKFAC']) if person['PS_SMOKE'] in SMOKER else 1
    return rule.RISK_MONTHLY_RATE(qx * rule.RISK_LOADING(scaled(risk['RK_LOAD']), factor))
