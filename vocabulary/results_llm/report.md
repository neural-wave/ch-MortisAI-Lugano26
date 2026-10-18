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
| all rows / payment method == 'LS' / not due date < 2027-03-27 | collection: **proposed: next business day (Ticino, fixed + Easter movable feasts) (answer 1) (extends: next business day (Ticino, fixed only))** | 100.000 % | 100.000 % |
| all rows / not payment method == 'LS' | collection: **same day** | 100.000 % | 100.000 % |

Brick proposed by the model and kept (all rows / payment method == 'LS' / proposals for collection; kept: exact rows (search, held out) (12143, 2829) -> (12183, 2845)): **proposed: next business day (Ticino, fixed + Easter movable feasts) (answer 1) (extends: next business day (Ticino, fixed only))**

```python
def brick(d: dt.date) -> dt.date:
    # name: next business day (Ticino, fixed + Easter movable feasts)

    def _easter(year: int) -> dt.date:
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

    es = _easter(d.year)
    movable_holidays = {
        es - dt.timedelta(days=2),    # Good Friday (Venerdì Santo)
        es + dt.timedelta(days=1),    # Easter Monday (Lunedì dell'Angelo)
        es + dt.timedelta(days=39),   # Ascension (Ascensione)
        es + dt.timedelta(days=49),   # Pentecost (Pentecoste) – always Sunday
        es + dt.timedelta(days=50),   # Whit Monday (Lunedì di Pentecoste)
        es + dt.timedelta(days=60),   # Corpus Christi (Corpo di Dio)
    }

    result = best(d)
    while result in movable_holidays:
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

_180 s_
