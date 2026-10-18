# Rule search stalled: ablation_t1_no_easter_holidays / all rows / payment method == 'LS'

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: Ablation: t1 with the Easter holidays removed from the dictionary. The engine should find the rest of the rule and leave over exactly the due dates near Easter, with a prompt that shows them, for a person or an LLM to add the missing brick.

Best rule: {'collection': 'next business day (Ticino, fixed only)'} - 99.606 % exact on the search rows, 99.323 % on held-out policies.

Holes and the bricks already tried:
- collection: same day, next weekday, next business day (Swiss federal), next business day (Ticino, fixed only), previous business day (Ticino)

Rows the best rule gets wrong (56 rows; features, expected, calculated; the 20 most frequent cases):
- {payment method: LS, frequency: M, due date: 2027-03-28} expected [target value removed] calculated 2027-03-29  (x31)
- {payment method: LS, frequency: M, due date: 2027-03-29} expected [target value removed] calculated 2027-03-29  (x6)
- {payment method: LS, frequency: M, due date: 2027-03-27} expected [target value removed] calculated 2027-03-29  (x3)
- {payment method: LS, frequency: M, due date: 2027-05-27} expected [target value removed] calculated 2027-05-27  (x3)
- {payment method: LS, frequency: M, due date: 2027-05-15} expected [target value removed] calculated 2027-05-17  (x3)
- {payment method: LS, frequency: M, due date: 2027-05-16} expected [target value removed] calculated 2027-05-17  (x2)
- {payment method: LS, frequency: Q, due date: 2027-05-15} expected [target value removed] calculated 2027-05-17  (x2)
- {payment method: LS, frequency: M, due date: 2027-05-06} expected [target value removed] calculated 2027-05-06  (x2)
- {payment method: LS, frequency: Q, due date: 2027-03-29} expected [target value removed] calculated 2027-03-29
- {payment method: LS, frequency: Q, due date: 2027-03-27} expected [target value removed] calculated 2027-03-29
- {payment method: LS, frequency: M, due date: 2027-05-17} expected [target value removed] calculated 2027-05-17
- {payment method: LS, frequency: Q, due date: 2027-05-27} expected [target value removed] calculated 2027-05-27

How the bricks of each hole are called (real calls of the best rule on missed rows):
- collection(datetime.date(2027, 3, 29)) -> datetime.date(2027, 3, 29)
- collection(datetime.date(2027, 3, 28)) -> datetime.date(2027, 3, 29)
- collection(datetime.date(2027, 3, 29)) -> datetime.date(2027, 3, 29)

The best rule is right on every other row, so extend it rather than rewrite it: `best(...)` is the
current best brick of the hole (the one called above) and can be called inside your brick.

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `best`, `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.
