# Rule search stalled: ablation_t1_no_easter_holidays / all rows / payment method == 'LS' / not due date < 2027-03-27

Context: the target comes from the legacy system of a Swiss life insurer in Ticino (COBOL until 2007-08-11, Neuron NG since). Amounts in francs, dates as calendar dates.
Target: Ablation: t1 with the Easter holidays removed from the dictionary. The engine should find the rest of the rule and leave over exactly the due dates near Easter, with a prompt that shows them, for a person or an LLM to add the missing brick.

Best rule: {'collection': 'proposed: next business day (Ticino, fixed + Easter-cycle movable holidays) (answer 1)'} - 99.734 % exact on the search rows, 100.000 % on held-out policies.

Holes and the bricks already tried:
- collection: same day, next weekday, next business day (Swiss federal), next business day (Ticino, fixed only), previous business day (Ticino), proposed: next business day (Ticino, fixed + Easter-cycle movable holidays) (answer 1), proposed: next business day (Ticino, fixed + Easter-movable holidays) (answer 4)

Rows the best rule gets wrong (7 rows; features, expected, calculated; the 20 most frequent cases):
- {payment method: LS, frequency: M, due date: 2027-06-29} expected [target value removed] calculated 2027-06-29  (x6)
- {payment method: LS, frequency: Q, due date: 2027-06-29} expected [target value removed] calculated 2027-06-29

How the bricks of each hole are called (real calls of the best rule on missed rows):
- collection(datetime.date(2027, 6, 29)) -> datetime.date(2027, 6, 29)
- collection(datetime.date(2027, 6, 29)) -> datetime.date(2027, 6, 29)
- collection(datetime.date(2027, 6, 29)) -> datetime.date(2027, 6, 29)

Answer with 1 to 3 blocks of Python code (```python ... ```). Each block defines
`def brick(...)` with exactly the arguments shown for the hole, and its first line is a comment
`# name: <a short description of the rule>`. Available without import: `dt` (the datetime
module), `D` (Decimal), ROUND_HALF_UP, ROUND_HALF_EVEN, ROUND_HALF_DOWN, ROUND_DOWN, ROUND_UP
and plain Python. Write a general business rule: no policy numbers and no lists of the
expected values above. A brick is kept only if it raises the exact matches on held-out policies.
