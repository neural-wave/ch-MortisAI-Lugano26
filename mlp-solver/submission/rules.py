"""Frozen runtime selections. Shared rules selected on search policies only.
Reserved-policy results are in verification.json; tax rules are inherited from submission 68.
Exactness outside supplied examples is not proved. No target outputs are stored here.
"""
from datetime import date
from accounts_surrender import first_closed_version
from charges_risk import multiplied, twelfth_of_qx
from conventions_age import days_365, nearest_birthday
from conventions_anchor import highest_recent_day
from conventions_birth import clamp_to_month_end
from conventions_calendar import next_business_day_ticino, same_day
from conventions_charge_age import at_most_the_value, at_the_last_anniversary, on_the_charge_date
from conventions_dates import money_date
from conventions_day_count import a_twelfth, actual_days_360, agreement_for_both_pots
from conventions_fees import every_month, never_below_zero
from conventions_fx_dates import day_before_trade, on_charge_date, share_less_invested
from conventions_offer import first_version, on_application_date, on_start_date, pot_2_rate
from conventions_penalty import completed_policy_years, waiver_periods_apply
from conventions_period import calendar_months, twelfth_of_a_year
from conventions_pot import before_the_end, valid_on_the_date
from conventions_rest import largest_never_negative
from conventions_rounding import half_up, on_the_day, policy_year_age, truncate
from conventions_schedule import before_maturity, closed_on_the_day, rounded_value
from conventions_steps import all_items_due, clamped_step, from_last_due_date
from conventions_tax import as_booked, when_processed
from conventions_tax_bases import reported_in_new_years, the_payout
from conventions_tax_germany import halved, lowered_by_church_tax
from conventions_tax_payout import after_the_surrender_penalty, the_death_booking
from conventions_tax_premium import received_amount, share_to_the_cent
from conventions_tax_remit import empty_text, sixteenth_of_next_month, tenth_of_next_month, thirty_days_after_month_end
from conventions_tax_rows import dated, in_full, the_signed_gain
from conventions_tax_share import days_share, the_surrender_value, withdrawn_share
from conventions_trade import issue_price, next_price_date, redemption_price
from conventions_valuation import after_every_booking, sum_of_the_slots
from ledger_cancel import before_the_charges, less_the_charges
from ledger_dates import charges_before_trades
from ledger_parts import share_then_net
from ledger_premium import exact_cross_rate, rate_on_or_before
from projection_month import to_the_cent, twelfth_growth
from conventions_day_count import a_twelfth
from conventions_day_count import actual_days_360
from conventions_valuation import after_every_booking
from conventions_day_count import agreement_for_both_pots
from conventions_steps import all_items_due
from conventions_charge_age import at_most_the_value
from conventions_charge_age import at_the_last_anniversary
from conventions_schedule import before_maturity
from ledger_cancel import before_the_charges
from conventions_pot import before_the_end
from conventions_period import calendar_months
from ledger_dates import charges_before_trades
from conventions_birth import clamp_to_month_end
from conventions_steps import clamped_step
from conventions_schedule import closed_on_the_day
from conventions_penalty import completed_policy_years
from conventions_fx_dates import day_before_trade
from conventions_age import days_365
from conventions_fees import every_month
from ledger_premium import exact_cross_rate
from accounts_surrender import first_closed_version
from conventions_offer import first_version
from conventions_steps import from_last_due_date
from conventions_rounding import half_up
from conventions_anchor import highest_recent_day
from conventions_trade import issue_price
from conventions_rest import largest_never_negative
from ledger_cancel import less_the_charges
from conventions_dates import money_date
from charges_risk import multiplied
from conventions_age import nearest_birthday
from conventions_fees import never_below_zero
from conventions_calendar import next_business_day_ticino
from conventions_trade import next_price_date
from conventions_offer import on_application_date
from conventions_fx_dates import on_charge_date
from conventions_offer import on_start_date
from conventions_charge_age import on_the_charge_date
from conventions_rounding import policy_year_age
from conventions_offer import pot_2_rate
from ledger_premium import rate_on_or_before
from conventions_trade import redemption_price
from conventions_schedule import rounded_value
from conventions_calendar import same_day
from conventions_fx_dates import share_less_invested
from ledger_parts import share_then_net
from conventions_valuation import sum_of_the_slots
from projection_month import to_the_cent
from conventions_rounding import truncate
from projection_month import twelfth_growth
from conventions_period import twelfth_of_a_year
from charges_risk import twelfth_of_qx
from conventions_pot import valid_on_the_date
from conventions_penalty import waiver_periods_apply
ERA_CUTOFF = date(2007, 8, 11)
ERA_DATE = on_application_date
ERA_ROUNDING = (truncate, half_up)
ERA_AGE = (days_365, nearest_birthday)
BIRTH_DATE = clamp_to_month_end
T0_ERA_DATE = money_date
T0_DATE = money_date
T0_ROUNDING = (truncate, half_up)
T1_COLLECTION_BY = 'PH_PAYMT'
T1_COLLECTION = {'LS': next_business_day_ticino, 'UB': same_day}
T1_PAST_DUE = all_items_due
T1_ANCHOR_DAY = highest_recent_day
T1_ORIGIN = from_last_due_date
T1_STEP = clamped_step
T3_TRADE_DATE = next_price_date
T3_POT_DATE = money_date
T3_POT_BOUNDARY = before_the_end
T3_AMOUNT_ERA_DATE = on_the_day
T3_ENTRY_DATE = money_date
T3_ALLOCATION_DATE = money_date
T3_ALLOCATION_ROWS = valid_on_the_date
T3_SPLIT = share_then_net
T3_AMOUNT_ROUNDING = (truncate, half_up)
T3_UNITS_ERA_DATE = on_the_day
T3_PREMIUM_PRICE = issue_price
T3_PREMIUM_FX_DATE = day_before_trade
T3_RATE_LOOKUP = rate_on_or_before
T3_CROSS_RATE = exact_cross_rate
T3_UNITS_ROUNDING = (truncate, half_up)
T3_CHARGE_UNITS_ERA_DATE = on_the_day
T3_CHARGE_PRICE = redemption_price
T3_CHARGE_FX_DATE = on_charge_date
T3_CHARGE_UNITS_ROUNDING = (truncate, half_up)
T3_ENTRY_AMOUNT = share_less_invested
T3_CHARGES_ERA_DATE = on_the_day
T3_TARIFF_DAY = on_the_charge_date
T3_CLOSED = closed_on_the_day
T3_ADMIN_CAP = at_most_the_value
T3_MANAGEMENT_BASE = before_the_charges
T3_RISK_BASE = less_the_charges
T3_SPLIT_REST = largest_never_negative
T3_PIECE_ROUNDING = (truncate, half_up)
T3_AMC_RATE = agreement_for_both_pots
T3_DAY_COUNT = (actual_days_360, a_twelfth)
T3_AMC_ROUNDING = (truncate, half_up)
T3_CHARGE_AGE = at_the_last_anniversary
T3_RISK_ROUNDING = (truncate, half_up)
RISK_LOADING = multiplied
RISK_MONTHLY_RATE = twelfth_of_qx
T3_DAY_ORDER = charges_before_trades
T3_SLOT_VALUE = rounded_value
T3_VALUE_ROUNDING = (truncate, half_up)
T3_SCHEDULE = before_maturity
T3_POLICY_VALUE = sum_of_the_slots
T3_VALUATION_TIME = after_every_booking
T3_SURRENDER_ERA_DATE = on_the_day
T3_PENALTY_YEARS = completed_policy_years
T3_WAIVER = waiver_periods_apply
T3_SURRENDER_ROUNDING = (truncate, half_up)
T4_END_YEAR = first_closed_version
T2_VERSION = first_version
T2_PARAMETER_DATE = on_application_date
T2_AGE_AT = on_start_date
T2_TERM = calendar_months
T2_NET_ROUNDING = to_the_cent
T2_GROWTH = twelfth_growth
T2_ORDER = ('premium', 'admin', 'management', 'risk', 'growth')
T2_ADMIN_MONTHS = every_month
T2_FLOOR = never_below_zero
T2_AMC_RATE = pot_2_rate
T2_AMC_PERIOD = twelfth_of_a_year
T2_CHARGE_ROUNDING = to_the_cent
T2_GROWTH_ROUNDING = to_the_cent
T2_ATTAINED_AGE = policy_year_age
T7_PAYOUT_AMOUNT = after_the_surrender_penalty
T7_DEATH_AMOUNT = the_death_booking
T7_PREMIUM_AMOUNT = received_amount
T7_BASIS_SHARE = share_to_the_cent
T7_LOSS_BASE = the_signed_gain
T7_BOC_DATED = dated
T7_BOL_FIRST_YEAR = in_full
T7_PRESENCE = as_booked
T7_RESIDENCE_KNOWN = when_processed
T7_RATE_KNOWN = when_processed
T7_CH_UNTAXED_BASE = the_payout
T7_REPORTED_VST = reported_in_new_years
T7_REMITTANCE = {'DE': tenth_of_next_month, 'IT': sixteenth_of_next_month, 'CH': thirty_days_after_month_end, 'LU': tenth_of_next_month}
T7_REMITTANCE_SHIFT = same_day
T7_NO_REMITTANCE = empty_text
T7_BOL_SHARE = days_share
T7_BOL_VALUE = the_surrender_value
T7_BOC_SHARE = withdrawn_share
T7_KST_CHURCH = lowered_by_church_tax
T7_TFS_WITH_HEV = halved

