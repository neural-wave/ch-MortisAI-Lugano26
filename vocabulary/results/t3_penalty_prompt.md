# Rule search stalled: t3_penalty / all rows

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: t3 surrender penalty: how the policy years are counted, whether waivers apply, how it is rounded.

Target: surrender value; input: the policy value before the penalty (diagnostic column).
Penalty rate: NRSURR by the product's surrender scale and the policy years, 0 without a row.

Best rule: {'policy years': 'completed policy years', 'waiver': 'waiver periods apply (NRWAIV)', 'rounding': 'truncate before 2007-08-11, then half up'} - 99.756 % exact on the search rows, 99.678 % on held-out policies.

Holes and the bricks already tried:
- policy years: completed policy years, calendar years since start, started policy years, days / 365, truncated
- waiver: waiver periods apply (NRWAIV), no waivers
- rounding: half up, truncate, truncate before 2007-08-11, then half up

Rows the best rule gets wrong (16 rows; features, expected, calculated; the 20 most frequent cases):
- {valuation date: 2025-12-31, product: FLFX} expected [target value removed] calculated 82049.81
- {valuation date: 2025-12-31, product: FLSP} expected [target value removed] calculated 103462.37
- {valuation date: 2020-04-30, product: FLFX} expected [target value removed] calculated 8062.73
- {valuation date: 2020-04-30, product: FLKL} expected [target value removed] calculated 23586.49
- {valuation date: 2020-04-30, product: FLFX} expected [target value removed] calculated 6771.07
- {valuation date: 2025-12-31, product: FLKL} expected [target value removed] calculated 17563.65
- {valuation date: 2025-12-31, product: FLKL} expected [target value removed] calculated 13284.66
- {valuation date: 2020-04-30, product: FLSP} expected [target value removed] calculated 65303.75
- {valuation date: 2020-04-30, product: FLKL} expected [target value removed] calculated 1716.85
- {valuation date: 2025-12-31, product: FLKL} expected [target value removed] calculated 20123.77
- {valuation date: 2020-04-30, product: FLFX} expected [target value removed] calculated 7382.81
- {valuation date: 2025-12-31, product: FLKL} expected [target value removed] calculated 100073.97
- {valuation date: 2025-12-31, product: FLFX} expected [target value removed] calculated 31532.25
- {valuation date: 2025-12-31, product: FLKL} expected [target value removed] calculated 45297.77
- {valuation date: 2025-12-31, product: FLFX} expected [target value removed] calculated 43787.99
- {valuation date: 2020-04-30, product: FLKL} expected [target value removed] calculated 31765.36

How the bricks of each hole are called (real calls of the best rule on missed rows):
- policy years(datetime.date(2011, 2, 1), datetime.date(2025, 12, 31)) -> 14
- policy years(datetime.date(2023, 11, 11), datetime.date(2025, 12, 31)) -> 2
- policy years(datetime.date(2005, 5, 1), datetime.date(2020, 4, 30)) -> 14
- rounding(Decimal('82049.81'), datetime.date(2025, 12, 31)) -> Decimal('82049.81')
- rounding(Decimal('103462.37'), datetime.date(2025, 12, 31)) -> Decimal('103462.37')
- rounding(Decimal('8062.73'), datetime.date(2020, 4, 30)) -> Decimal('8062.73')

The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the
current best brick of the hole (the one called above) and can be called inside your brick.

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.
