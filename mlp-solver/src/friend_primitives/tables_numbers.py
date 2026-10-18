"""Neuron's `N(scale)` columns (SCHEMA.md, "Conventions"): integers whose last `scale` digits are decimals.
N(2) for amounts (123456 is 1234.56), N(6) for rates, shares and fund units (12500 is 0.0125). They are
decoded into Decimal, never float, so every fee and unit comes out to the cent the legacy system booked."""
from functools import cache
from decimal import Decimal as D


@cache  # the same rates and fees are decoded every month for every policy
def scaled(value, scale=6):
    """An `N(scale)` column as an exact Decimal; N(6), the default, is the scale of rates and units."""
    return D(value) / (10 ** scale)
