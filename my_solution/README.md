# Neuron migration — rules of the legacy system as code

`submission.py` calculates every task from the Neuron export in `legacy_dir`: commissions (t0), next due dates
(t1), the offer projection (t2), surrender values (t3), annual statements (t4) and the manual corrections (t5).
Python standard library only, money in `Decimal`, no network, no model at run time.

## Results on the train targets

Official `starter_kit/check.py`, one run of all tasks (Python 3.14.4):

| Task | Exact rows | What is left |
|---|---|---|
| t0 commission | 225,848 / 225,858 = 99.996 % | 10 manual corrections |
| t1 next due dates | 15,028 / 15,028 = 100 % | — |
| t2 projected maturity value | 3,011 / 3,019 = 99.735 % | 8 manual corrections |
| t3 surrender value | 6,137 / 6,153 = 99.740 % | 16 manual corrections |
| t4 annual statement | 34,124 / 34,145 = 99.939 % | 21 manual corrections |
| t5 outliers | 55 flagged values | exactly the corrections above |

Maintainability index (radon, as `scoring.maintainability`): 89.2, with 95 files (the leaderboard accepts at most
100; the 137 small modules of before had 93.2). All tasks t0-t5 together run in about 40 s, t7 in about 13 s.

## Run it

```
cd starter_kit
python3 check.py --submission ../my_solution --legacy ../legacy --targets ../targets
```

From the project root, `.venv/bin/python tools/quality_gate.py` runs the same check plus maintainability, run
time, the self-tests and a purity check (standard library only, no float, no policy numbers, targets only in t5).

**One button.** `python3 autosolve.py` searches the rules in the data and writes `rules.py`: every choice in it
names a function of `conventions.py`, with the evidence as comments (rows, exact share on held-out policies,
rows left over, ties). Deleting `rules.py` and running it again gives the same bytes. So far it finds the era
(the cut-off and how each system rounds and counts ages), the reading of impossible birth dates, the rules of
t0, all of t1 (the schedule, its anchor day and the collection date) and all of t2 (14 conventions of the
offer, among them the order of the steps of a month out of 48, found by a coordinate search on every policy year)
and how a premium buys units in t3 (13 conventions: trade date, pot, fund amounts, prices, exchange rates, the units of
premiums and charges, the entry charge of t4) and the monthly charges of t3 (18 conventions, every charge day of a
sample checked on its own; a tie on the sample is replayed on all train policies: 1,077,101 of 1,077,102 charge
totals, the other one a manual correction), the policy value, the units on a valuation date, the surrender penalty
and the last statement year. For every calculation that changed with the conversion it also finds the day that
decides the era (application, money, trade, charge or valuation date): 65 of the 72 conventions of `docs/holes.md`;
the other 7 are data cleaning or have no row in the export that tells their options apart.

## How the rules were found

The business description of each task gave a first formula. Every detail it leaves open is a *convention*
(a rounding, a reference date, a calendar, an order of steps). Each convention was decided by the data:

- **Exhaustive search over a dictionary of conventions** (`vocabulary/`, outside this package): every
  combination of candidate conventions is scored by *exact* matches on the train targets, never by an
  average error. 20 % of the policies are held out to confirm the winner.
- **A decision tree on the misses** names the condition where a rule changes, e.g. `payment method == 'LS'`
  or `application date < 2007-08-11`, and each part is searched again.
- **The diagnostic files** check single steps: values per policy year (t2), every unit booking
  (`t3_booking.csv`), holdings per fund and pot, the policy value before the penalty.
- **What no rule explains is a manual correction**: one corrected row costs one row and never moves a
  parameter, because only exact matches count.

The calculation itself (fund accounting, the monthly offer loop, the schedule) is a small library for
unit-linked policies; every convention inside it is listed in `docs/holes.md` (72 of them, with the place
in the code, the alternatives and the evidence); `autosolve.py` chooses 65 of them and writes `rules.py`.

## The rules

**System change.** Neuron NG replaced the COBOL system on **2007-08-11**, the date of all 946 events 800
"system conversion"; the batch user of the events switches from `CBLBATCH` to `NGBATCH` on that day. The solution reads that day from each extract it is given (`eras.conversion_day`: the day of its events 800, else the cut-off autosolve found), so a client converted on another day is split right without a new search.
The COBOL system truncated to the cent and counted the entry age as days / 365; Neuron NG rounds half up
and takes the age at the nearest birthday. Which day decides the system is itself a rule of each calculation,
found in the data (`rules.py`, `*_ERA_DATE`): the application date for the offer and the entry age, the charge date
for the charges, the day of the trade or valuation where the data cannot tell (figure a).