# Automatically selected tax conventions; public sample scores are in the separate search report.
from tax_search_conventions import payout_year, remittance_year, next_tax_business_day
T7_ANNUAL_YEAR = payout_year

# Selected by bounded public-example calibration, without target lookup at runtime.
from conventions_tax_bases import reported_in_new_years
from conventions_tax_germany import halved, lowered_by_church_tax
from conventions_tax_payout import after_the_surrender_penalty, the_death_benefit
from conventions_tax_premium import received_amount, share_to_the_cent
from conventions_tax_rows import in_full, not_dated, zero_for_a_loss
from conventions_tax_share import days_share, the_policy_value, withdrawn_share
from tax_search_conventions import next_tax_business_day, remittance_year
T7_LOSS_BASE = zero_for_a_loss
T7_BOC_DATED = not_dated
T7_REMITTANCE_SHIFT = next_tax_business_day
T7_DEATH_AMOUNT = the_death_benefit
T7_ANNUAL_YEAR = remittance_year
T7_PAYOUT_AMOUNT = after_the_surrender_penalty
T7_BOL_VALUE = the_policy_value
T7_BOL_FIRST_YEAR = in_full
T7_BOC_SHARE = withdrawn_share
T7_BOL_SHARE = days_share
T7_BASIS_SHARE = share_to_the_cent
T7_PREMIUM_AMOUNT = received_amount
T7_KST_CHURCH = lowered_by_church_tax
T7_TFS_WITH_HEV = halved
T7_REPORTED_VST = reported_in_new_years

