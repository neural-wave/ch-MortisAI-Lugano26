# Rule finder report

## t0_commission

t0 commission: on which date is the broker (and his tier) taken, and how is the amount rounded?

Holes: the date that selects the policy version (application, start, due or money date)
and the rounding brick. Formula: rounding(received amount x rate(tier on that date, premium type)).

225858 rows, 28 combinations of broker taken on (4), rounding (7).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | broker taken on: **money date**; rounding: **half up** | 99.995 % | 99.998 % |
| ↳ left over | 10 rows the rule does not explain (candidates for manual corrections, t5) | | |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| broker taken on: money date; rounding: half up | 99.995 % | 99.998 % |
| broker taken on: money date; rounding: up | 99.995 % | 99.998 % |
| broker taken on: money date; rounding: truncate before 2007-08-11, then half up | 99.995 % | 99.998 % |
| broker taken on: money date; rounding: half even | 99.995 % | 99.998 % |
| broker taken on: due date; rounding: half up | 99.994 % | 99.998 % |

Left over: 10 policies (4 are not listed corrections). The rows contain 6 policies with a listed manual correction (NREXCP t0_commission); 6 of them are left over.

_7 s_

## t1_collection

t1 collection date: how is a due date moved to the day the money is collected?

Hole: the business-day shift. The search finds that no single shift explains all rows,
the diagnosis finds the payment method behind it, and each part gets its own rule.

15028 rows, 6 combinations of collection (6).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | collection: **next business day (Ticino, with Easter)** | 94.451 % | 94.552 % |
| ↳ misses concentrate where `payment method == 'LS'` | 0.000 % missed if true, 32.980 % if false | | |
| all rows / payment method == 'LS' | collection: **next business day (Ticino, with Easter)** | 100.000 % | 100.000 % |
| all rows / not payment method == 'LS' | collection: **same day** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| collection: next business day (Ticino, with Easter) | 94.451 % | 94.552 % |
| collection: next business day (Ticino, fixed only) | 94.156 % | 93.989 % |
| collection: next business day (Swiss federal) | 94.049 % | 93.954 % |
| collection: next weekday | 90.659 % | 90.510 % |
| collection: same day | 72.806 % | 73.673 % |

_0 s_

## t2_offer

t2 offer projection: rounding, entry age, growth and management rate of the first two policy years.

Holes: rounding, entry age, growth per month, management rate (pot 1 or pot 2).
Target: the projected value at the end of policy years 1 and 2 (diagnostic file).

3019 rows, 48 combinations of rounding (3), entry age (4), growth (2), management rate (2).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rounding: **truncate before 2007-08-11, then half up**; entry age: **days / 365 before 2007-08-11, then nearest**; growth: **yearly rate / 12**; management rate: **pot 2 rate** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rounding: truncate before 2007-08-11, then half up; entry age: days / 365 before 2007-08-11, then nearest; growth: yearly rate / 12; management rate: pot 2 rate | 100.000 % | 100.000 % |
| rounding: truncate before 2007-08-11, then half up; entry age: nearest birthday; growth: yearly rate / 12; management rate: pot 2 rate | 99.378 % | 99.176 % |
| rounding: truncate before 2007-08-11, then half up; entry age: days / 365; growth: yearly rate / 12; management rate: pot 2 rate | 98.300 % | 97.694 % |
| rounding: half up; entry age: nearest birthday; growth: yearly rate / 12; management rate: pot 2 rate | 73.051 % | 70.675 % |
| rounding: half up; entry age: days / 365 before 2007-08-11, then nearest; growth: yearly rate / 12; management rate: pot 2 rate | 73.051 % | 70.675 % |

_8 s_

## t2_offer_plain

t2 offer projection without any era brick in the dictionary.

The same holes as t2_offer, but only plain roundings and ages. No single combination fits,
so the diagnosis has to find on its own that the rule changes with the application date,
and the search per segment recovers the COBOL rule before and the Neuron NG rule after.

3019 rows, 36 combinations of rounding (3), entry age (3), growth (2), management rate (2).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rounding: **half up**; entry age: **nearest birthday**; growth: **yearly rate / 12**; management rate: **pot 2 rate** | 73.051 % | 70.675 % |
| ↳ misses concentrate where `application date < 2007-08-11` | 99.880 % missed if true, 0.000 % if false | | |
| all rows / application date < 2007-08-11 | rounding: **truncate**; entry age: **days / 365**; growth: **yearly rate / 12**; management rate: **pot 2 rate** | 100.000 % | 100.000 % |
| all rows / not application date < 2007-08-11 | rounding: **half up**; entry age: **nearest birthday**; growth: **yearly rate / 12**; management rate: **pot 2 rate** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rounding: half up; entry age: nearest birthday; growth: yearly rate / 12; management rate: pot 2 rate | 73.051 % | 70.675 % |
| rounding: half up; entry age: days / 365; growth: yearly rate / 12; management rate: pot 2 rate | 71.352 % | 68.369 % |
| rounding: half even; entry age: nearest birthday; growth: yearly rate / 12; management rate: pot 2 rate | 71.103 % | 67.545 % |
| rounding: half even; entry age: days / 365; growth: yearly rate / 12; management rate: pot 2 rate | 69.486 % | 65.404 % |
| rounding: half up; entry age: last birthday; growth: yearly rate / 12; management rate: pot 2 rate | 43.242 % | 45.964 % |

