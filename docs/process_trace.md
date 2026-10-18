# How the solution was built: process, trials and errors

A technical record of how, with AI assistance (`my_solution/README.md`, "Use of AI") and a person deciding at each
step, we turned a hand-written solution of the Lifeware challenge into a rule-search pipeline and then solved the
surprise task t7.
It is written to be learned from: what was tried, what failed, why, and what fixed it. The same episodes, one per
line, are in `process_trace.jsonl` (fields: phase, kind, goal, attempt, observation, diagnosis, fix, result, lesson,
commits). Times are of 2026-10-17; commits are in `git log`. No tax row, target value, token or server address is in
these files.

## 1. The method in one page

1. **Measure first.** `tools/quality_gate.py` runs the official `check.py`, radon maintainability, the tests, a purity
   check (standard library, no float, no policy numbers, no target files outside t5), the run time and the number of
   skipped policies, and compares them with a stored baseline. Every change ends with this gate; `main` only gets
   green changes.
2. **Classify before automating.** Every hidden choice of the solution (a *hole*: a rounding, a reference date, a
   calendar, an order of steps) was listed with its place, alternatives and evidence (`docs/holes.md`): 72 holes.
3. **A dictionary of conventions.** Each hole has a family of named candidate functions (*bricks*) in
   `my_solution/conventions*.py`. The solution calls the chosen brick through `rules.py`.
4. **Exact-match search.** `vocabulary/engine.py` scores every combination by exact rows (never by average error),
   holds out 20 % of the policies, and diagnoses the misses with a one-level decision tree (`payment method == 'LS'`,
   `application date < 2007-08-11`). Statistical cuts on dates are snapped to *landmarks* (a day on which all events of
   one kind happened). Many holes: coordinate descent with pair moves when stuck; ties on a sample are replayed on all
   policies.
5. **Ties by a written principle.** When the data cannot decide: the option consistent with the same era elsewhere,
   else a stated business reason, else the simplest; marked "not distinguishable on train" in `rules.py` and README.
6. **One button.** `autosolve.py` runs all cases and writes `rules.py` deterministically (same input, same bytes);
   `--verify` compares, `--demo` shows the first cases in 40 s.
7. **A language model for what the dictionary lacks.** Only when a part stays unexplained; the proposed code runs in a
   sandbox and is kept only if no row gets worse (ablations: a removed rule found again in one step).
8. **Honesty rules.** Count before claiming; separate "checked on data", "tie", "guess"; never put target values in
   tracked files (`tools/target_leaks.py` in the gate); report negative results.

## 2. Timeline

| Step | What | Result |
|---|---|---|
| 0–1 | git, gate, inventory of 72 holes | baseline measured |
| 1 | skip a failing policy, not the task | robustness test, 0 skipped |
| 2 | the 3 t4 cent errors | two general rules, t4 34,121 → 34,124 |
| 3 | one dictionary, `autosolve.py`, t0 | `rules.py` generated |
| 4 | era, ages, birth dates, calendar | 13 of 72 holes |
| 5 | t1 schedule | 17 of 72, t1 100 % |
| 6 | t2 offer (coordinate search) | 32 of 72 |
| 7 | t3 premiums into units | 45 of 72 |
| 8 | t3 monthly charges (18 holes) | 60 of 72 |
| 9 | value, penalty, t4 last year, `--demo` | 64 of 72 |
| 10 | language model, sandbox, ablations | Easter ablation 94 % → 100 % in one step |
| 11 | the date of the era as a hole of every rule | 65 of 72 |
| 12 | figures (t6), README, cleanup | submission |
| t7.0 | the team's build v22 measured on our extract | which switch moves how many rows |
| t7.1 | v22 ported, 13 switches | output = v22 on every row |
| t7.2 | rules of which payouts carry which tax, from NRTAXB | 99.6–100 % agreement |
| t7 submissions | 1: base 0 (1/20 unchanged); 2: empty date (1/20 → 11/20); 3: penalty, cents, stamp-duty base, weekend shift | see `logs/t7_leaderboard.md` |
| t7 constraints | ≤ 100 files, speed | 95–98 files (MI 89.2 by decision), t7 3× faster |
| generalization | cut-off from each extract, autosolve on test clients | see `docs/generalization.md` |