from tax_italy_history import flat_rate
from tax_search_conventions import unchanged_exemption, surcharge_on_withheld
T7_IT_TAX = flat_rate
T7_TFS_EXEMPT = unchanged_exemption
T7_SURCHARGE = surcharge_on_withheld

# Selected by bounded public-example calibration, without target lookup at runtime.
from conventions_tax_bases import reported_in_new_years
from conventions_tax_germany import halved, lowered_by_church_tax
from conventions_tax_payout import after_the_surrender_penalty
from conventions_tax_premium import received_amount, share_to_the_cent
from conventions_tax_rows import in_full, not_dated, zero_for_a_loss
from conventions_tax_share import days_share, the_policy_value, withdrawn_share
from tax_italy_history import historical_signed
from tax_search_conventions import death_benefit_cent, next_tax_business_day, no_partial_exemption, remittance_year, surcharge_on_withheld
T7_IT_TAX = historical_signed
T7_TFS_EXEMPT = no_partial_exemption
T7_SURCHARGE = surcharge_on_withheld
T7_LOSS_BASE = zero_for_a_loss
T7_BOC_DATED = not_dated
T7_REMITTANCE_SHIFT = next_tax_business_day
T7_DEATH_AMOUNT = death_benefit_cent
T7_ANNUAL_YEAR = remittance_year
T7_PAYOUT_AMOUNT = after_the_surrender_penalty
T7_BOL_VALUE = the_policy_value
T7_BOL_FIRST_YEAR = in_full
T7_BOC_SHARE = withdrawn_share
T7_BOL_SHARE = days_share
T7_BASIS_SHARE = share_to_the_cent
T7_PREMIUM_AMOUNT = received_amount
T7_KST_CHURCH = lowered_by_church_tax
T7_TFS_WITH_HEV = halved
T7_REPORTED_VST = reported_in_new_years
