# Neuron migration — Lifeware challenge, Neural Wave AI Hackathon

The rules of a legacy insurance system, found in its data and turned into code.

| Where | What |
|---|---|
| [`my_solution/`](my_solution/README.md) | **The submission**: `submission.py` and its modules, standard library only. Results, rules, ties and limits are in its README. |
| `autosolve.py` | **The one button**: searches every convention in the data and writes `my_solution/rules.py` (13 min); `--demo` shows the first targets in 40 s; `--verify` checks `rules.py` against the search. |
| [`vocabulary/`](vocabulary/README.md) | The rule-search engine: exact-match search over a dictionary of conventions, a decision tree on the misses, ties by a stated principle, a language model for what the dictionary lacks (sandboxed, kept only if no row gets worse). |
| [`figures/`](figures/README.md) | t6: the hidden rules made visible (`tools/figures.py`). |
| [`docs/generalization.md`](docs/generalization.md) | How much work a new target is: per target, per step, the ablations with the language model. |
| [`docs/holes.md`](docs/holes.md) | The 72 conventions of the calculation: where they are, the alternatives, the evidence (in Russian). |
| `tools/quality_gate.py` | Accuracy per task, maintainability, run time, tests and purity in one command. |
| `tests/` | Tests of the solution and of the generator of `rules.py`. |
| `logs/t7_leaderboard.md`, `logs/t7_evidence.json` | t7: what each leaderboard submission showed, and the evidence behind every T7 choice. |
| `starter_kit/` | The official `check.py` and `scoring.py`, unchanged. |

```
python3 autosolve.py                      # find the rules, write my_solution/rules.py, run check.py
cd starter_kit && python3 check.py --submission ../my_solution --legacy ../legacy --targets ../targets
```

The data (`legacy/`, `targets/`) is not in the repository.