## 3. Trials and errors, by kind

### Wrong hypotheses rejected by data
- t4 cent errors were not "rounding in the month of the conversion" nor "leap years": the risk charge base and a
  negative split rest were (step 2).
- "Half up before 2007" for t0 was not supported: no train commission before 2007 can tell roundings apart (step 3).
- t7: a zero base for untaxed Swiss payouts did not move the leaderboard (submission 1): the base was not the cause.

### Search failures and their fixes
- Coordinate descent stuck at an infeasible start → pair moves when below 99 % (step 6).
- Ties on a 3 % sample were decided only by family order → full replay of every train policy (step 8).
- Searches depended on each other → `ASSUMES`, checked at the end (step 8).
- A tree split at a random date (Easter 2027) hid the real rule from the model → splits only on plausible dates
  before asking the model (step 10).
- The era finder crashed on a client whose other conventions differed: another column split first, then the fixed
  growth and management rate fitted 0 % of the offers → date-only diagnosis, and the fixed parts become holes when
  they fit less than half (generalization).
- A feature leaked the target ("KST booked" explaining KST) → a tax never sees itself (t7.2).

### Engineering errors
- A chained shell command hid a failed `git add` → check a clean worktree before merging.
- An uncommitted change was lost by `git checkout --` while reverting an experiment → commit before experiments.
- A textual rename turned the local variable `dates.append` into a module name and t3 fell to 0 % → rename only
  where the module is imported.
- Merging a hub module created a circular import → keep hubs, reject merges that create import cycles.
- The end of a 13-minute pipeline crashed on a case without a `check.py` task → test the tail on a tiny case first.
- A figure compared `Decimal('2220')` with the text `'2220.00'` → compare numbers as numbers.

### Metric pressure (maintainability)
- radon MI falls with the logarithm of a module's lines and Halstead volume and rises with the share of comments
  (optimum about 57 %). Big modules or one-line docstrings dropped MI below the floor several times (92.6, 89.4,
  88.66). Small topic modules with multi-line evidence docstrings restored it.
- The upload limit of 100 files forced merging: the naive merge gave 84.2, a greedy plan within themes 89.3; the
  owner decided to accept 89.2 as the new floor.

### Leaderboard as an oracle (t7)
- 20 rows per evaluation, the same rows each time, a noise of ±2 rows: only changes of large groups are visible.
  Each submission changes one group per table; every change is logged with the rows it touches and what to do on
  each outcome.
- The biggest jump came from the format, not the rule: rows with `None` were dropped by the scorer as malformed.

### Security and privacy
- An automated review found escapes from the model sandbox (frames, `str.format`, module objects) → hardened, with
  tests; documented as a guard, not a security boundary.
- Target values were found in reports and saved prompts → removed or redacted, and a leak scan joined the gate.
- Tax rows are never printed by the closed model; only aggregate counts.

## 4. Lessons that carry over

1. Build the gate before changing code; keep the baseline in a file.
2. Exact matches, not average error: one corrected row costs one row and never moves a parameter.
3. Snap statistical change points to business events of the data.
4. A sample tie is not a data tie; escalate to all rows.
5. Write the tie principle down and mark every tie.
6. When no option fits, extend the dictionary (by hand or by a sandboxed model), and keep a new brick only if no row
   gets worse.
7. With hidden amounts, use internal consistency as the target (which payouts carry a booking).
8. Check how the scorer parses every column before hunting for rule errors.
9. Count before you write a number; commit before you experiment.
10. Read per-extract facts (the conversion day) at run time, so the rules carry to a new client.
