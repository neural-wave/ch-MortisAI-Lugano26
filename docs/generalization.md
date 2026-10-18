# Generalization: how much work is a new target?

The challenge asks: "if the client asks tomorrow for the formula of another quantity, how much work is it?"
This page answers with what the project measured, not with what it hopes.

## The one button

`python3 autosolve.py` (13 minutes on a laptop, standard library only) reads the export and the train
targets, searches every convention below and writes `my_solution/rules.py`. Deleting `rules.py` and pressing
the button again gives the same bytes; the official `check.py` then gives the numbers of the README.
`python3 autosolve.py --demo` shows the first four targets in about 40 seconds.

The search does not know the answers. It knows a *dictionary*: families of named candidate conventions
(`my_solution/conventions_*.py`: roundings, reference dates, calendars, age rules, orders of steps...). For each
target, a *case* (`vocabulary/cases/*.py`) states which holes the calculation has and which family fills each.
The engine scores every combination by exact matches only, splits the rows where the rule changes (a decision
tree on the misses), and settles ties by a stated principle. A language model is asked only when a part stays
unexplained, and its code is kept only if it raises the exact rows of held-out policies.

## Per target

Rules: constants written to `rules.py`. Era pairs: rules with one option for the COBOL years and one for
Neuron NG. Day of the era: which date decides between the two systems, also searched (step 11). LLM: bricks
from the language model in the final rules (it found bricks in the ablations below, none is needed for the
real data). Search time: the run from scratch (`rules.py` deleted), 2026-10-17. Ties: choices the data cannot
decide, settled by the principle and marked in `rules.py` (a case may count several holes of one choice).

| Case (target) | Rules | Era pairs | Day of the era | Ties settled by the principle | LLM | Search time |
|---|---|---|---|---|---|---|
| The era of Neuron (t2 offers, years 1 and 2) | 5 | 2 | application date (8 rows decide) | 2 | 0 | 28 s |
| t0 commission | 3 | 1 | money date (a tie: no row decides) | 3 | 0 | 8 s |
| t1 collection date (a split by payment method) | 2 | | | | 0 | 0 s |
| t1 due dates | 4 | | | 2 | 0 | 4 s |
| t3 trade date and pot of a premium | 3 | | | | 0 | 16 s |
| t3 amount of a premium per fund | 6 | 1 | trade date (= money date on every row) | 4 | 0 | 93 s |
| t3 units of a premium | 6 | 1 | trade date (= money date on every row) | 1 | 0 | 18 s |
| t3 units of a charge | 4 | 1 | charge date (77,494 rows decide) | 1 | 0 | 60 s |
| t4 entry charges | 1 | | | 1 | 0 | 1 s |
| t3 monthly charges | 19 | 5 | charge date (14,838 rows decide) | 7 | 0 | 322 s |
| t3 policy value | 1 | | | | 0 | 0 s |
| t3 units on a valuation date | 1 | | | | 0 | 27 s |
| t3 surrender penalty | 4 | 1 | valuation date (a tie: 1,658 rows change era, no value changes) | 3 | 0 | 13 s |
| t4 last statement year | 1 | | | 1 | 0 | 0 s |
| t2 offer projection | 14 | | | 3 | 0 | 77 s |
| **All** | **74** | **12** | **7** | **28** | **0** | **13 min (797 s)** |

The 74 constants cover 65 of the 72 conventions listed in `docs/holes.md`. The other 7 are not searched:
two are data cleaning (lower-case currency codes, smoker code `J`), four have no row in the export that tells
their options apart (overlapping rows without a version number, start and currency from the first version, the
date of the commission rate, the mortality above age 110), and one is a parameter of our t5 method, not of Neuron.

**Added by hand.** Every brick of the dictionary was written by people, most of them taken from the teammate's
hand-written solution and its alternatives. Writing a brick is the remaining hand work; choosing among them is not.
Two families were added while automating, because the search showed a gap: the anchor day of t1 (the highest day
of the last 12 due dates) and the never-negative rest of a charge split.

## A new target: the recipe and its cost

1. A case file of 30 to 80 lines: read the rows that have a target, write the formula with holes, name the
   family of each hole. The t3 cases call the solution's own functions with trial rules, so the search and the
   answer run the same code.
2. Run `python3 autosolve.py` (or `vocabulary/run.py --cases <case>` for one case). Exact rows, the split where the
   rule changes, ties and left-over rows come out as a report.
3. If a part stays unexplained, add `--llm`: the model sees the missed rows, the rows the rule gets right close
   to them and the calls of each hole, and proposes a brick; it is kept only if no row gets worse.
4. The solution reads the new constants from `rules.py`.

A formula target with no simulation needs no Python at all: a JSON spec (`vocabulary/specs/*.json`).

## What the language model did (ablations)

A brick was removed from the dictionary and the engine was asked to find the rule anyway (step 10, Qwen 27B
on our own server, `vocabulary/results_llm_step10/`):

| Ablation | Without the brick | With the model | Kept brick |
|---|---|---|---|
| t1 collection without the Easter holidays | 94.2 % (99.6 % of the direct debits) | **100 %** in one step | next business day with the Easter holidays of Ticino |
| The era without the COBOL age rule | 98.0 % of the COBOL offers, a false split | **100 %** | days since birth / 365, rounded |
| t1 schedule without the anchor day | 99.95 %, called "explained" | not asked | none: a gap this small looks like noise to the engine |

The kept bricks are stored with their origin (`vocabulary/learned.json`) and compiled through the sandbox on
every later run, so a rerun without the model gives the same rules.

