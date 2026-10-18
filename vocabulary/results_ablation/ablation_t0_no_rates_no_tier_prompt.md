# Rule search stalled: ablation_t0_no_rates_no_tier / all rows

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: Ablation: t0 without the rate table NRCOMR and without the broker tier (NRBROK is not read). The tier is a property of the broker that no read column carries: the broker number determines it, but through 400 brokers that a tree of three tests cannot map. The engine should NOT reach 100 %: it must report what it cannot explain instead of inventing a rule.

Best rule: {'rate': 'fitted 0.03', 'rounding': 'half up'} - 43.392 % exact on the search rows, 46.184 % on held-out policies.

Holes and the bricks already tried:
- rate: fitted 0.03, fitted 0.04, fitted 0.02
- rounding: half up, truncate, half even, half down, up, 5 Rappen, truncate before 2007-08-11, then half up

Rows the best rule gets wrong (39062 rows; features, expected, calculated; the 20 most frequent cases):
- {premium type: L, product: FLKL, broker: B00108} expected [target value removed] calculated 22.50  (x373)
- {premium type: L, product: FLKL, broker: B00145} expected [target value removed] calculated 9.15  (x358)
- {premium type: L, product: FLFX, broker: B00082} expected [target value removed] calculated 22.50  (x349)
- {premium type: L, product: FLKL, broker: B00345} expected [target value removed] calculated 21.30  (x333)
- {premium type: L, product: FLKL, broker: B00289} expected [target value removed] calculated 7.65  (x327)
- {premium type: L, product: FLFX, broker: B00028} expected [target value removed] calculated 5.55  (x325)
- {premium type: L, product: FLKL, broker: B00040} expected [target value removed] calculated 19.35  (x320)
- {premium type: L, product: FLKL, broker: B00070} expected [target value removed] calculated 2.25  (x318)
- {premium type: L, product: FLFX, broker: B00309} expected [target value removed] calculated 21.15  (x305)
- {premium type: L, product: FLFX, broker: B00376} expected [target value removed] calculated 16.65  (x302)
- {premium type: L, product: FLKL, broker: B00292} expected [target value removed] calculated 3.60  (x300)
- {premium type: L, product: FLKL, broker: B00176} expected [target value removed] calculated 7.50  (x296)
- {premium type: L, product: FLKL, broker: B00216} expected [target value removed] calculated 21.75  (x290)
- {premium type: L, product: FLFX, broker: B00052} expected [target value removed] calculated 15.90  (x287)
- {premium type: L, product: FLFX, broker: B00166} expected [target value removed] calculated 18.75  (x286)
- {premium type: L, product: FLKL, broker: B00106} expected [target value removed] calculated 20.85  (x279)
- {premium type: L, product: FLKL, broker: B00266} expected [target value removed] calculated 4.95  (x275)
- {premium type: L, product: FLKL, broker: B00252} expected [target value removed] calculated 7.05  (x268)
- {premium type: L, product: FLKL, broker: B00173} expected [target value removed] calculated 6.30  (x264)
- {premium type: L, product: FLKL, broker: B00244} expected [target value removed] calculated 2.25  (x261)

How the bricks of each hole are called (real calls of the best rule on missed rows):
- rounding(Decimal('5.55'), datetime.date(2007, 4, 29)) -> Decimal('5.55')
- rounding(Decimal('5.55'), datetime.date(2007, 5, 30)) -> Decimal('5.55')
- rounding(Decimal('5.55'), datetime.date(2007, 6, 28)) -> Decimal('5.55')

The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the
current best brick of the hole (the one called above) and can be called inside your brick.

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.
