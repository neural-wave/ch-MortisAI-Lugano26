"""t7: open choices of the rows the answers give (rules.py T7_LOSS_BASE, T7_BOC_DATED, T7_BOL_FIRST_YEAR).

Each a submission of its own (logs/t7_leaderboard.md): the base of a payout at a loss in Italy and Germany (0 or the
signed gain), a remittance date for stamp duty collected alone ("None if nothing was withheld", 182 rows), and the
yearly stamp duty of the first policy year (in full or for the days from the start, as the duty of a payout year).
"""
from decimal import Decimal as D
from tables import grouped, day

TAXED_GAINS = ('IT', 'DE')  # the countries that tax the gain of a payout


def zero_for_a_loss(profit, country):
    """The base of a gain, 0 for a loss; a country without a tax on gains (Luxembourg) 0 always: the choice of
    version 22, right for the untaxed rows of the sample as far as submission 2 shows."""
    return max(profit, D('0.00')) if country in TAXED_GAINS else D('0.00')


def the_signed_gain(profit, country):
    """The gain as it is, a loss negative, in the countries that tax the gain (Italy, Germany: there the base is the
    gain whether or not a tax is due); a country without such a tax (Luxembourg) keeps 0."""
    return profit if country in TAXED_GAINS else D('0.00')


def dated(stamp):
    """Stamp duty collected (BOC) is remitted like a withheld tax: its row gets a remittance date (the Italian
    tax office receives it as it receives the substitute tax)."""
    return bool(stamp)


def not_dated(stamp):
    """Only a withheld tax is remitted ("None if nothing was withheld", the task): stamp duty collected alone gives
    no date (182 rows, 168 of them Italian payouts with stamp duty only)."""
    return False


def in_full(folder, booking):
    """The yearly stamp duty of the first policy year as of any year: the rate times the value on 31 December,
    however late in the year the policy began."""
    return D(1)


def from_the_start(folder, booking):
    """The yearly stamp duty of the first policy year for the days from the start to 31 December (the day of the
    year of 31 December is the length of the year)."""
    start = min(day(r['PH_BEGDT']) for r in grouped(folder, 'NRPOLH', 'PH_POLNR')[booking.policy])
    return min(D(1), D((booking.date - start).days + 1) / booking.date.timetuple().tm_yday)


LOSS_BASES = {'zero for a loss': zero_for_a_loss, 'the signed gain in Italy and Germany': the_signed_gain}
BOC_DATES = {'dated': dated, 'no date': not_dated}
FIRST_YEARS = {'in full': in_full, 'from the start': from_the_start}