## New clients: the rules come back with one button

The team's test stand (`stand/run.py`) builds clients of the same insurer with other hidden rules and scores a
build on their **test** policies, whose targets nobody had. The honest protocol: autosolve sees only a copy of the
client's `client/legacy` and `client/targets` (`stand_runs/<client>/input/`, outside git); our `rules.py` is not
touched; the card of hidden rules is opened only after the results below were written down (and hashed).

    cd stand_runs/<client>/hack && ../../../.venv/bin/python autosolve.py --legacy ../input/legacy \
        --targets ../input/targets --out ../autosolve_out
    python3 stand/run.py <builds> --clients <clients folder> --tasks t0 t1 t2 t3 t4

| Client | Build | t0 | t1 | t2 | t3 | t4 |
|---|---|---|---|---|---|---|
| c002 (L2: our conventions, new parameters, conversion 2010-07-03) | rules of our extract (#41) | 96.3 | 100.0 | 90.8 | 65.7 | 58.7 |
| | + the conversion day read from the extract | 94.1 | 100.0 | 100.0 | 99.9 | 100.0 |
| | **after autosolve on the client** | **100.0** | **100.0** | **100.0** | **99.9** | **100.0** |
| c003 (L3: L2 and other conventions) | rules of our extract (#41) | 92.7 | 92.3 | 0.0 | 23.1 | 0.8 |
| | + the conversion day read from the extract | 97.2 | 92.3 | 0.0 | 23.0 | 0.8 |
| | **after autosolve on the client** | **100.0** | **99.8** | **100.0** | **90.4** | **99.5** |

The conversion day alone lifts c002 to almost 100 % in t2-t4, but costs t0 2 points: with a later conversion the
commissions of 2007-2010 fall into the COBOL era, where our rules truncate, a choice the data of our extract could not
make (a tie, see the README). autosolve on the client decides it from the client's own rows.

**Rules found** (the card, opened afterwards, against the client's `rules.py`):
- c002: 15 of 15: roundings (truncate / half up), ages (days/365 / nearest birthday), management period (actual/360 /
  a twelfth), the Ticino calendar, collection (LS next business day, UB same day), commission (half up, money date),
  FX of the day before the trade, buy price ask, growth rate/12, pot 2, conversion 2010-07-03.
- c003: 14 of 15: roundings (half even / half up), ages (nearest birthday / days/365), actual/360 in both eras,
  FX of the trade day, buy price bid, compounded growth, pot 1, collection (LS and UB next business day), commission,
  conversion 2002-04-06. **Missed: the calendar of canton Zurich**: not in the dictionary; the engine took the
  nearest brick (Ticino with Good Friday, a Zurich holiday) and t1 stays at 99.8 %. A Zurich calendar brick, or the
  language model on the unexplained part, is the way to close it.
- c003 t3 and t4 keep one-cent differences (365 surrender values, 138 management charges): the family of the rule is
  right (actual/360), the client computes it slightly otherwise in the Neuron NG era; open.

**Engine changes the stand asked for** (the story of this section; all before any card was opened):
1. the conversion day is read from each extract (the day of its events 800), so the rules of our extract split a new
   client at its own conversion;
2. the era finder looks at the date columns alone when another column splits the misses first;
3. the era case searches the growth and the management rate (pot 1, pot 2, pot 1 then 2) too when its fixed options
   fit less than half of the offers (c003: 0 %);
4. t1 collection: one rule for LS and UB when no split is found (the client collects both the same way);
5. t7's NRTAXB case is skipped on an extract without the tax module.
On our extract the search and `rules.py` are unchanged (`autosolve --verify`).

The blind client c021 (L7) is not in our copy of the stand yet; its card stays closed until its final run.

## Rules decided by very few rows

On unseen policies these rules rest on little evidence (also in the README):

| Rule | Next option | Rows that decide |
|---|---|---|
| t0: the broker of the money date | the broker of the due date | 2 commissions |
| t0: rounding half up from 2007-08-11 | half even; truncation | 1 commission; 2 commissions |
| The era of an offer on the application date | the start date | 8 offers |
| t3: the admin fee at most the policy value | the full fee | 1 of 1,077,102 charge totals |
| t3: the risk charge on the values less the two charges | the remaining units valued again | 2 of 1,077,102 |
| t3: no negative rounding rest | the largest slot takes any rest | 3 of 1,077,102 |

## How long the automation took

Wall-clock times of the steps of the plan, on 2026-10-17:

| Step | What | Time |
|---|---|---|
| 0–1 | git, quality gate, inventory of the 72 conventions | about 40 min |
| 1 | README, protection against a failing policy | 66 min, of them about 50 min paused (usage limit) |
| 2 | the 3 wrong t4 rows: two general rules | 14 min |
| 3 | the one button on t0 | 8 min |
| 4 | the era, the calendar, the ages, the birth dates | 12 min |
| 5 | t1 | 4 min |
| 6 | t2 | 18 min |
| 7 | t3: premiums into units | 23 min |
| 8 | t3: the monthly charges | 74 min, of them about 10 min paused and 25 min waiting for runs |
| 9 | t3 value and penalty, t4, t5 | 54 min, of them about 45 min waiting for three full runs |
| 10 | the language model, the sandbox, the ablations | 49 min, of them about 25 min waiting for the model |
| 11 | the day of the era as a hole, the run from scratch, this page | 12:30–13:11, about half of it waiting for two full runs |

The times count the work with AI assistance (`my_solution/README.md`, "Use of AI"), a person deciding at each step;
the families of conventions and the hand-written solution they come from existed before.
