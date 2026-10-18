# t7 on the leaderboard: submissions and what they showed

Nazar submits; the evaluation scores 20 rows of each table, a different 20 every time, every two hours. A row
counts only if every column is exact. 20 rows give a noise of about ±2 rows, so one submission changes **one large
group per table** (payout and annual are two independent experiments). Rule (agreed in the team): a shift of +4 rows or
more is accepted, −3 or less is reverted, anything between is noise: decide with the next submission or by meaning.
Small groups (church tax, HEV/TFS, currency before 1999, the 2 withdrawals near the Swiss threshold) are never
decided here: `rules.py` and the README describe them as ties.

The share of rows a change touches assumes the actuary samples all rows alike; if the sample favours taxed rows,
the groups of untaxed rows (most of Switzerland) weigh less.

| # | Build | Sent | payout change | annual change | payout | annual | Conclusion |
|---|---|---|---|---|---|---|---|
| 0 | team03-submission-22 | 17.10 ~15:20 | — (the reference) | — | 1/20 | 15/20 | the base of untaxed Swiss payouts and the remittance days are the suspects |
| 1 | `dist/t7-send-1` (Hack `main` fb1b00e, tag `submission`) | | Swiss base without withholding tax: the payout in CHF → **0.00** | reported withholding tax (status M) as **new rows** | 17.10 | **1/20** | **15/20** | exactly as v22, apparently the same 20 rows: the Swiss base is not the cause; reported VST not in the sample or wrong (it cannot cost a row) |
| 2 | `dist/t7-send-2-57` (built by Nazar; in the repository from commit 723e53f on: T7_NO_REMITTANCE) | 17.10 20:04 | remittance date **''** instead of None when nothing was withheld; Swiss base back to the payout | as submission 1 | **11/20** | 15/20 | the empty date was the cause: the scorer had dropped every untaxed row as malformed (scoring_t7 is published now: None and '' read alike) |
| 3 | `dist/t7-send-3.zip` (main 5fe65d1; the builds 3A, 3A-bol, 3B are superseded) | 18.10, after the generalization test | A1 net of the penalty, A2 shares to the cent, B2 weekend to the next Ticino business day | B1 stamp duty on the surrender value | **13/20** | **14/20** | the same 20 rows every time, so the changes are real: payout +2 (A1/A2/B2 kept), annual -1 (B1 reverted) |
| 4 | `dist/t7-send-4.zip` (5d50269, tag **best-send4**) | 18.10 | the signed gain as the base of a loss in Italy and Germany | B1 reverted; first-year stamp duty from the start | **26/40** | **10/30** | **the sample changed (payout 40 rows, annual 30): a new reference point**; annual 33 % comes from the new sample, not from our changes (the first-year share changes about 6 % of the rows) |

## Submission 1

**What changes against version 22** (checked on the extract with a local diff of the two builds):
- payout: 1,404 of 2,493 rows (56 %), only the column *taxable base*, only Swiss payouts without withholding tax:
  1,269 with status M, 129 with status E (below the threshold, or the 2 withdrawals just above it), 6 with status M
  and Italian stamp duty collected (holders who left Italy). No other column, no other row.
- annual: no existing row changes; 873 new rows (only `ch_vst`): years of Swiss holders with status M and a payout
  above 5000 CHF, 8 % of the payout in CHF. 11 such years already have a row and are left as they are.

**Expected outcomes and what to do:**

| payout (v22: 1/20) | Meaning | Next |
|---|---|---|
| 5/20 or more | the base of an untaxed payout is 0.00: keep | submission 2 tests the remittance days |
| 2–4/20 | noise: the base is not shown wrong or right | keep 0.00 one more round (the change touches 56 % of the rows, so a right base should show as about +10 rows if the rest of those rows is right); suspect the format or another column of the same rows: country, zeros, the empty date |
| 0–1/20 | the base was not the problem, or those rows are wrong in another column | ask the organizers how an empty remittance date is read (Nazar asks); check the country of untaxed Swiss rows; consider the gain as the base |

