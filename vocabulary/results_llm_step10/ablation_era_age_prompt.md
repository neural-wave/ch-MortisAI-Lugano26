# Rule search stalled: ablation_era_age / all rows / application date < 2007-08-11 / application date < 2006-04-01

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: Ablation: the era case without the age rule of the COBOL system (days since birth / 365, rounded).

The diagnosis still finds the application date of 2007-08-11 (a landmark: the day of all events 800); the
offers before it then miss with every remaining age rule. With a model connected, a proposed age brick is
kept only if it raises the exact rows of the held-out policies.

Best rule: {'rounding': 'truncate', 'entry age': 'days / 365.25', 'birth date': 'clamp to the month end'} - 98.510 % exact on the search rows, 98.649 % on held-out policies.

Holes and the bricks already tried:
- rounding: half up, truncate, half even, half down, up, 5 Rappen
- entry age: last birthday, nearest birthday, calendar years, days / 365.25
- birth date: clamp to the month end, roll into the next month

Rows the best rule gets wrong (10 rows; features, expected, calculated; the 20 most frequent cases):
- {application date: 1998-05-02, start date: 1998-06-01, product: FLKL, frequency: M} expected [target value removed] calculated (7012.88, 14296.50)
- {application date: 1997-09-07, start date: 1997-11-01, product: FLKL, frequency: M} expected [target value removed] calculated (8298.31, 16928.54)
- {application date: 2002-10-10, start date: 2002-12-01, product: FLFX, frequency: M} expected [target value removed] calculated (2700.14, 5518.55)
- {application date: 2003-11-18, start date: 2004-01-01, product: FLKL, frequency: M} expected [target value removed] calculated (2847.96, 5805.63)
- {application date: 2002-04-27, start date: 2002-06-01, product: FLSP, frequency: E} expected [target value removed] calculated (132677.61, 138183.69)
- {application date: 2000-04-23, start date: 2000-05-01, product: FLSP, frequency: E} expected [target value removed] calculated (102374.11, 106613.78)
- {application date: 2002-01-28, start date: 2002-03-01, product: FLFX, frequency: M} expected [target value removed] calculated (4459.36, 9093.21)
- {application date: 1994-07-26, start date: 1994-08-01, product: FLKL, frequency: Q} expected [target value removed] calculated (8494.48, 17316.71)
- {application date: 1996-01-09, start date: 1996-02-01, product: FLFX, frequency: Q} expected [target value removed] calculated (6596.30, 13498.45)
- {application date: 2000-03-23, start date: 2000-05-01, product: FLKL, frequency: J} expected [target value removed] calculated (8409.34, 17143.39)

How the bricks of each hole are called (real calls of the best rule on missed rows):
- rounding(Decimal('579.50'), datetime.date(1998, 5, 2)) -> Decimal('579.50')
- rounding(Decimal('0.57250'), datetime.date(1998, 5, 2)) -> Decimal('0.57')
- rounding(Decimal('0.0004265644583333333333333333333'), datetime.date(1998, 5, 2)) -> Decimal('0.00')
- entry age(datetime.date(1957, 12, 6), datetime.date(1998, 6, 1)) -> 40
- entry age(datetime.date(1958, 5, 10), datetime.date(1997, 11, 1)) -> 39
- entry age(datetime.date(1945, 6, 12), datetime.date(2002, 12, 1)) -> 57
- birth date('571206') -> datetime.date(1957, 12, 6)
- birth date('580510') -> datetime.date(1958, 5, 10)
- birth date('450612') -> datetime.date(1945, 6, 12)

The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the
current best brick of the hole (the one called above) and can be called inside your brick.

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.

---

# Rule search stalled: ablation_era_age / all rows / application date < 2007-08-11 / not application date < 2006-04-01

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: Ablation: the era case without the age rule of the COBOL system (days since birth / 365, rounded).

The diagnosis still finds the application date of 2007-08-11 (a landmark: the day of all events 800); the
offers before it then miss with every remaining age rule. With a model connected, a proposed age brick is
kept only if it raises the exact rows of the held-out policies.

Best rule: {'rounding': 'truncate', 'entry age': 'nearest birthday', 'birth date': 'clamp to the month end'} - 95.614 % exact on the search rows, 93.333 % on held-out policies.

Holes and the bricks already tried:
- rounding: half up, truncate, half even, half down, up, 5 Rappen
- entry age: last birthday, nearest birthday, calendar years, days / 365.25
- birth date: clamp to the month end, roll into the next month

Rows the best rule gets wrong (7 rows; features, expected, calculated; the 20 most frequent cases):
- {application date: 2006-04-01, start date: 2006-05-01, product: FLKL, frequency: Q} expected [target value removed] calculated (8782.95, 17813.58)
- {application date: 2006-05-09, start date: 2006-06-01, product: FLKL, frequency: J} expected [target value removed] calculated (4824.21, 9784.29)
- {application date: 2006-04-07, start date: 2006-06-01, product: FLKL, frequency: M} expected [target value removed] calculated (6773.93, 13739.68)
- {application date: 2006-05-11, start date: 2006-07-01, product: FLFX, frequency: M} expected [target value removed] calculated (5478.91, 11134.99)
- {application date: 2007-04-19, start date: 2007-05-01, product: FLKL, frequency: M} expected [target value removed] calculated (5111.16, 10381.89)
- {application date: 2006-09-21, start date: 2006-10-10, product: FLFX, frequency: M} expected [target value removed] calculated (6190.46, 12563.26)
- {application date: 2006-08-24, start date: 2006-08-31, product: FLKL, frequency: M} expected [target value removed] calculated (4923.96, 9993.91)

How the bricks of each hole are called (real calls of the best rule on missed rows):
- rounding(Decimal('2180.25'), datetime.date(2006, 4, 1)) -> Decimal('2180.25')
- rounding(Decimal('2.17275'), datetime.date(2006, 4, 1)) -> Decimal('2.17')
- rounding(Decimal('0.01854941491666666666666666667'), datetime.date(2006, 4, 1)) -> Decimal('0.01')
- entry age(datetime.date(1943, 11, 3), datetime.date(2006, 5, 1)) -> 62
- entry age(datetime.date(1945, 12, 2), datetime.date(2006, 6, 1)) -> 60
- entry age(datetime.date(1974, 12, 6), datetime.date(2006, 6, 1)) -> 31
- birth date('431103') -> datetime.date(1943, 11, 3)
- birth date('451202') -> datetime.date(1945, 12, 2)
- birth date('741206') -> datetime.date(1974, 12, 6)

The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the
current best brick of the hole (the one called above) and can be called inside your brick.

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.