| Task | Rule |
|---|---|
| t0 | Received, not reversed premiums (state P). `PR_AMTRC` × NRCOMR rate of the broker tier and the premium type; the broker is the one of the policy version valid on the **money date**. Half up to the cent. |
| t1 | Policies paying premiums on the extract date. The schedule continues from the last past due date by the frequency; the day of month is the highest day among the last 12 due dates (a COBOL schedule may have drifted from the 31st to the 28th). Direct debit (LS): the next business day of **Ticino** (11 fixed holidays plus Easter Monday, Ascension, Whit Monday, Corpus Christi); bank transfer (UB): the due date itself. |
| t2 | The offer of the first policy version with the parameters valid on the **application date**. Each month: premium, admin fee, management charge (pot 2 rate / 12), risk charge, growth (1 + rate / 12), every step rounded to the cent by the system of the application date. Risk charge: sum at risk of the benefit option × qx (mortality table, sex basis, smoker factor, loading) / 12 at entry age + completed policy years. |
| t3 | Premiums buy units at the **issue price of the first price date after the money date**, with the FX rate of the day before; the entry charge (broker tier or agreement on the money date) is taken first, pot 1 for the first `PD_INIMON` months. On every monthly anniversary: admin fee (at most the value) and management charge (pot rates or agreement; COBOL: actual days / 360, NG: 1/12) on the values before charges, then the risk charge on those values less the two charges (the remaining units are not valued again); each split over funds and pots pro rata, the largest takes the rounding rest but never a negative piece; units cancelled at the redemption price and FX of the day. Customer orders are taken from NRBOOK. Surrender value: units at the redemption price, minus the NRSURR penalty of the completed policy years, none in a waiver period. |
| t4 | Premiums by money date, entry charges by trade date, the other charges by charge date; from the start year to the year of surrender or death, at the latest 2025. |
| t5 | A target value is a manual correction if it differs from the rules by at least one currency unit (any column of a t4 row) or by any day. |

## Rules decided by very few rows

Some rules are right on every train row, but only a handful of rows tell them from the next option. On unseen
policies such a rule rests on that little evidence:

| Rule | Next option | Rows that decide |
|---|---|---|
| t0: the broker of the money date | the broker of the due date | 2 commissions (the broker tier differs between the two dates for 4 premiums) |
| t0: rounding half up from 2007-08-11 | half even; truncation | 1 commission; 2 commissions (rounding up matches the same rows) |
| t3: the admin fee at most the policy value | the full fee | 1 of 1,077,102 charge totals (a full replay of all train policies) |
| t3: the risk charge on the values less the two charges | the remaining units valued again | 2 of 1,077,102 charge totals |
| t2/t3: the era of an offer and of the entry age is that of the application date | the start date | 8 offers (the only ones applied before 2007-08-11 and started after it) |
| t3: no negative rounding rest | the largest slot takes any rest | 3 of 1,077,102 charge totals |

The last three were ties on the 3 % sample the search runs on and were decided by replaying every train policy.

## What the data cannot decide

Some choices are **not distinguishable on train**: several options match exactly the same train rows. The
search then follows a stated principle: the option consistent with the rule of the same era in the other
calculations, or a preference the search case states with its reason, else the simplest option. `rules.py`
marks each such choice; on unseen policies the options may differ. Currently:

