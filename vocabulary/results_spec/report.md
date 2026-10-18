# Rule finder report

## t0_commission_spec

t0 commission declared as a spec: on which date is the broker taken, and how is the commission rounded?

225858 rows, 14 combinations of broker taken on (2), rounding (7).

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

_15 s_

## t0_without_rate_table

t0 commission WITHOUT the rate table NRCOMR: the rate is an unknown constant fitted from the data. The tree has to find on its own that the rate depends on broker tier and premium type, and the fit recovers each rate of the table (30 % of the policies).

69555 rows, 21 combinations of rate (3), rounding (7).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rate: **fitted 0.03**; rounding: **half up** | 43.392 % | 46.184 % |
| ↳ misses concentrate where `broker tier == 'B'` | 0.240 % missed if true, 100.000 % if false | | |
| all rows / broker tier == 'B' | rate: **fitted 0.03**; rounding: **half up** | 99.787 % | 99.633 % |
| ↳ misses concentrate where `premium type == 'L'` | 0.010 % missed if true, 100.000 % if false | | |
| all rows / broker tier == 'B' / premium type == 'L' | rate: **fitted 0.03**; rounding: **half up** | 99.988 % | 100.000 % |
| ↳ left over | 3 rows the rule does not explain (candidates for manual corrections, t5) | | |
| all rows / broker tier == 'B' / not premium type == 'L' | rate: **fitted 0.01**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' | rate: **fitted 0.04**; rounding: **half up** | 55.761 % | 47.387 % |
| ↳ misses concentrate where `broker tier == 'A'` | 0.300 % missed if true, 100.000 % if false | | |
| all rows / not broker tier == 'B' / broker tier == 'A' | rate: **fitted 0.04**; rounding: **half up** | 99.729 % | 99.509 % |
| ↳ misses concentrate where `premium type == 'L'` | 0.000 % missed if true, 100.000 % if false | | |
| all rows / not broker tier == 'B' / broker tier == 'A' / premium type == 'L' | rate: **fitted 0.04**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' / broker tier == 'A' / not premium type == 'L' | rate: **fitted 0.015**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' / not broker tier == 'A' | rate: **fitted 0.02**; rounding: **half up** | 99.773 % | 99.745 % |
| ↳ misses concentrate where `premium type == 'L'` | 0.010 % missed if true, 100.000 % if false | | |
| all rows / not broker tier == 'B' / not broker tier == 'A' / premium type == 'L' | rate: **fitted 0.02**; rounding: **half up** | 99.993 % | 100.000 % |
| ↳ left over | 1 row the rule does not explain (candidates for manual corrections, t5) | | |
| all rows / not broker tier == 'B' / not broker tier == 'A' / not premium type == 'L' | rate: **fitted 0.005**; rounding: **half up** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rate: fitted 0.03; rounding: half up | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: truncate | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half even | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half down | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: up | 43.392 % | 46.184 % |

Left over: 4 policies (all of them are listed corrections). The rows contain 4 policies with a listed manual correction (NREXCP t0_commission); 4 of them are left over.

_19 s_

## t1_collection_spec

t1 collection date declared as a spec: how is a due date moved to the day the money is collected?

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

_1 s_
