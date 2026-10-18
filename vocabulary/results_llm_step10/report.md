# Rule finder report

## ablation_t1_anchor

Ablation: the t1 schedule without the anchor day Neuron uses (the highest day of the last 12 due dates).

The dictionary keeps the day of the start, of the last due date, the highest day ever and the most common recent
day. Schedules that drifted from the 31st to the 28th in the COBOL years, and month ends, are then missed; the
engine should say so and, with a model connected, take a proposed anchor day only if it raises the exact rows.

15028 rows, 48 combinations of past due (2), anchor day (4), origin (2), step (3).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | past due: **paid items due**; anchor day: **most common day of the last 12 due dates**; origin: **last due date**; step: **clamped to the month end** | 99.951 % | 100.000 % |
| ↳ left over | 6 rows the rule does not explain (candidates for manual corrections, t5) | | |

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| past due: paid items due; anchor day: most common day of the last 12 due dates; origin: last due date; step: clamped to the month end | 99.951 % | 100.000 % |
| past due: paid items due; anchor day: most common day of the last 12 due dates; origin: start date; step: clamped to the month end | 99.951 % | 100.000 % |
| past due: all items due; anchor day: most common day of the last 12 due dates; origin: last due date; step: clamped to the month end | 99.926 % | 100.000 % |
| past due: all items due; anchor day: most common day of the last 12 due dates; origin: start date; step: clamped to the month end | 99.926 % | 100.000 % |
| past due: paid items due; anchor day: day of the last due date; origin: last due date; step: clamped to the month end | 99.811 % | 99.438 % |

_5 s_

## ablation_era_age

Ablation: the era case without the age rule of the COBOL system (days since birth / 365, rounded).

The diagnosis still finds the application date of 2007-08-11 (a landmark: the day of all events 800); the
offers before it then miss with every remaining age rule. With a model connected, a proposed age brick is
kept only if it raises the exact rows of the held-out policies.

3019 rows, 48 combinations of rounding (6), entry age (4), birth date (2).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | rounding: **half up**; entry age: **nearest birthday**; birth date: **clamp to the month end** | 73.051 % | 70.675 % |
| ↳ misses concentrate where `application date < 2007-08-11` | 99.880 % missed if true, 0.000 % if false | | |
| all rows / application date < 2007-08-11 | rounding: **truncate**; entry age: **proposed: days since birth / 365, rounded to nearest whole year (COBOL era) (answer 1)**; birth date: **clamp to the month end** | 100.000 % | 100.000 % |
| all rows / not application date < 2007-08-11 | rounding: **half up**; entry age: **nearest birthday**; birth date: **clamp to the month end** | 100.000 % | 100.000 % |

Brick proposed by the model and kept (all rows / application date < 2007-08-11 / proposals for entry age; kept: exact rows (search, held out) (2399, 603) -> (2412, 607)): **proposed: days since birth / 365, rounded to nearest whole year (COBOL era) (answer 1)**

```python
def brick(birth_date, entry_date):
    # name: days since birth / 365, rounded to nearest whole year (COBOL era)
    days = (entry_date - birth_date).days
    return int((D(days) / D(365)).quantize(D('1'), rounding=ROUND_HALF_UP))
```

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| rounding: half up; entry age: nearest birthday; birth date: clamp to the month end | 73.051 % | 70.675 % |
| rounding: half up; entry age: nearest birthday; birth date: roll into the next month | 73.051 % | 70.675 % |
| rounding: half up; entry age: days / 365.25; birth date: clamp to the month end | 72.678 % | 70.675 % |
| rounding: half up; entry age: days / 365.25; birth date: roll into the next month | 72.678 % | 70.675 % |
| rounding: half even; entry age: nearest birthday; birth date: clamp to the month end | 71.103 % | 67.545 % |

_537 s_

## ablation_t1_no_easter_holidays

Ablation: t1 with the Easter holidays removed from the dictionary. The engine should find the rest of the rule and leave over exactly the due dates near Easter, with a prompt that shows them, for a person or an LLM to add the missing brick.

15028 rows, 5 combinations of collection (5).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | collection: **proposed: brick 1 (answer 1) (extends: next business day (Ticino, fixed only))** | 94.451 % | 94.552 % |
| ↳ misses concentrate where `payment method == 'LS'` | 0.000 % missed if true, 32.980 % if false | | |
| all rows / payment method == 'LS' | collection: **proposed: brick 1 (answer 1) (extends: next business day (Ticino, fixed only))** | 100.000 % | 100.000 % |
| all rows / not payment method == 'LS' | collection: **same day** | 100.000 % | 100.000 % |

Brick proposed by the model and kept (all rows / payment method == 'LS' / proposals for collection; kept: exact rows (search, held out) (12143, 2829) -> (12183, 2845)): **proposed: brick 1 (answer 1) (extends: next business day (Ticino, fixed only))**

```python
def brick(d):
    # next business day (Ticino, fixed + Easter-derived movable holidays)
    def _easter_sunday(year):
        a = year % 19
        b = year // 100
        c = year % 100
        dd = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - dd - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return dt.date(year, month, day)

    def _movable(year):
        es = _easter_sunday(year)
        return {
            es + dt.timedelta(days=1),    # Easter Monday
            es + dt.timedelta(days=39),   # Ascension
            es + dt.timedelta(days=50),   # Whit Monday
            es + dt.timedelta(days=60),   # Corpus Christi
        }

    holidays = set()
    for y in (d.year - 1, d.year, d.year + 1):
        holidays |= _movable(y)

    result = best(d)
    while result in holidays:
        result = best(result + dt.timedelta(days=1))
    return result
```

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| collection: next business day (Ticino, fixed only) | 94.156 % | 93.989 % |
| collection: next business day (Swiss federal) | 94.049 % | 93.954 % |
| collection: next weekday | 90.659 % | 90.510 % |
| collection: same day | 72.806 % | 73.673 % |
| collection: previous business day (Ticino) | 67.258 % | 68.225 % |

_168 s_
