"""The day of month a premium schedule aims at (t1), (past due dates, start date) -> day.

After a short month the schedule returns to its anchor day: the day of the start, of the last due date, or
the highest or most common day among the recent due dates (the highest of the last 12 undoes the clamping of
a 31st to the 28th or 30th). A schedule converted from the COBOL system can have drifted from the 31st to the
28th, so the history and the start date need not agree (40 policies in force, docs/holes.md).
"""
from collections import Counter


def start_day(past, start):
    """The day of month of the start date."""
    return start.day


def last_due_day(past, start):
    """The day of month of the last due date (of the start without one)."""
    return past[-1].day if past else start.day


def highest_recent_day(past, start):
    """The highest day among the last 12 due dates."""
    return max(d.day for d in past[-12:]) if past else start.day


def highest_day_ever(past, start):
    """The highest day among all due dates."""
    return max(d.day for d in past) if past else start.day


def most_common_recent_day(past, start):
    """The most common day among the last 12 due dates (the earliest day on a tie)."""
    days = Counter(d.day for d in past[-12:]).most_common()
    return min(days, key=lambda kv: (-kv[1], kv[0]))[0] if past else start.day


ANCHOR_DAYS = {'start day': start_day, 'day of the last due date': last_due_day,
               'highest day of the last 12 due dates': highest_recent_day, 'highest day ever': highest_day_ever,
               'most common day of the last 12 due dates': most_common_recent_day}
