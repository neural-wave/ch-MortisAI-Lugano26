"""The conventions a legacy system may have used, as small functions: the dictionary of the rule search.

Each conventions_*.py module holds one topic and its families; this module gathers the families. rules.py
names the bricks Neuron used, imported from their own modules; the search in vocabulary/ tries every brick of
a family and keeps the one that matches the targets exactly. A family lists its options from the simplest to
the most special, because the search keeps the earlier option when two explain the data equally well.
A new idea is one more function in its family: the search tries it on the next run.
"""
from conventions_rounding import ROUNDINGS  # noqa: F401 (the families, gathered for the search)
from conventions_dates import PREMIUM_DATES  # noqa: F401
from conventions_age import AGES  # noqa: F401
from conventions_rounding import ATTAINED_AGES  # noqa: F401
from conventions_birth import BIRTH_DATES  # noqa: F401
from conventions_calendar import SHIFTS  # noqa: F401
from conventions_steps import PAST_DUE  # noqa: F401
from conventions_anchor import ANCHOR_DAYS  # noqa: F401
from conventions_steps import ORIGINS, STEPS  # noqa: F401
from conventions_offer import OFFER_VERSIONS, OFFER_DATES  # noqa: F401
from conventions_period import TERMS  # noqa: F401
from conventions_period import ORDERS  # noqa: F401
from conventions_fees import ADMIN_MONTHS, FLOORS  # noqa: F401
from conventions_offer import AMC_RATES  # noqa: F401
from conventions_period import AMC_PERIODS  # noqa: F401
from projection_month import GROWTH, ROUNDING_STEPS  # noqa: F401
from conventions_trade import TRADE_DATES, PRICES  # noqa: F401
from conventions_fx_dates import PREMIUM_FX_DATES, CHARGE_FX_DATES  # noqa: F401
from ledger_premium import RATE_LOOKUPS, CROSS_RATES  # noqa: F401
from ledger_parts import SPLITS  # noqa: F401
from conventions_fx_dates import ENTRY_AMOUNTS  # noqa: F401
from conventions_pot import ALLOCATION_ROWS, POT_BOUNDARIES  # noqa: F401
from conventions_charge_age import TARIFF_DAYS  # noqa: F401
from conventions_charge_age import ADMIN_CAPS  # noqa: F401
from ledger_cancel import MANAGEMENT_BASES, RISK_BASES  # noqa: F401
from conventions_rest import SPLIT_RESTS  # noqa: F401
from conventions_day_count import AMC_AGREEMENTS  # noqa: F401
from conventions_day_count import DAY_COUNTS  # noqa: F401
from charges_risk import LOADINGS, MONTHLY_RATES  # noqa: F401
from conventions_charge_age import CHARGE_AGES  # noqa: F401
from ledger_dates import DAY_ORDERS  # noqa: F401
from conventions_schedule import SLOT_VALUES  # noqa: F401
from conventions_schedule import SCHEDULES  # noqa: F401
from conventions_schedule import CLOSINGS  # noqa: F401
from conventions_valuation import VALUATION_TIMES, POLICY_VALUES  # noqa: F401
from conventions_penalty import PENALTY_YEARS, WAIVERS  # noqa: F401
from accounts_surrender import END_YEARS  # noqa: F401