Change point: exact matches per application year with plain half-up rounding:

1993: 0.000 % 1994: 0.000 % 1995: 0.000 % 1996: 0.000 % 1997: 0.000 % 1998: 0.000 % 1999: 0.000 % 2000: 0.000 % 2001: 0.000 % 2002: 0.000 % 2003: 0.000 % 2004: 0.000 % 2005: 0.000 % 2006: 1.270 % 2007: 34.450 % 2008: 100.000 % 2009: 100.000 % 2010: 100.000 % 2011: 100.000 % 2012: 100.000 % 2013: 100.000 % 2014: 100.000 % 2015: 100.000 % 2016: 100.000 % 2017: 100.000 % 2018: 100.000 % 2019: 100.000 % 2020: 100.000 % 2021: 100.000 % 2022: 100.000 % 2023: 100.000 % 2024: 100.000 % 2025: 100.000 %

_17 s_

## t3_units

t3 units of a booking: which price, which price and exchange-rate dates, how units are rounded.

Bookings of premiums (PRM) buy units, admin fee, management and risk charges (ADM, AMC, RSK)
cancel units. Target: the units of the diagnostic file t3_booking.csv, from its amount.
Holes: issue or redemption price, the date of the price, the date of the exchange rate,
the rounding of the units. A sample of 1 % of the policies keeps the run short
(RF_SHARE=5 python3 vocabulary/run.py ... for 5 %).

52061 rows, 54 combinations of price (2), price date (3), exchange rate date (3), units (3).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | price: **redemption price (bid)**; price date: **booking price date**; exchange rate date: **trade date**; units: **6 decimals, truncate before 2007-08-11, then half up** | 94.014 % | 89.041 % |
| ↳ misses concentrate where `booking type == 'PRM'` | 84.280 % missed if true, 0.000 % if false | | |
| all rows / booking type == 'PRM' | price: **issue price (ask)**; price date: **booking price date**; exchange rate date: **day before trade date**; units: **6 decimals, truncate before 2007-08-11, then half up** | 100.000 % | 100.000 % |
| all rows / not booking type == 'PRM' | price: **redemption price (bid)**; price date: **booking price date**; exchange rate date: **trade date**; units: **6 decimals, truncate before 2007-08-11, then half up** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| price: redemption price (bid); price date: booking price date; exchange rate date: trade date; units: 6 decimals, truncate before 2007-08-11, then half up | 94.014 % | 89.041 % |
| price: redemption price (bid); price date: trade date; exchange rate date: trade date; units: 6 decimals, truncate before 2007-08-11, then half up | 94.014 % | 89.041 % |
| price: redemption price (bid); price date: booking price date; exchange rate date: trade date; units: 6 decimals, half up | 89.064 % | 84.257 % |
| price: redemption price (bid); price date: trade date; exchange rate date: trade date; units: 6 decimals, half up | 89.064 % | 84.257 % |
| price: redemption price (bid); price date: booking price date; exchange rate date: day before trade date; units: 6 decimals, truncate before 2007-08-11, then half up | 78.237 % | 79.612 % |

_27 s_

## t3_penalty

t3 surrender penalty: how the policy years are counted, whether waivers apply, how it is rounded.

Target: surrender value; input: the policy value before the penalty (diagnostic column).
Penalty rate: NRSURR by the product's surrender scale and the policy years, 0 without a row.

6153 rows, 24 combinations of policy years (4), waiver (2), rounding (3).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | policy years: **completed policy years**; waiver: **waiver periods apply (NRWAIV)**; rounding: **truncate before 2007-08-11, then half up** | 99.756 % | 99.678 % |
| ↳ left over | 16 rows the rule does not explain (prompt for an LLM written) | | |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| policy years: completed policy years; waiver: waiver periods apply (NRWAIV); rounding: truncate before 2007-08-11, then half up | 99.756 % | 99.678 % |
| policy years: calendar years since start; waiver: waiver periods apply (NRWAIV); rounding: truncate before 2007-08-11, then half up | 99.756 % | 99.678 % |
| policy years: days / 365, truncated; waiver: waiver periods apply (NRWAIV); rounding: truncate before 2007-08-11, then half up | 99.287 % | 99.436 % |
| policy years: completed policy years; waiver: waiver periods apply (NRWAIV); rounding: half up | 97.821 % | 97.665 % |
| policy years: calendar years since start; waiver: waiver periods apply (NRWAIV); rounding: half up | 97.821 % | 97.665 % |

Left over: 16 policies (5 are not listed corrections). The rows contain 11 policies with a listed manual correction (NREXCP t3_surrender_value); 11 of them are left over.

_0 s_

## t4_premiums

t4 premiums of a statement year: which items count and by which date they fall into a year.

Target: the premiums column of the annual statement. Holes: the item set (received and not
reversed, all paid items, or all items at their amount due) and the date that decides the year
(money date, due date, or the effective date of the booking event).

34145 rows, 9 combinations of items (3), year by (3).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | items: **received, not reversed**; year by: **money date** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| items: received, not reversed; year by: money date | 100.000 % | 100.000 % |
| items: state P (paid); year by: money date | 100.000 % | 100.000 % |
| items: received, not reversed; year by: booking event date | 100.000 % | 100.000 % |
| items: state P (paid); year by: booking event date | 100.000 % | 100.000 % |
| items: received, not reversed; year by: due date | 95.151 % | 95.000 % |

_4 s_