| Choice | Options that tie | Chosen, because |
|---|---|---|
| Rounding of the commission before 2007-08-11 | half up, truncate, half even, half down, up | truncate: the COBOL rule of the other calculations |
| Rounding of the commission from 2007-08-11 | half up, up | half up: the Neuron NG rule of the other calculations |
| An impossible birth date (31 November) | clamp to the month end, roll into the next month | clamp: month ends are clamped in every schedule |
| t1: the past items a schedule continues | all items due, the paid ones only | all items: the simplest |
| t1: where a schedule counts from | the last due date, the start date | the last due date: the simplest |
| t2: the term | calendar months, completed months (no train policy matures on an earlier day of the month) | calendar months: the simplest |
| t2: the net premium | rounded to the cent, kept exact | rounded: the rule of every other step |
| t2: a charge larger than the value | stops at zero, goes below zero (no train offer gets there) | stops at zero: as in t3, where no charge takes the value below zero |
| t3: rounding a premium's fund amount | once, after the share, or after the net (all 407,636 bookings agree) | once: the simplest |
| t3: rows of an allocation set | those valid on the date, the whole set | valid on the date: the simplest |
| t3: units from 2007-08-11 | half up, half even (half down for charges) | half up: the Neuron NG rule of the other calculations |
| t3: rounding of the charges from 2007-08-11 | half up, half even, half down | half up: the Neuron NG rule of the other calculations |
| t3: a closed policy | not charged from the day of its closing, or not checked (it holds no units) | not charged: a closed contract is worth 0 by the task |
| t3: the last charge day | before maturity, or the maturity day too (no train charge falls on it) | before maturity: on that day the value is paid out and no policy month begins |
| t3: the policy years of the penalty | completed policy years, calendar years since the start (the train valuations at the end of December or in the COVID waiver cannot tell) | completed: SCHEMA defines SR_YEAR so |
| The day that decides the era of the commission rounding | money, due, application or start date (the COBOL rounding itself cannot be told apart) | the money date: the day of the calculation itself |
| The day that decides the era of a premium's amount and units | trade date, money date (in the same era for every train booking) | the trade date: the day of the calculation itself |
| The day that decides the era of the surrender rounding | valuation date, application date (1,658 valuations change era, none changes its value) | the valuation date: the day of the calculation itself |
| t4: the year a policy ends | the first closed version, the year it was processed | the closed version: the task counts the year the policy ends |

Four more conventions are not searched yet and have no row in the export that tells the options apart: the order of overlapping rows in tables without a version number (no such overlap exists),
start, maturity and currency from the first policy version (they never change), the date of the commission
rate (NRCOMR never changes) and the mortality of ages above 110 (the oldest insured person reaches 101).
**The truncation of the commission before 2007-08-11 is a choice without evidence (a tie).** No train commission before the conversion has a third decimal of 5 or more, so half up, truncation, half even, half down and up all match the same rows. Truncation is chosen because every other calculation of the COBOL years truncates (offers, units, charges, surrender values: there the data decide it); on another extract with such a commission it may be wrong.
The broker date of t0 (money date rather than due date) rests on 4 of 306,456 premiums: only for those
does the broker tier differ between the two dates.

## On new clients

