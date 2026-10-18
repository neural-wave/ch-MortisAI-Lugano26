"""The offer month's charges on the fund value (t2), each rounded to cents on its own (eras.rounded)."""
from tables import scaled
from eras import rounded
from tariff import risk_amount, risk_rate


def management_charge(value, terms):
    """A twelfth of the yearly charge at the pot 2 rate NRCHRG.CG_AMCP2.

    The offer has no initial units (pot 1); all 30 best of the 1,800 searched conventions use CG_AMCP2.
    """
    rate = scaled(terms.charges['CG_AMCP2'])
    return rounded(value * rate / 12, terms.applied)


def risk_charge(value, month, terms):
    """Sum at risk (by the benefit option, last character of RK_TARKEY) times the monthly rate.

    The rate is taken at entry age plus completed policy years: it changes on the anniversary,
    not on the birthday of the insured person.
    """
    rate = risk_rate(terms.risk, terms.person, terms.charges, terms.mortality, terms.age + month // 12)
    insured = scaled(terms.risk['RK_SUMIN'], 2)
    return rounded(risk_amount(value, insured, terms.risk['RK_TARKEY'][-1]) * rate, terms.applied)
