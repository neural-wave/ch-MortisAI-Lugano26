"""The surrender penalty (t3): how the policy years of NRSURR are counted, and the waiver periods (NRWAIV).

SR_YEAR is "completed policy years" (SCHEMA): the anniversaries passed (a 29 February start completes its
year on 28 February), or the calendar years since the start, the started years, or the days over 365. In a
waiver period (NRWAIV, both days included) no penalty applies, or the periods are ignored. Checked on the
surrender values of t3_surrender_value.csv, with its policy value column as the value before the penalty.
"""
from tables import table, day
from conventions_birth import completed_years


def completed_policy_years(start, date):
    """The policy anniversaries passed on `date`."""
    return completed_years(start, date)


def calendar_years_since_start(start, date):
    """The difference of the calendar years."""
    return date.year - start.year


def started_policy_years(start, date):
    """The policy year `date` falls in, counted from 1."""
    return completed_years(start, date) + 1


def days_over_365(start, date):
    """The days since the start over 365, cut."""
    return (date - start).days // 365


def waiver_periods_apply(folder, date):
    """No penalty inside a waiver period of NRWAIV."""
    return any(day(r['WV_VLDFR']) <= date <= day(r['WV_VLDTO']) for r in table(folder, 'NRWAIV'))


def no_waivers(folder, date):
    """The waiver periods are ignored."""
    return False


PENALTY_YEARS = {'completed policy years': completed_policy_years, 'calendar years since start': calendar_years_since_start,
                 'started policy years': started_policy_years, 'days / 365, cut': days_over_365}
WAIVERS = {'waiver periods apply': waiver_periods_apply, 'no waivers': no_waivers}