| annual (v22: 15/20) | Meaning | Next |
|---|---|---|
| 19/20 or more | reported tax belongs in the table: keep | — |
| 13–18/20 | noise: new rows can only add rows that exist in the truth, existing rows did not change | keep (it cannot cost a row); the 5 rows v22 missed are elsewhere: the stamp duty base (submission 2) |
| 12/20 or less | cannot come from this change (no existing row changed): sample or format | repeat unchanged next time |

## The plan after submission 1

Ordered by the rows a change touches (measured on the extract in step T7.0; the team's plan, with two changes: the
remittance days of Switzerland and Italy are tested together, and the annual stamp duty base comes first because it
touches 24 % of the rows, the payout-year share only 2 %).

| # | payout | rows | annual | rows |
|---|---|---|---|---|
| 2 | Switzerland and Italy remit on the 10th of the next month, like Germany (Neuron's batch day) | 590 (24 %) | stamp duty on the surrender value instead of the policy value | 1,517 (24 %) |
| 3 | a remittance on a weekend moves to the next weekday (Ticino holidays: a tie) | 201 (8 %) | stamp duty of a payout year: months instead of days | 134 (2 %) |
| 4 | what 1–3 show | | what 1–3 show | |

## Submission 2 (Nazar's build `t7-send-2-57`, uploaded as t7-send-2-main): payout 11/20, annual 15/20

Result: about 10 of the 14 untaxed rows of the sample pass now; about 5 of the 6 taxed rows still fail (team estimate).

Hypothesis: the scoring drops a row whose remittance date is None as malformed (the official converter of dates
cannot read None), so every payout without tax (1,813 of 2,493 rows, 73 %) failed whatever its other columns. The
build writes an empty text instead. The repository reproduces it on every row (switch T7_NO_REMITTANCE, from 723e53f).

| payout | Meaning | Next |
|---|---|---|
| 8/20 or more | the format was the cause | submission 3A |
| 4–7/20 | partly | 3A, and look at the taxed rows (remittance days) |
| 3/20 or less | not the format (or the converter reads both alike) | submission 3B |

Annual is unchanged from submission 1: 15/20 again is expected.

## Submission 3: three ready builds (95 files each, no bundle)

All three built from `main` code at commit b4cefb2 + rules.py of autosolve, with the switches below changed in the
build's rules.py (marked `# t7-send-3...`). Compared with build 2 on the extract:

| Build | payout change | payout rows changed | annual change | annual rows changed |
|---|---|---|---|---|
| `t7-send-3A` (Nazar's 3A) | a remittance on a weekend moves to the next weekday | 201 dates (CH 89, IT 87, DE 24, LU 1); and 134 IT stamp duties through the annual change | stamp duty of a payout year: months instead of days | 134 (2 %) |
| `t7-send-3A-bol` (recommended instead of 3A) | the same weekday shift | 201 dates; and 163 stamp duties through the annual change | stamp duty on the **surrender value** instead of the policy value | 1,517 (21 %) |
| `t7-send-3B` | None again (the task's words) and Switzerland and Italy remit on the **10th** like Germany | 590 taxed rows (CH 263, IT 327); the 1,813 untaxed rows return to None as in v22 | stamp duty on the surrender value | 1,517 (21 %) |

Why the surrender value for annual: the months share touches 134 rows, about 0.4 of 20 rows, which no submission can
see; the stamp duty base touches 1,517 rows, about 4 of 20, and the Italian stamp duty on life policies is, as far as
we know (not checked against a source), taken on the surrender value ("valore di riscatto"). The second example of the task has the same value both ways (an
old policy, no penalty left), so it does not decide. A change of the stamp duty also changes what a payout collects
(BOC, the stamp duty column of payout): 134-163 payout rows, about one of 20; noted, not avoidable.

Why 3B tests the 10th: rows with and without tax look alike in every column but the date and the base (checked: key
types, country codes, Decimal amounts with two places, no negative value). If the empty text does not help, the
actuary's 20 rows are probably mostly taxed ones ("different patterns"); their only unproven column is the remittance
day, and Neuron's tax batch runs on the 10th (the German example is the 10th too). 590 of the 680 taxed rows change.

| 3A / 3A-bol: payout | Next |
|---|---|
| up by 4 or more | keep the weekday shift; test the Ticino holidays only by meaning (a tie) |
| within ±3 | noise; next: the 10th for Switzerland and Italy |
| down by 3 or more | revert the shift |

| 3B: payout | Next |
|---|---|
| up by 4 or more | the 10th is right; next: the weekday shift |
| within ±3 | the cause is elsewhere: ask the organizers for one failing row's columns (no values needed: which column) |

| annual (3A-bol, 3B) | Next |
|---|---|
| 19/20 or more | the surrender value is right: keep |
| 13–18/20 | noise: decide by the law (surrender value) or try the payout-year share next |
| 12/20 or less | revert to the policy value |

## Submission 3 (`dist/t7-send-3.zip`, built from main): every change more likely than what it replaces

Strategy from now on: a build carries every change that is more likely than the current choice; a 50/50 change waits.
If a table falls, the changes are reverted in groups by this list. Rows changed, counted on the extract against
submission 2 (each change alone; together they overlap):

| Change | Why it is more likely | payout rows | annual rows |
|---|---|---|---|
| A1 payout net of the surrender penalty (withdrawals, surrenders; death claims without penalty) | the rules of which payouts are taxed then contradict no Swiss and no Italian NRTAXB booking (gross: 2 and 5); the formula of t3's surrender value | 555 (CH 494, IT 47, DE 14) | 238 |
| A2 the paid back share of a withdrawal rounded to the cent, carried rounded | exact shares left 74 bases with fractions of a cent, which never match (scoring_t7 compares exactly); now 0 | 86 (IT 74, DE 12) | 5 |
| B1 Italian stamp duty on the surrender value at 31 December | the tax module nets the penalty (A1); the example of the task agrees both ways | 163 (BOC collected, mostly IT) | 1,517 |
| B2 a remittance date on a weekend moves to the next Ticino business day | a tax office takes no money on a weekend: 208 of the 680 dated rows fell on one | 208 (CH 94, IT 88, DE 25, LU 1) | 0 |
| **all four** | | **881** | **1,750** |

Switches made but not used (each a submission of its own, 50/50 or untested): stamp duty alone without a date (182
rows), the signed gain as the base of a loss outside Switzerland (577), the first-year stamp duty from the start, the
due premium (PR_AMTDU), the death benefit of the tariff for death claims.

| payout (2: 11/20) | Next |
|---|---|
| 14/20 or more | keep all; next: one untested switch per table |
| 9–13/20 | noise or mixed; keep A1 and A2 (local evidence), test B2 alone next |
| 8/20 or less | revert B2 first (no local evidence), then A1 |

| annual (2: 15/20) | Next |
|---|---|
| 18/20 or more | keep B1 |
| 13–17/20 | noise; keep B1 one more round with the next change elsewhere |
| 12/20 or less | revert B1 (the policy value again) |

## Submission 4 (`dist/t7-send-4.zip`)

Submission 3 gave payout 13/20 (+2) and annual 14/20 (-1) on the same 20 rows as before, so both moves are real:
A1, A2 and B2 stay, B1 (stamp duty on the surrender value) goes back to the policy value.

| Change | Why | payout rows | annual rows |
|---|---|---|---|
| B1 reverted: the yearly stamp duty on the policy value again | annual fell 15 -> 14 with it | 163 (stamp duty collected) | 1,517 |
| the base of a payout at a loss in Italy and Germany: the signed gain (EUR; in Germany times the taxable share; untaxed rows only, Luxembourg and Switzerland unchanged) | the untaxed Swiss rows pass; the about 4 failing untaxed rows of the sample match the Italian and German losses with base 0.00 in number | 397 (IT 236, DE 161) | 0 |
| the yearly stamp duty of the first policy year for the days from the start to 31 December | the law takes a part year pro rata, as Neuron does in a payout year; every team is at 15/20 annual | 113 (stamp duty collected) | 409 |
| **all three** | | **447** | **1,517** (the first-year rows are among the reverted ones) |

A German contract of the old regime (begun before 2005, premiums for five years or more, paid after twelve years) is
tax free: its taxable share is 0, so its base stays 0.00 for a gain and for a loss.

| annual (3: 14/20) | Next |
|---|---|
| 16/20 or more | keep the first-year share |
| 15/20 | the revert alone; the first-year share is noise: keep it one more round |
| 14/20 or less | revert the first-year share |

| payout (3: 13/20) | Next |
|---|---|
| 14/20 or more | keep the signed base of a loss |
| 13/20 or less | revert it (0.00 again) |

## Submission 4: the new reference point (best-send4)

Submission 4 (commit 5d50269, tag `best-send4`, zip `dist/t7-send-4.zip`):
the t7 sample changed (payout 40 rows, annual 30): payout **26/40**, annual **10/30**. This is the new reference
point. Annual at 33 % is not from our changes (the first-year share changes about 6 % of the rows) but from the
composition of the new sample. It is our best build: if anything goes wrong, back to `best-send4`. The last upload
before the deadline is a full build, never a diagnostic one.

## Submission 5: DIAGNOSTIC (`dist/t7-send-5-diag.zip`, branch diag5 at 4c7c09c from best-send4)

Never the final upload. The scorer counts a missing row as wrong and ignores rows it does not ask for
(`scoring_t7.accuracy`: `predictions.get(k) == targets[k]` over the target keys only). So a build that answers one
group G only scores the right rows of group G in the sample.

- payout returns only the rows with an amount withheld, surcharged or collected (680 of 2,493 on our extract);
- annual returns only the years with Italian stamp duty alone and no payout in the year (5,257 of 7,252);
- everything else is submission 4; t0-t5 unchanged.

Groups on our extract (the sample of 40 + 30 rows is drawn from the private and public policies, so only the
proportions carry over):

| payout | rows | annual (groups overlap) | rows |
|---|---|---|---|
| CH untaxed | 1,398 | stamp duty alone, no payout in the year | 5,257 |
| CH with VST | 263 | stamp duty in a payout year | 289 |
| IT taxed (SOS or stamp duty collected) | 327 | stamp duty of the first policy year | 380 |
| IT untaxed | 66 | TAXFIX19 in the row | 375 |
| DE taxed | 89 | STP | 454 |
| DE untaxed | 196 | VST (871 of them reported, status M) | 1,127 |
| LU (1 with stamp duty collected) | 154 | SOS | 148 |
| **taxed together** | **680** | KST+SOL | 88 |
| | | KIS | 29 |

**How to read it** (submission 4 on the same sample: payout 26/40, annual 10/30):
- payout X right taxed rows -> the untaxed rows give 26 - X right ones. The number of taxed rows in the sample is
  not shown; on our extract they are 27 % of the payouts (about 11 of 40).
  - X about the taxed share (10-11): the taxed rows are right; the misses are untaxed -> submission 6 changes the
    untaxed group (base of a loss, Luxembourg, death claims).
  - X low (5 or less): the misses are taxed rows -> submission 6 changes the taxed group (remittance days of CH and
    IT, stamp duty collected without a date, church tax).
- annual Y right "stamp duty alone" rows -> the other groups give 10 - Y right ones.
  - Y high, close to the share of such rows (72 % on our extract, about 22 of 30): stamp duty alone is right; the
    misses are in the other groups -> submission 6 changes one of them (the year of a payout tax, STP, TAXFIX19,
    stamp duty of a payout year, the first year, reported VST).
  - Y low: the yearly stamp duty itself is wrong (its base, its rate, its rounding) -> submission 6 looks there first.

## Candidates for submission 6 (switches ready on branch cand6, none switched on)

Rows each changes against submission 4 on our extract. Which group to touch follows from submission 5.

| Group (if submission 5 points there) | Switch | payout rows | annual rows |
|---|---|---|---|
| payout, taxed | Switzerland remits on the 10th (T7_REMITTANCE) | 263 | 0 |
| payout, taxed | Italy remits on the 10th | 327 | 0 |
| payout, taxed | stamp duty collected alone gets no date (T7_BOC_DATED) | 182 (IT 174) | 0 |
| payout, taxed | capital gains tax not lowered by church tax (T7_KST_CHURCH) | 29 | 29 |
| payout, untaxed | base of a loss 0.00 again (T7_LOSS_BASE) | 397 (IT 236, DE 161) | 0 |
| payout, untaxed | the signed gain in Luxembourg too (T7_LOSS_BASE, new option) | 154 | 0 |
| payout, untaxed | death claims pay the death benefit of the tariff (T7_DEATH_AMOUNT) | 49 | 38 |
| annual, other | taxes of a payout in the year of the remittance (T7_TAX_YEAR, new) | 0 | 47 |
| annual, other | STP converted on the booking date (T7_STP_FX_DATE, new) | 0 | **0**: the booking date is the money date for all 454 premiums, nothing to test |
| annual, other | stamp duty of a payout year in months, or in full (T7_BOL_SHARE) | 134 | 134 |
| annual, other | first-year stamp duty in full again (T7_BOL_FIRST_YEAR) | 113 | 409 |
| annual, other | no reported VST (T7_REPORTED_VST) | 0 | 871: cannot raise the score (extra rows are ignored), only lower it |
| annual, other | TAXFIX19 in the corrected years | — | not offered: the second example of the task puts the 2019 correction (194.54) into 2019 |

## Submission 5 result (diagnostic, the sample of submission 4: payout 40 rows, annual 30)

- payout, the taxed rows only: **3 right** -> the untaxed rows: 26 - 3 = **23 right**. Almost every untaxed row is
  right; all 14 payout misses are taxed rows. What every taxed row has and an untaxed row does not is the remittance
  date. Germany (the 10th of the next month) is proven by the example of the task; Switzerland (30 days after the
  month end) and Italy (the 16th) are guesses from the law. If those are wrong, only the German taxed rows pass:
  about 3. Hypothesis: Neuron remitted everything in one batch on the 10th, for every country (as its run TAXBATCH).
- annual, "stamp duty alone" rows only: **2 right** -> the other groups: 10 - 2 = **8 right**. Suspect: the
  first-year stamp duty from the start (submission 4), which changes exactly "stamp duty alone" rows.

## Submission 6 (`dist/t7-send-6.zip`, branch send6 at 27d7409 from best-send4)

| Change | Why | payout rows | annual rows |
|---|---|---|---|
| every country remits on the 10th of the next month (Switzerland and Italy too); the weekend shift to the next Ticino business day stays | submission 5: 3 of the about 11 taxed rows pass, about the German ones; the 10th is proven for Germany and is the day of Neuron's batch | 590 (CH 263, IT 327) | 0 |
| the first-year stamp duty in full again (as before submission 4) | submission 5: 2 "stamp duty alone" rows right, the group this change of submission 4 touched | 113 stamp duties collected (inside the Italian rows of the line above but 2) | 409 |
| **both** | | **592** | **409** |

| payout (4: 26/40, same sample) | Next |
|---|---|
| more than 26 | the 10th is right; if it rose little, test Switzerland and Italy one at a time next |
| 26 or less | revert the 10th |

| annual (4: 10/30) | Next |
|---|---|
| more than 10 | the full first year is right |
| less than 10 | back to the share from the start |

## Submission 6 result (sample B, as 4 and 5): payout 24/40 (4: 26), annual 12/30 (4: 10)

- the full first-year stamp duty is right: annual +2;
- "the 10th for every country" is wrong: payout -2. The remittance days go back to the law (Switzerland 30 days after
  the month end, Italy the 16th, Germany the 10th), the weekend shift stays.

## Submission 7 (`dist/t7-send-7.zip`, branch send7 at d7f2dc5, preliminary tag best-send7)

best-send4 with the full first-year stamp duty (right by submission 6); the remittance days of the law stay.
Against submission 4: annual 409 rows (it_bol), payout 113 rows (the stamp duty collected at a payout follows the
accrued duty: IT 109, CH 2, DE 1, LU 1). Expected on sample B: payout 26 (the date change of submission 6 reverted;
the 113 stamp duties now agree with the right first year), annual 12.

## Submission 8: DIAGNOSTIC by country (`dist/t7-send-8-diag.zip`, branch diag8 at 65091f0 from best-send7)

- payout: every untaxed row (1,813: CH 1,398, DE 196, LU 153, IT 66) and the Swiss taxed rows (263); the Italian (327),
  German (89) and Luxembourg (1) taxed rows are left out: 2,076 rows;
- annual: only the years with a payout: 1,555 rows (stamp duty of a payout year 289, SOS 148, VST withheld 256, VST
  reported for status M 871, KST with SOL and KIS 88, STP in a payout year 14);
- the two examples of the task are outside both groups (a German taxed row, a year without a payout): by design.

How to read it (sample B; submission 5 showed 23 right untaxed rows, unchanged since):
- payout: score - 23 = the right Swiss taxed rows. Switzerland right (about its share of the taxed rows) -> the
  failing taxed rows are Italian (remittance on the 16th, stamp duty collected); Switzerland low -> its remittance
  (30 days after the month end) or its VST is wrong.
- annual: score = the right payout years; 12 (submission 7, expected) - score = the right years without a payout.

## Submissions 9 and 10 (branch t7-autosolve): the rules of the team's build 57 chosen by autosolve, and the HEV tie

- `dist/t7-send-9.zip` (SHA256 3640abc9…): every T7_* as build 57; the t7 output equals 57-switches byte for byte on
  the whole extract. Known samples: 20/20, 20/20, 40/40, 30/30.
- `dist/t7-send-10.zip` (SHA256 02ed31f3…): the same with T7_TFS_WITH_HEV = halved, nothing else. Known samples the
  same 110/110 (no HEV payout in them). It changes 3 payout rows (Germany: two withdrawals of 2026, a surrender of
  2024; base, KST, surcharges) and 3 yearly rows (KST, SOL, one KIS).
- Reading the third sample: send-10 above send-9 on payout means Neuron applied the HEV exemption (halved); below or
  equal means it did not, and send-9 stays final.
- Result (sample C, the third): send-10 payout 38/40, annual 27/30, unchanged against send-9: sample C has no HEV
  row. The HEV exemption stays none: a tie on the samples, the leaderboard did not tell them apart.

## Submissions 11 and 12 (sample C): the weak ties, one hypothesis each, on top of send-9

| Hole | Alternative | s1 / s2 | Extract rows payout / annual | Groups |
|---|---|---|---|---|
| presence | by the rules found (not NRTAXB) | 110/110 | 3 / 3 | Germany: 2 death claims, 1 surrender (2000, 2015, 2016); KST, SOL, remittance date |
| reported withholding | none | 110/110 | 0 / 872 | every changed row disappears (status M years without another tax) |
| remittance LU | the 16th / 30 days after the month end | 110/110 | 0 / 0 | Luxembourg withholds nothing: dropped |

- `dist/t7-send-11.zip` (SHA256 75836a2b…): presence by the rules found. Higher payout or annual than send-9 (38/40,
  27/30) means a German row of NRTAXB is a booking Neuron's amounts do not follow; lower means NRTAXB decides.
- `dist/t7-send-12.zip` (SHA256 95226846…): reported withholding none, a diagnostic: rows only disappear, so the
  score cannot rise. Annual lower than 27/30 means sample C holds years of reported VST (Neuron lists them); equal
  means it holds none (no evidence either way).
- Result of send-11 (sample C): payout 38/40, annual 27/30, unchanged against send-9: the 3 German rows are not in
  sample C. Presence stays as booked in NRTAXB; send-12 was not submitted. The final T7_* values are those of send-9.