On test clients of the same insurer with other hidden rules (the team's stand), one run of `autosolve.py` on the
client's own data brings the build from 92.7 / 92.3 / 0.0 / 23.1 / 0.8 % (t0-t4, our rules) to 100 / 99.8 / 100 /
90.4 / 99.5 % on an L3 client, and to 100 / 100 / 100 / 99.9 / 100 % on an L2 client; 29 of the 30 planted rules
are found, the calendar of canton Zurich is not in the dictionary. Details: `docs/generalization.md`.

## t7: the same engine without answers

t7 (the tax audit) has no local targets. The engine that finds the conventions of t0-t4 chooses those of t7 too
(`autosolve.py --only t7`, about 7 minutes), with evidence in place of targets, the strongest first
(`vocabulary/evidence.py`, case `vocabulary/cases/t7_tax.py`):

1. **the two rows of the task** to the cent, and every amount in whole cents (the official `scoring_t7` compares
   exactly: an exact share of the premiums paid back left 172 amounts with fractions of a cent);
2. **NRTAXB**, Neuron's record of the taxes it booked without their amounts: the rules of which payouts carry a tax
   contradict it 3 times net of the surrender penalty, 13 times on the gross amount; the residence Neuron knew when it
   processed a payout puts every Italian stamp duty in Italy (the residence known today: 12 not);
3. the yearly table must hold the taxes of the payouts of the year;
4. **the leaderboard log** `logs/t7_evidence.json`: every upload with its choices and its score; a higher score wins
   only on the same sample; an option no sample compared stays as the best confirmed build has it;
5. a tie: the meaning, else the first option.

Every T7 line of `rules.py` carries the level that decided it. The uploads so far (`logs/t7_leaderboard.md`):

| Upload | What changed | payout | annual |
|---|---|---|---|
| v22 | the team's first build | 1/20 | 15/20 |
| 1 | base 0 for untaxed Swiss payouts; reported withholding tax | 1/20 | 15/20 |
| 2 | **an empty remittance date instead of None**: the scorer had dropped every untaxed row as malformed | 11/20 | 15/20 |
| 3 | **tax on the payout net of the surrender penalty**; shares to the cent; weekend to the next business day | 13/20 | 14/20 |
| 4 | stamp duty back on the policy value; the signed gain as the base of a loss | 26/40 | 10/30 (new sample) |
| 5 | diagnostic: only the taxed rows (3 right) and only "stamp duty alone" (2 right) | — | — |
| 6 | every country remits on the 10th; the first-year stamp duty in full | 24/40 | 12/30 |
| 7 | the remittance days of the law again, the first year in full (chosen by the engine from 1-6) | | |

Findings on the way: the tax tables are **bitemporal** (a move or a rate entered later counts from then: the versions
known when Neuron processed the payout); the 2017-2019 Italian stamp duty was raised afterwards and corrected by the run
**TAXFIX19** in one amount in 2019 (the second example of the task); a diagnostic upload that answers one group only
tells which group fails (a missing row counts as wrong, an extra one is ignored).

## Use of AI

- **Claude Code (Anthropic), a closed model**, wrote and ran the code of this repository with a person deciding each
  step: the engine, the solution, the tests, the documents. For t7 it read the code and ran programs that print
  aggregate counts and our own calculated answers; it did not print rows of the tax tables (NRTAXB, NRTAXR, NRADDR,
  NRHOLD) nor evaluation logs. Claude in a chat outside this repository did read some rows of these tables at the
  start of t7 (the team's context document notes it); from then on only aggregates went to a closed model.
- **Qwen 27B (open weights) on our own server** is the language model inside the rule search (`--llm`): it proposes a
  new brick where the dictionary lacks one; its code runs in a sandbox and is kept only if no row gets worse
  (ablations: a removed Easter calendar and a removed age rule found again).
- **The submission calls no model**: everything is computed from `legacy_dir` with the standard library.

## Who found the rules

| Part | Written by | What it holds |
|---|---|---|
| `rules.py` | **the search** (`autosolve.py`, one button, 13 min) | 74 choices: 65 of the 72 conventions of `docs/holes.md`, each with its evidence |
| `conventions*.py` | people, from the hand-written solution and its alternatives | the dictionary: named candidate conventions the search chooses from |
| the other modules | people | a small library of unit-linked accounting: reading the export, the schedule, the offer loop, the fund ledger |
| bricks of a language model | Qwen 27B, kept by the engine | none in the final rules; in the ablations it found two removed rules again (figure g) |

How much work a new target is, per target and per step: [`docs/generalization.md`](../docs/generalization.md).

## Figures (t6)

[`figures/`](../figures/README.md): the system change on 2007-08-11, the entry age at the nearest birthday,
the collection calendar of Ticino, an annual statement as a waterfall, one policy over its life, the differences
to the targets (never a cent: the misses are manual corrections) and the language model in the loop. They are
made by `tools/figures.py`.

## Robustness

The private policies are unseen. If one policy breaks a rule (no policy version on a date, no main risk, an
impossible date), `guard.per_policy` leaves out that policy instead of the whole task and names it on stderr.
On the train and public policies nothing is skipped; the quality gate fails if a train policy ever is.

## Layout

| Modules | Task |
|---|---|
| `submission.py` | entry points |
| `commission*` | t0 |
| `schedule*`, `dates*` | t1, calendar of Ticino, Easter |
| `projection*` | t2 |
| `ledger*`, `charges*`, `orders`, `market*`, `accounts*` | t3 and t4 fund accounting |
| `tariff*`, `eras` | parameters, risk charge, the COBOL / Neuron NG rules |
| `rules.py` | the choices of the search (written by `autosolve.py`, do not edit by hand) |
| `conventions*` | the dictionary of candidate conventions the choices name |
| `outliers*` | t5 |
| `tables*`, `guard` | reading the export, skipping a failing policy |

## Known limits

Every train row the rules miss is flagged by t5 as a manual correction (55 rows); no row is off by a rule
we know of. Some choices rest on few rows or cannot be decided on train (the two tables above); on unseen
policies they may differ. The search chooses among conventions people wrote down: a convention outside the
dictionary is found only if the language model proposes it (`vocabulary/README.md`). Seven conventions are not
searched (data cleaning, or no data that tells the options apart).
