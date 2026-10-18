"""Rules of Neuron found by autosolve.py: generated, do not edit by hand (run `python3 autosolve.py`).

Each choice was picked by an exact-match search over the families of conventions.py: every combination
is scored by the rows it matches to the cent or the day, the simplest of the best wins, and 20 % of the
policies are held out of the search to check the winner. A pair is (COBOL system, Neuron NG): the era
of the calculation decides. "Not distinguishable on train" marks a choice the train rows cannot make;
it follows the rule of the same era in the other calculations, else the simplest option, and may matter
on unseen policies.
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
from conventions_tax_found import (
    before_the_penalty, by_rate_periods, cut_to_the_cent, in_the_remittance_year, on_the_premium_day,
    open_premiums_and_share_left, the_rate_raise_rounded_once,
)
from conventions_tax_germany import lowered_by_church_tax, no_exemption
from conventions_tax_payout import after_the_surrender_penalty, the_death_benefit
from conventions_tax_premium import received_amount, share_to_the_cent
from conventions_tax_remit import (
    empty_text, office_business_day, sixteenth_of_next_month, tenth_of_next_month,
    thirty_days_after_month_end,
)
from conventions_tax_rows import in_full, not_dated, zero_for_a_loss
from conventions_tax_share import days_share, the_policy_value, withdrawn_share
from conventions_trade import issue_price, next_price_date, redemption_price
from conventions_valuation import after_every_booking, sum_of_the_slots
from ledger_cancel import before_the_charges, less_the_charges
from ledger_dates import charges_before_trades
from ledger_parts import share_then_net
from ledger_premium import exact_cross_rate, rate_on_or_before
from projection_month import to_the_cent, twelfth_growth

# the era of Neuron (from the offers of t2, policy years 1 and 2)
# 3,019 rows; the best single rule fits 73.0514 % of the search rows, 70.6755 % held out.
# The diagnosis splits on application date < 2007-08-11 (the last value before it: 2007-08-06); moved onto 2007-08-11, the only day of all events 800 (NREVNT).
# COBOL (application date < 2007-08-11): 829 rows, 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (COBOL): birth date clamp to the month end = roll into the next month; chosen clamp to the month end (consistent with the month ends of every schedule (dates.add_months)).
# Neuron NG (application date >= 2007-08-11): 2,190 rows, 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (Neuron NG): birth date clamp to the month end = roll into the next month; chosen clamp to the month end (consistent with the month ends of every schedule (dates.add_months)).
# The day of the era (ERA_DATE): application date (3,019 exact rows); start date: 3,011 (8 rows in the other era).
ERA_CUTOFF = date(2007, 8, 11)  # the first day of Neuron NG; before it the COBOL system
ERA_DATE = on_application_date  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
ERA_ROUNDING = (truncate, half_up)  # every amount of the calculations that follow the era (eras.rounded)
ERA_AGE = (days_365, nearest_birthday)  # the age at the start date, by the system that wrote the offer
BIRTH_DATE = clamp_to_month_end  # a PS_BIRTH that does not exist (31 November, 30 February)

# t0 commission
# COBOL (money date < 2007-08-11): 29,469 rows, 99.9957 % of the search rows, 100.0000 % held out; 1 row left over (t5).
# Not distinguishable on train (COBOL): rounding half up = truncate = half even = half down = up; chosen truncate (the rule of the same era in the other calculations).
# Neuron NG (money date >= 2007-08-11): 196,389 rows, 99.9950 % of the search rows, 99.9972 % held out; 9 rows left over (t5).
# Not distinguishable on train (Neuron NG): rounding half up = up; chosen half up (the rule of the same era in the other calculations).
# The day of the era (T0_ERA_DATE): money date (225,848 exact rows); due date: 225,848 (19 rows in the other era); application date: 225,848 (69,084 rows in the other era); start date: 225,848 (68,141 rows in the other era).
# Not distinguishable on train: the day of the era money date = due date = application date = start date; chosen money date (the day of the calculation itself: so it is wherever the data decide, as in the charges).
T0_ERA_DATE = money_date  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T0_DATE = money_date  # the policy version (broker tier) and the commission rate are taken on this date
T0_ROUNDING = (truncate, half_up)

# t1 collection date
# 15,028 rows; no single rule fits (94.4513 %); the diagnosis splits on PH_PAYMT.
# PH_PAYMT LS: 12,508 rows, 100.0000 % of the search rows, 100.0000 % held out.
# PH_PAYMT UB: 2,520 rows, 100.0000 % of the search rows, 100.0000 % held out.
T1_COLLECTION_BY = 'PH_PAYMT'  # the column whose value selects the rule
T1_COLLECTION = {'LS': next_business_day_ticino, 'UB': same_day}  # the shift from the due date to the collection day

# t1 due dates
# 15,028 rows; every one of 60 combinations tried on 100 % of the policies (15,028 rows); confirmed on all rows: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train: past due all items due = paid items due; chosen all items due (the simplest).
# Not distinguishable on train: origin last due date = start date; chosen last due date (the simplest).
T1_PAST_DUE = all_items_due  # the history a schedule continues
T1_ANCHOR_DAY = highest_recent_day  # the day of month the schedule aims at
T1_ORIGIN = from_last_due_date  # where the schedule counts from
T1_STEP = clamped_step  # the next due date after a short month

# t3 trade date and pot of a premium
# 407,636 rows; every one of 24 combinations tried on 20 % of the policies (78,446 rows); confirmed on all rows: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
T3_TRADE_DATE = next_price_date  # the day a premium buys units
T3_POT_DATE = money_date  # the day that decides pot 1 or 2
T3_POT_BOUNDARY = before_the_end

# t3 amount of a premium per fund
# COBOL (trade date < 2007-08-11): 54,503 rows, coordinate search on 10 % of the policies (173 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (COBOL): allocation rows rows valid on the date = the whole set; chosen rows valid on the date (the simplest).
# Not distinguishable on train (COBOL): split gross x share x net, rounded once = share rounded, then net = net rounded, then share; chosen gross x share x net, rounded once (the simplest).
# Neuron NG (trade date >= 2007-08-11): 353,133 rows, coordinate search on 10 % of the policies (159 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (Neuron NG): allocation rows rows valid on the date = the whole set; chosen rows valid on the date (the simplest).
# Not distinguishable on train (Neuron NG): split gross x share x net, rounded once = share rounded, then net = net rounded, then share; chosen gross x share x net, rounded once (the simplest).
# The day of the era (T3_AMOUNT_ERA_DATE): trade date (40,763 exact rows); money date: 40,763 (0 rows in the other era); application date: 38,810 (12,635 rows in the other era).
T3_AMOUNT_ERA_DATE = on_the_day  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T3_ENTRY_DATE = money_date  # the entry rate (broker tier, ENT agreement) is taken on this day
T3_ALLOCATION_DATE = money_date  # the allocation set of this day is invested
T3_ALLOCATION_ROWS = valid_on_the_date
T3_SPLIT = share_then_net
T3_AMOUNT_ROUNDING = (truncate, half_up)

# t3 units of a premium
# COBOL (trade date < 2007-08-11): 54,503 rows, coordinate search on 10 % of the policies (23 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Neuron NG (trade date >= 2007-08-11): 353,133 rows, coordinate search on 10 % of the policies (12 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (Neuron NG): units rounding half up = half even; chosen half up (the rule of the same era in the other calculations).
# The day of the era (T3_UNITS_ERA_DATE): trade date (40,763 exact rows); money date: 40,763 (0 rows in the other era); application date: 34,457 (12,635 rows in the other era).
T3_UNITS_ERA_DATE = on_the_day  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T3_PREMIUM_PRICE = issue_price  # the unit price a premium buys at
T3_PREMIUM_FX_DATE = day_before_trade  # the day of the exchange rate of a premium
T3_RATE_LOOKUP = rate_on_or_before
T3_CROSS_RATE = exact_cross_rate
T3_UNITS_ROUNDING = (truncate, half_up)

# t3 units of a charge
# COBOL (charge date < 2007-08-11): 17,657 rows, coordinate search on 20 % of the policies (25 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Neuron NG (charge date >= 2007-08-11): 136,269 rows, coordinate search on 20 % of the policies (17 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (Neuron NG): units rounding half up = half even = half down; chosen half up (the rule of the same era in the other calculations).
# The day of the era (T3_CHARGE_UNITS_ERA_DATE): charge date (153,926 exact rows); application date: 115,170 (77,494 rows in the other era).
T3_CHARGE_UNITS_ERA_DATE = on_the_day  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T3_CHARGE_PRICE = redemption_price  # the unit price a charge cancels at
T3_CHARGE_FX_DATE = on_charge_date  # the day of the exchange rate of a charge
T3_CHARGE_UNITS_ROUNDING = (truncate, half_up)

# t4 entry charges
# 34,145 rows; every one of 2 combinations tried on 100 % of the policies (34,145 rows); confirmed on all rows: 0.0037 % of the search rows, 0.0145 % held out; 34143 rows left over (t5).
# Not distinguishable on train: entry amount gross share less the invested amount = its own rounded amount; chosen gross share less the invested amount (the simplest).
T3_ENTRY_AMOUNT = share_less_invested  # the entry charge of a fund on the statement (t4)

# t3 monthly charges
# COBOL (charge date < 2007-08-11): 5,646 rows, coordinate search on 34 % of the policies (229 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (COBOL): closed closed on the day = not checked; chosen closed on the day (business meaning: a surrendered or claimed policy is a closed contract, worth 0 by the task, so nothing is charged from it).
# Not distinguishable on train (COBOL): schedule monthly, before maturity = monthly, up to maturity; chosen monthly, before maturity (business meaning: on the maturity day the value is paid out and no new policy month begins, so no charge falls on it).
# Neuron NG (charge date >= 2007-08-11): 31,497 rows, coordinate search on 34 % of the policies (39 trials); confirmed: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (Neuron NG): closed closed on the day = not checked; chosen closed on the day (business meaning: a surrendered or claimed policy is a closed contract, worth 0 by the task, so nothing is charged from it).
# Not distinguishable on train (Neuron NG): piece rounding half up = half even = half down; chosen half up (the rule of the same era in the other calculations).
# Not distinguishable on train (Neuron NG): risk rounding half up = half even = half down; chosen half up (the rule of the same era in the other calculations).
# Not distinguishable on train (Neuron NG): value rounding half up = half even = half down; chosen half up (the rule of the same era in the other calculations).
# Not distinguishable on train (Neuron NG): schedule monthly, before maturity = monthly, up to maturity; chosen monthly, before maturity (business meaning: on the maturity day the value is paid out and no new policy month begins, so no charge falls on it).
# All train policies, a full replay (admin cap): charge totals matched by at most the value: 1,077,101; the full fee: 1,077,100.
# All train policies, a full replay (closed): charge totals matched by closed on the day: 1,077,101; not checked: 1,077,101 (still not distinguishable).
# All train policies, a full replay (risk base): charge totals matched by the values less the two charges: 1,077,101; the units valued again: 1,077,099.
# All train policies, a full replay (schedule): charge totals matched by monthly, before maturity: 1,077,101; monthly, up to maturity: 1,077,101 (still not distinguishable).
# All train policies, a full replay (split rest): charge totals matched by the largest slot, never negative: 1,077,101; the largest slot: 1,077,098.
# The day of the era (T3_CHARGES_ERA_DATE): charge date (37,143 exact rows); application date: 25,671 (14,838 rows in the other era).
T3_CHARGES_ERA_DATE = on_the_day  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T3_TARIFF_DAY = on_the_charge_date  # the NRCHRG row of this day
T3_CLOSED = closed_on_the_day
T3_ADMIN_CAP = at_most_the_value
T3_MANAGEMENT_BASE = before_the_charges
T3_RISK_BASE = less_the_charges  # the values the risk charge is taken on
T3_SPLIT_REST = largest_never_negative  # who takes the rounding rest of a split
T3_PIECE_ROUNDING = (truncate, half_up)
T3_AMC_RATE = agreement_for_both_pots
T3_DAY_COUNT = (actual_days_360, a_twelfth)
T3_AMC_ROUNDING = (truncate, half_up)
T3_CHARGE_AGE = at_the_last_anniversary
T3_RISK_ROUNDING = (truncate, half_up)
RISK_LOADING = multiplied
RISK_MONTHLY_RATE = twelfth_of_qx
T3_DAY_ORDER = charges_before_trades  # charges and trades of the same day
T3_SLOT_VALUE = rounded_value
T3_VALUE_ROUNDING = (truncate, half_up)
T3_SCHEDULE = before_maturity

# t3 policy value
# 6,153 rows; every one of 2 combinations tried on 100 % of the policies (6,153 rows); confirmed on all rows: 99.9796 % of the search rows, 100.0000 % held out; 1 row left over (t5).
T3_POLICY_VALUE = sum_of_the_slots  # how the slot values add up to the policy value

# t3 units on a valuation date
# 31,578 rows; every one of 2 combinations tried on 20 % of the policies (6,117 rows); confirmed on all rows: 100.0000 % of the search rows, 99.9514 % held out; 3 rows left over (t5).
T3_VALUATION_TIME = after_every_booking  # the valuation of a day comes after its bookings

# t3 surrender penalty
# COBOL (valuation date < 2007-08-11): 735 rows, 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train (COBOL): penalty years completed policy years = calendar years since start; chosen completed policy years (SCHEMA.md: SR_YEAR is the completed policy years).
# Neuron NG (valuation date >= 2007-08-11): 5,418 rows, 99.7232 % of the search rows, 99.6307 % held out; 16 rows left over (t5).
# Not distinguishable on train (Neuron NG): penalty years completed policy years = calendar years since start; chosen completed policy years (SCHEMA.md: SR_YEAR is the completed policy years).
# The day of the era (T3_SURRENDER_ERA_DATE): valuation date (6,137 exact rows); application date: 6,137 (1,658 rows in the other era).
# Not distinguishable on train: the day of the era valuation date = application date; chosen valuation date (the day of the calculation itself: so it is wherever the data decide, as in the charges).
T3_SURRENDER_ERA_DATE = on_the_day  # the day whose system (COBOL or Neuron NG) applies the pairs of this calculation
T3_PENALTY_YEARS = completed_policy_years  # the policy years of the NRSURR scale
T3_WAIVER = waiver_periods_apply  # the waiver periods of NRWAIV
T3_SURRENDER_ROUNDING = (truncate, half_up)

# t4 last statement year
# 3,019 rows; every one of 2 combinations tried on 100 % of the policies (3,019 rows); confirmed on all rows: 100.0000 % of the search rows, 100.0000 % held out; 0 rows left over (t5).
# Not distinguishable on train: end year the first closed version = its processing year; chosen the first closed version (the task counts the year the policy ends: the validity start of the closed version, not the day a clerk entered it (PH_CHGTS)).
T4_END_YEAR = first_closed_version  # the year a policy ends by surrender or death

# t2 offer projection
# 82,059 rows; a coordinate search from the simplest options on 10 % of the policies (8,234 rows, 125 trials); confirmed on all rows: 99.9923 % of the search rows, 99.9820 % held out; 8 rows left over (t5).
# Not distinguishable on train: term calendar months = completed months; chosen calendar months (the simplest).
# Not distinguishable on train: net premium rounding to the cent (era rule) = kept exact; chosen to the cent (era rule) (the simplest).
# Not distinguishable on train: floor never below zero = may go below zero; chosen never below zero (consistent with the fund accounting of t3, where no charge takes the value below zero: the admin fee is at most the value (charges.py) and no negative piece is booked (conventions_rest, step 2)).
T2_VERSION = first_version  # the policy version the offer belongs to
T2_PARAMETER_DATE = on_application_date  # NRCHRG, NRILLU and NRENTC are taken on it
T2_AGE_AT = on_start_date  # the entry age is the age on this day
T2_TERM = calendar_months
T2_NET_ROUNDING = to_the_cent
T2_GROWTH = twelfth_growth
T2_ORDER = ('premium', 'admin', 'management', 'risk', 'growth')  # the steps of one month
T2_ADMIN_MONTHS = every_month
T2_FLOOR = never_below_zero
T2_AMC_RATE = pot_2_rate
T2_AMC_PERIOD = twelfth_of_a_year
T2_CHARGE_ROUNDING = to_the_cent
T2_GROWTH_ROUNDING = to_the_cent
T2_ATTAINED_AGE = policy_year_age

# t7 taxes (no targets: each choice by evidence, the strongest first; vocabulary/evidence.py)
# payout amount (gross | after the surrender penalty): after the surrender penalty. Evidence: (t) exact rows on sample_1/sample_2: gross 37/54, after the surrender penalty 40/70; confirmed by both samples.
# death claim amount (the DTH booking | the death benefit | the death benefit, not rounded): the death benefit. Evidence: (t) exact rows on sample_1/sample_2: the DTH booking 38/70, the death benefit 40/70, the death benefit, not rounded 39/70; confirmed by sample_1 only.
# premium amount (received (PR_AMTRC) | due (PR_AMTDU)): received (PR_AMTRC). Evidence: (t) exact rows on sample_1/sample_2: received (PR_AMTRC) 40/70, due (PR_AMTDU) 40/65; confirmed by sample_2 only.
# paid back share (exact | to the cent): to the cent. Evidence: (a) exact breaks whole cents in t7_tax_payout (73 amounts).
# base of a loss (zero for a loss | the signed gain in Italy and Germany): zero for a loss. Evidence: (t) exact rows on sample_1/sample_2: zero for a loss 40/70, the signed gain in Italy and Germany 37/61; confirmed by both samples.
# stamp duty alone (dated | no date): no date. Evidence: (t) exact rows on sample_1/sample_2: dated 37/66, no date 40/70; confirmed by both samples.
# stamp duty first year (in full | from the start): in full. Evidence: (t) exact rows on sample_1/sample_2: in full 40/70, from the start 36/65; confirmed by both samples.
# presence (as booked in NRTAXB | by the rules found): as booked in NRTAXB. Evidence: (d') kept as the best confirmed build has it (no sample compared the options left).
# residence known (as known when processed | as known today): as known when processed. Evidence: (b) NRTAXB contradictions as known when processed 3, as known today 15.
# rate known (as known when processed | as known today): as known when processed. Evidence: (a) as known today breaks the example of t7_tax_annual.
# untaxed Swiss base (the payout in CHF | zero | the gain, not below zero): the payout in CHF. Evidence: (t) exact rows on sample_1/sample_2: the payout in CHF 40/70, zero 28/49, the gain, not below zero 28/49; confirmed by both samples.
# reported withholding (none | in the years without a row): in the years without a row. Evidence: (d) leaderboard, sample A: in the years without a row 75 %, none 75 %; (d') kept as the best confirmed build has it (no sample compared the options left).
# remittance (the 10th of the next month | the 16th of the next month | 30 days after the month end): DE the 10th of the next month, IT the 16th of the next month, CH 30 days after the month end, LU the 10th of the next month. Evidence: DE: (a) the 16th of the next month breaks the example of t7_tax_payout; 30 days after the month end breaks the example of t7_tax_payout; IT: (t) exact rows on sample_1/sample_2: the 10th of the next month 38/67, the 16th of the next month 40/70, 30 days after the month end 38/67; confirmed by both samples; CH: (t) exact rows on sample_1/sample_2: the 10th of the next month 38/66, the 16th of the next month 38/66, 30 days after the month end 40/70; confirmed by both samples; LU: (d') kept as the best confirmed build has it (no sample compared the options left).
# remittance shift (none | next weekday | next business day (Ticino) | next business day of the tax office): next business day of the tax office. Evidence: (t) exact rows on sample_1/sample_2: none 37/65, next weekday 39/69, next business day (Ticino) 40/69, next business day of the tax office 40/70; confirmed by sample_2 only.
# no remittance (None | an empty text): an empty text. Evidence: (d) leaderboard, sample A: an empty text 65 %, None 5 %.
# stamp duty share (days of the year | days / 365 | months | the full year): days of the year. Evidence: (t) exact rows on sample_1/sample_2: days of the year 40/70, days / 365 40/66, months 38/60, the full year 38/60; confirmed by sample_2 only.
# stamp duty value (policy value | surrender value): policy value. Evidence: (t) exact rows on sample_1/sample_2: policy value 40/70, surrender value 35/64; confirmed by both samples.
# stamp duty collected (the withdrawn share | everything): the withdrawn share. Evidence: (t) exact rows on sample_1/sample_2: the withdrawn share 40/70, everything 35/66; confirmed by both samples.
# church tax (lowered by the church tax | not lowered): lowered by the church tax. Evidence: (t) exact rows on sample_1/sample_2: lowered by the church tax 40/70, not lowered 40/67; confirmed by sample_2 only.
# exemption with half income (halved | the full exemption | none): none, as build 57. Evidence: a tie on the samples (no HEV payout in
# them); the leaderboard did not tell them apart (send-10 halved = send-9 none on sample C).
# exemption (the full exemption | none): none. Evidence: (t) exact rows on sample_1/sample_2: the full exemption 40/68, none 40/70; confirmed by sample_2 only.
# Italian substitute tax (the rate of the payout day | each rate on the gain of its period): each rate on the gain of its period. Evidence: (t) exact rows on sample_1/sample_2: the rate of the payout day 36/56, each rate on the gain of its period 40/70; confirmed by both samples.
# earlier withdrawals in the periods (all premiums, the whole period | open premiums, the share left): open premiums, the share left. Evidence: (t) exact rows on sample_1/sample_2: all premiums, the whole period 38/67, open premiums, the share left 40/70; confirmed by both samples.
# year in the yearly table (the payout year | the remittance year): the remittance year. Evidence: (t) exact rows on sample_1/sample_2: the payout year 39/65, the remittance year 40/70; confirmed by both samples.
# stamp duty at a payout (after the penalty | before the penalty): before the penalty. Evidence: (t) exact rows on sample_1/sample_2: after the penalty 40/69, before the penalty 40/70; confirmed by sample_2 only.
# German surcharges (by the system | cut to the cent): cut to the cent. Evidence: (t) exact rows on sample_1/sample_2: by the system 40/67, cut to the cent 40/70; confirmed by sample_2 only.
# premium rounding (on the payout day | on the premium day): on the premium day. Evidence: (t) exact rows on sample_1/sample_2: on the payout day 40/65, on the premium day 40/70; confirmed by sample_2 only.
# the 2019 correction (recalculated, duty by duty | recalculated, rounded once | the rate raise, rounded once): the rate raise, rounded once. Evidence: (a) recalculated, rounded once breaks the example of t7_tax_annual; (t) exact rows on sample_1/sample_2: recalculated, duty by duty 37/66, the rate raise, rounded once 40/70; confirmed by both samples.
T7_PAYOUT_AMOUNT = after_the_surrender_penalty  # what a withdrawal or a surrender paid
T7_DEATH_AMOUNT = the_death_benefit  # what a death claim paid
T7_PREMIUM_AMOUNT = received_amount  # the premiums a payout pays back
T7_BASIS_SHARE = share_to_the_cent  # the premiums a withdrawal pays back
T7_LOSS_BASE = zero_for_a_loss  # the base of a payout at a loss in Italy and Germany
T7_BOC_DATED = not_dated  # whether stamp duty collected alone gives a remittance date
T7_BOL_FIRST_YEAR = in_full  # the yearly stamp duty of the first policy year
T7_PRESENCE = as_booked  # whether a tax was booked
T7_RESIDENCE_KNOWN = when_processed  # the NRHOLD and NRADDR versions Neuron used
T7_RATE_KNOWN = when_processed  # the NRTAXR versions Neuron used
T7_CH_UNTAXED_BASE = the_payout  # the base of a Swiss payout without withholding tax
T7_REPORTED_VST = reported_in_new_years  # withholding tax of status M in the yearly table
T7_REMITTANCE = {'DE': tenth_of_next_month, 'IT': sixteenth_of_next_month, 'CH': thirty_days_after_month_end, 'LU': tenth_of_next_month}  # the day a withheld tax reaches the tax office, by country of residence
T7_REMITTANCE_SHIFT = office_business_day  # a remittance day the office is closed
T7_NO_REMITTANCE = empty_text  # the remittance date of a payout without tax
T7_BOL_SHARE = days_share  # the share of a payout year the Italian stamp duty is due for
T7_BOL_VALUE = the_policy_value  # the value the yearly Italian stamp duty is taken on
T7_BOC_SHARE = withdrawn_share  # the open stamp duty a withdrawal collects
T7_KST_CHURCH = lowered_by_church_tax  # the capital gains tax with church tax
T7_TFS_WITH_HEV = no_exemption  # TFS for an HEV payout (a tie on the samples and on the leaderboard)
T7_TFS = no_exemption  # the German partial exemption of 2018 (TFS) of a payout taxed in full
T7_SOS = by_rate_periods  # the rates of the Italian substitute tax on the gain
T7_SOS_EARLIER = open_premiums_and_share_left  # earlier withdrawals in the rate periods of the Italian gain
T7_ANNUAL_YEAR = in_the_remittance_year  # the year of a payout's tax in the yearly table
T7_BOL_PAYOUT_AMOUNT = before_the_penalty  # what the Italian stamp duty at a payout is taken on
T7_SURCHARGE_ROUNDING = cut_to_the_cent  # the rounding of German SOL and KIS
T7_PREMIUM_ROUNDING = on_the_premium_day  # the day whose system rounds a converted premium
T7_BOL_CORRECTION = the_rate_raise_rounded_once  # the 2019 correction of the Italian stamp duty (TAXFIX19)

# t7 taxes at a payout: the rules NRTAXB shows (decision tree of the engine, 20 % of the policies held out)
# VST: booked at 257 of 2,493 payouts; the tree agrees with NRTAXB on 2,493 (100.0000 %):
#   reporting status == 'M': never (2,107 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not reporting status == 'M' / above the Swiss threshold == True: always (257 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not reporting status == 'M' / not above the Swiss threshold == True: never (129 payouts, 100.0000 % of the search rows, 100.0000 % held out)
# SOS: booked at 153 of 2,493 payouts; the tree agrees with NRTAXB on 2,488 (99.7994 %):
#   country == 'IT' / gain above zero == False: never (235 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   country == 'IT' / not gain above zero == False: always (158 payouts, 97.5207 % of the search rows, 94.5946 % held out)
#   not country == 'IT': never (2,100 payouts, 100.0000 % of the search rows, 100.0000 % held out)
# KST: booked at 88 of 2,493 payouts; the tree agrees with NRTAXB on 2,484 (99.6390 %):
#   German regime == 'full' / gain above zero == False: never (157 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   German regime == 'full' / not gain above zero == False: always (91 payouts, 95.7143 % of the search rows, 85.7143 % held out)
#   not German regime == 'full': never (2,245 payouts, 99.8320 % of the search rows, 100.0000 % held out)
# SOL: booked at 88 of 2,493 payouts; the tree agrees with NRTAXB on 2,493 (100.0000 %):
#   KST booked == False: never (2,405 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not KST booked == False: always (88 payouts, 100.0000 % of the search rows, 100.0000 % held out)
# KIS: booked at 29 of 2,493 payouts; the tree agrees with NRTAXB on 2,488 (99.7994 %):
#   KST booked == False: never (2,405 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not KST booked == False / church member == False: never (54 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not KST booked == False / not church member == False: always (34 payouts, 82.7586 % of the search rows, 100.0000 % held out)
# BOC: booked at 295 of 2,493 payouts; the tree agrees with NRTAXB on 2,493 (100.0000 %):
#   Italian stamp duty accrued == False: never (2,198 payouts, 100.0000 % of the search rows, 100.0000 % held out)
#   not Italian stamp duty accrued == False: always (295 payouts, 100.0000 % of the search rows, 100.0000 % held out)
