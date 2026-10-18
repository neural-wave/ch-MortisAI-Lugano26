"""t7: the day Neuron paid a withheld tax to the tax office, and the shift of a day the office is closed.

The only evidence is the first example of the task: a German payout of 17 July 2006 was remitted on 10 August. The
law gives Italy the 16th of the next month and Switzerland 30 days after the month end; Neuron's yearly tax batch
runs on the 10th. A weekend falls on 30 % of the dates without a shift; a closed day moves the payment to the next day
the tax office is open (office_business_day).
"""
import calendar
import datetime as dt
from conventions_dates import add_months
from conventions_calendar import same_day, next_weekday, next_business_day_ticino
from conventions_holidays import business_day

# The holidays of the tax office a tax is paid to: fixed (month, day) and days after Easter Sunday. The Swiss federal
# tax administration is in Bern (Berchtold's day, 2 January, is a holiday there, not in Ticino).
OFFICE_HOLIDAYS = {
    'CH': (((1, 1), (1, 2), (8, 1), (12, 25), (12, 26)), (-2, 1, 39, 50)),
    'IT': (((1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)), (1,)),
    'DE': (((1, 1), (5, 1), (10, 3), (12, 25), (12, 26)), (-2, 1, 39, 50)),
    'LU': (((1, 1), (5, 1), (6, 23), (8, 15), (11, 1), (12, 25), (12, 26)), (1, 39, 50)),
}


def month_end(date):
    """The last day of the month of `date`."""
    return date.replace(day=calendar.monthrange(date.year, date.month)[1])


def day_of_next_month(date, n):
    """The n-th of the month after `date`, at most its last day."""
    following = add_months(date.replace(day=1), 1)
    return following.replace(day=min(n, month_end(following).day))


def tenth_of_next_month(date):
    """The 10th of the next month: the German example of the task, and the day Neuron's yearly tax batch runs (10
    January, 03:00), so possibly the day it remitted everything."""
    return day_of_next_month(date, 10)


def sixteenth_of_next_month(date):
    """The 16th of the next month (the Italian law)."""
    return day_of_next_month(date, 16)


def thirty_days_after_month_end(date):
    """30 days after the end of the month (the Swiss law, VStG art. 16)."""
    return month_end(date) + dt.timedelta(days=30)


def no_date():
    """None, as the task writes it: "remittance date is None if nothing was withheld"."""
    return None


def empty_text():
    """An empty text, as an empty cell of the answer file reads (in case None is dropped as malformed)."""
    return ''


NO_REMITTANCE = {'None': no_date, 'an empty text': empty_text}
REMITTANCE_DAYS = {'the 10th of the next month': tenth_of_next_month, 'the 16th of the next month': sixteenth_of_next_month,
                   '30 days after the month end': thirty_days_after_month_end}
def office_business_day(date, country):
    """The day itself if the tax office of `country` is open, else its next business day (the released samples:
    a Swiss remittance due on Tuesday 2 January was paid on Wednesday 3 January)."""
    return business_day(date, *OFFICE_HOLIDAYS.get(country, ((), ())))


def unshifted(date, country):
    """The day itself."""
    return same_day(date)


def next_weekday_anywhere(date, country):
    """The next weekday, whatever the country."""
    return next_weekday(date)


def ticino_business_day(date, country):
    """The next business day of Ticino, where Neuron ran, whatever the country."""
    return next_business_day_ticino(date)


REMITTANCE_SHIFTS = {'none': unshifted, 'next weekday': next_weekday_anywhere, 'next business day (Ticino)': ticino_business_day,
                     'next business day of the tax office': office_business_day}
