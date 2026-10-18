# Rule finder report

## ablation_t0_no_rates_no_premium_type

Ablation: t0 without the rate table and without the premium type column. The product code is a proxy (FLSP is the single-premium product), so the engine may recover the rates through it.

69555 rows, 21 combinations of rate (3), rounding (7).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rate: **fitted 0.03**; rounding: **half up** | 43.392 % | 46.184 % |
| ↳ misses concentrate where `broker tier == 'B'` | 0.240 % missed if true, 100.000 % if false | | |
| all rows / broker tier == 'B' | rate: **fitted 0.03**; rounding: **half up** | 99.787 % | 99.633 % |
| ↳ misses concentrate where `product == 'FLSP'` | 100.000 % missed if true, 0.010 % if false | | |
| all rows / broker tier == 'B' / product == 'FLSP' | rate: **fitted 0.01**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / broker tier == 'B' / not product == 'FLSP' | rate: **fitted 0.03**; rounding: **half up** | 99.988 % | 100.000 % |
| ↳ left over | 3 rows the rule does not explain (candidates for manual corrections, t5) | | |
| all rows / not broker tier == 'B' | rate: **fitted 0.04**; rounding: **half up** | 55.761 % | 47.387 % |
| ↳ misses concentrate where `broker tier == 'A'` | 0.300 % missed if true, 100.000 % if false | | |
| all rows / not broker tier == 'B' / broker tier == 'A' | rate: **fitted 0.04**; rounding: **half up** | 99.729 % | 99.509 % |
| ↳ misses concentrate where `product == 'FLSP'` | 100.000 % missed if true, 0.000 % if false | | |
| all rows / not broker tier == 'B' / broker tier == 'A' / product == 'FLSP' | rate: **fitted 0.015**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' / broker tier == 'A' / not product == 'FLSP' | rate: **fitted 0.04**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' / not broker tier == 'A' | rate: **fitted 0.02**; rounding: **half up** | 99.773 % | 99.745 % |
| ↳ misses concentrate where `product == 'FLSP'` | 100.000 % missed if true, 0.010 % if false | | |
| all rows / not broker tier == 'B' / not broker tier == 'A' / product == 'FLSP' | rate: **fitted 0.005**; rounding: **half up** | 100.000 % | 100.000 % |
| all rows / not broker tier == 'B' / not broker tier == 'A' / not product == 'FLSP' | rate: **fitted 0.02**; rounding: **half up** | 99.993 % | 100.000 % |
| ↳ left over | 1 row the rule does not explain (candidates for manual corrections, t5) | | |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rate: fitted 0.03; rounding: half up | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: truncate | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half even | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half down | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: up | 43.392 % | 46.184 % |

Left over: 4 policies (all of them are listed corrections). The rows contain 4 policies with a listed manual correction (NREXCP t0_commission); 4 of them are left over.

_17 s_

## ablation_t0_no_rates_no_tier

Ablation: t0 without the rate table NRCOMR and without the broker tier (NRBROK is not read). The tier is a property of the broker that no read column carries: the broker number determines it, but through 400 brokers that a tree of three tests cannot map. The engine should NOT reach 100 %: it must report what it cannot explain instead of inventing a rule.

69555 rows, 21 combinations of rate (3), rounding (7).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rate: **fitted 0.03**; rounding: **half up** | 43.392 % | 46.184 % |
| ↳ left over | 39062 rows the rule does not explain (prompt for an LLM written) | | |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rate: fitted 0.03; rounding: half up | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: truncate | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half even | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: half down | 43.392 % | 46.184 % |
| rate: fitted 0.03; rounding: up | 43.392 % | 46.184 % |

Left over: 598 policies (594 are not listed corrections). The rows contain 4 policies with a listed manual correction (NREXCP t0_commission); 4 of them are left over.

_15 s_

## ablation_t1_no_easter_holidays

Ablation: t1 with the Easter holidays removed from the dictionary. The engine should find the rest of the rule and leave over exactly the due dates near Easter, with a prompt that shows them, for a person or an LLM to add the missing brick.

15028 rows, 5 combinations of collection (5).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | collection: **next business day (Ticino, fixed only)** | 94.156 % | 93.989 % |
| ↳ misses concentrate where `payment method == 'LS'` | 0.450 % missed if true, 32.820 % if false | | |
| all rows / payment method == 'LS' | collection: **next business day (Ticino, fixed only)** | 99.606 % | 99.323 % |
| ↳ left over | 56 rows the rule does not explain (prompt for an LLM written) | | |
| all rows / not payment method == 'LS' | collection: **same day** | 100.000 % | 100.000 % |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| collection: next business day (Ticino, fixed only) | 94.156 % | 93.989 % |
| collection: next business day (Swiss federal) | 94.049 % | 93.954 % |
| collection: next weekday | 90.659 % | 90.510 % |
| collection: same day | 72.806 % | 73.673 % |
| collection: previous business day (Ticino) | 67.258 % | 68.225 % |

_1 s_
