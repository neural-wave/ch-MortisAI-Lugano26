"""One policy that breaks a rule costs that policy, not the whole task.

The private policies are unseen. A row the rules do not expect (no policy version on a date, no main risk,
an impossible date) would raise and lose every value of the task. Here the policy is left out instead and
named on stderr; the quality gate fails if a train policy is skipped, so a rule cannot hide behind this.
"""
import sys


def per_policy(task, policies, calculate):
    """Merge the {key: value} of `calculate(pid, rows)` over the (pid, rows) pairs; a failing policy is skipped."""
    result = {}
    for pid, rows in policies:
        try:
            result.update(calculate(pid, rows))
        except Exception as error:  # any error of one policy must not stop the others
            print(f'{task}: skipped policy {pid} ({type(error).__name__}: {error})', file=sys.stderr)
    return result
