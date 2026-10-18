"""General candidate conventions for tax years and banking calendars. No sample values."""
import datetime as dt
from conventions_holidays import business_day, TICINO, EASTER_TICINO
from decimal import Decimal as D, ROUND_HALF_UP


def payout_year(payout, country):
    return payout.date.year


def remittance_year(payout, country):
    from tax_annual_table import remittance
    return remittance(country, payout.date).year


def next_tax_business_day(date):
    # The two-day New Year closure is a candidate, selected against known examples.
    return business_day(date, (*TICINO, (1, 2)), EASTER_TICINO)


def unchanged_exemption(value):return value
def no_partial_exemption(value):return D(0)


def death_benefit_cent(folder,head,value):
    from conventions_tax_payout import the_death_benefit
    return the_death_benefit(folder,head,value).quantize(D('.01'),rounding=ROUND_HALF_UP)


def surcharge_on_withheld(tax,exact,rate,rounding):return rounding(tax*rate)
def surcharge_on_exact(tax,exact,rate,rounding):return rounding(exact*rate)
