"""The growth of an offer month (t2) and where a step of the month is rounded.

The yearly illustration rate (NRILLU) becomes a monthly factor as a twelfth (1 + r / 12) or compounded
((1 + r) ** (1 / 12)). A step of the month (the net premium, a charge, the growth) is rounded to the cent by
the rule of its era (rules.py ERA_ROUNDING, passed in as `rounding`) or kept exact until a later step.

One month of the offer projection (t2): the steps in the order rule.T2_ORDER, each done the rule's way.

`rule` is the rules module (or, in the rule search, a trial of choices with the same names), `terms` the Offer
of projection_offer. The order found: premium, admin fee, management charge, risk charge, growth; tried
against all 48 orders on every policy year of t2_projection_year.csv, each year started from its expected value.
"""
from decimal import Decimal as D
from tables import scaled
from conventions_fees import management, risk


def twelfth_growth(rate):
    """The monthly growth factor 1 + rate / 12."""
    return 1 + rate / 12


def compounded_growth(rate):
    """The monthly growth factor (1 + rate) ** (1 / 12)."""
    return (1 + rate) ** (D(1) / 12)


def to_the_cent(value, date, rounding):
    """The step is rounded by the rule of its era."""
    return rounding(value, date)


def kept_exact(value, date, rounding):
    """The step is not rounded."""
    return value


GROWTH = {'yearly rate / 12': twelfth_growth, 'compounded': compounded_growth}
ROUNDING_STEPS = {'to the cent (era rule)': to_the_cent, 'kept exact': kept_exact}


def premium(value, month, terms, rule):
    """The premium of the month, when one is due (every `terms.every` months; a single premium once)."""
    return value + terms.net if month % terms.every == 0 else value


def admin(value, month, terms, rule):
    """The monthly admin fee CG_ADMFEE (cents), in the months rule.T2_ADMIN_MONTHS names."""
    fee = scaled(terms.charges['CG_ADMFEE'], 2)
    return rule.T2_FLOOR(value, fee) if rule.T2_ADMIN_MONTHS(month, terms.every) else value


def growth(value, month, terms, rule):
    """The growth of the month at the illustration rate, rounded as rule.T2_GROWTH_ROUNDING says."""
    return rule.T2_GROWTH_ROUNDING(value * terms.growth, terms.applied, terms.rounding)


STEPS = {'premium': premium, 'admin': admin, 'management': management, 'risk': risk, 'growth': growth}


def advance(value, month, terms, rule):
    """The value after policy month `month` (0 = the first month of the term)."""
    for step in rule.T2_ORDER:
        value = STEPS[step](value, month, terms, rule)
    return value
