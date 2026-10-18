"""Moving a due date to the day the money is collected, date -> date: the candidate shifts of t1.

A direct debit can only be drawn on a business day of the bank's canton, a bank transfer arrives when the
customer sends it. The family goes from no shift over plain weekdays to the federal and the Ticino calendar
(with and without the Easter holidays, and with Good Friday); the search keeps the one that matches every
collection date of the train policies, per payment method (rules.py, T1_COLLECTION): direct debits (12,508
due dates) move to the next business day of Ticino with the Easter holidays and without Good Friday, bank
transfers (2,520) stay on the due date.
"""
from conventions_holidays import business_day, FEDERAL, TICINO, EASTER_TICINO


def same_day(date):
    """No shift: the money is booked on the due date itself."""
    return date


def next_weekday(date):
    """The next Monday to Friday, no holidays."""
    return business_day(date)


def next_business_day_federal(date):
    """The next business day of the federal holidays only."""
    return business_day(date, FEDERAL)


def next_business_day_ticino_fixed(date):
    """The next business day of Ticino without the movable Easter holidays."""
    return business_day(date, TICINO)


def next_business_day_ticino(date):
    """The next business day of Ticino, Easter holidays included."""
    return business_day(date, TICINO, EASTER_TICINO)


def next_business_day_ticino_good_friday(date):
    """As next_business_day_ticino, with Good Friday as in most other cantons."""
    return business_day(date, TICINO, (-2, *EASTER_TICINO))


def previous_business_day_ticino(date):
    """The previous business day of Ticino, Easter holidays included."""
    return business_day(date, TICINO, EASTER_TICINO, step=-1)


SHIFTS = {'same day': same_day, 'next weekday': next_weekday,
          'next business day (Swiss federal)': next_business_day_federal,
          'next business day (Ticino, fixed only)': next_business_day_ticino_fixed,
          'next business day (Ticino, with Easter)': next_business_day_ticino,
          'next business day (Ticino, with Easter and Good Friday)': next_business_day_ticino_good_friday,
          'previous business day (Ticino)': previous_business_day_ticino}
