# Rule finder report

## ablation_t1_no_easter_holidays

Ablation: t1 with the Easter holidays removed from the dictionary. The engine should find the rest of the rule and leave over exactly the due dates near Easter, with a prompt that shows them, for a person or an LLM to add the missing brick.

15028 rows, 5 combinations of collection (5).

| Segment | Rule | Search | Held out |
|---|---|---|---|
| all rows | collection: **next business day (Ticino, fixed only)** | 94.156 % | 93.989 % |
| ↳ misses concentrate where `payment method == 'LS'` | 0.450 % missed if true, 32.820 % if false | | |
| all rows / payment method == 'LS' | collection: **next business day (Ticino, fixed only)** | 99.606 % | 99.323 % |
| ↳ misses concentrate where `due date < 2027-03-27` | 0.000 % missed if true, 1.720 % if false | | |
| all rows / payment method == 'LS' / due date < 2027-03-27 | collection: **next business day (Ticino, fixed only)** | 100.000 % | 100.000 % |
| all rows / payment method == 'LS' / not due date < 2027-03-27 | collection: **proposed: next business day (Ticino, fixed + Easter-cycle movable holidays) (answer 1)** | 99.734 % | 100.000 % |
| ↳ left over | 7 rows the rule does not explain (prompt for an LLM written) | | |
| all rows / not payment method == 'LS' | collection: **same day** | 100.000 % | 100.000 % |

Brick proposed by the model and kept (all rows / payment method == 'LS' / not due date < 2027-03-27 / proposals for collection): **proposed: next business day (Ticino, fixed + Easter-cycle movable holidays) (answer 1)**

```python
def brick(d):
    # name: next business day (Ticino, fixed + Easter-cycle movable holidays)

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

    def _is_ticino_holiday(date):
        # Fixed public holidays in Ticino
        if (date.month, date.day) in (
            (1, 1), (1, 6), (4, 25), (5, 1),
            (8, 1), (12, 8), (12, 25), (12, 26)
        ):
            return True
        # Easter-cycle movable holidays (Good Friday, Easter Monday,
        # Ascension, Whit Monday, Corpus Christi)
        es = _easter_sunday(date.year)
        if date in (
            es - dt.timedelta(2),   # Good Friday
            es + dt.timedelta(1),   # Easter Monday
            es + dt.timedelta(39),  # Ascension Thursday
            es + dt.timedelta(50),  # Whit Monday
            es + dt.timedelta(60),  # Corpus Christi
        ):
            return True
        return False

    r = d
    while r.weekday() >= 5 or _is_ticino_holiday(r):
        r += dt.timedelta(1)
    return r
```

Runners-up on all rows:

| Rule | Search | Held out |
|---|---|---|
| collection: next business day (Ticino, fixed only) | 94.156 % | 93.989 % |
| collection: next business day (Swiss federal) | 94.049 % | 93.954 % |
| collection: next weekday | 90.659 % | 90.510 % |
| collection: same day | 72.806 % | 73.673 % |
| collection: previous business day (Ticino) | 67.258 % | 68.225 % |

_607 s_
