"""One premium item over the funds of its policy (t3): trade date, pot, gross share and net amount per fund.

The entry rate is that of the broker tier (or an ENT agreement) on rule.T3_ENTRY_DATE, the pot is decided on
rule.T3_POT_DATE, the allocation set on rule.T3_ALLOCATION_DATE (all three: the money date); each fund buys on
rule.T3_TRADE_DATE (the next price date) and its amount is rule.T3_SPLIT rounded by the era of the trade date.
The search runs this very function with its trial choices on the 407,636 PRM bookings of t3_booking.csv.

How one premium becomes fund amounts (t3): the order of share, net and rounding.

The net amount of a fund is the gross premium times the fund share times one less the entry rate, rounded
once, or rounded after the share, or the net premium rounded first and then shared. All three give the same
cent on every one of the 407,636 PRM bookings of the train policies (rules.py notes the tie, T3_SPLIT): no
fund share times a net rate of the train data ends on a half cent in one order and not in another.

Converting amounts in policy currency to fund units, by the choices of ledger.rule (T3_*), to 6 decimals.

The exchange rate is fund currency per policy currency, so an amount times the rate over the price gives the
units. A premium buys at rule.T3_PREMIUM_PRICE (the issue price) with the rate of rule.T3_PREMIUM_FX_DATE
(the day before the trade, as BK_FXRAT in NRBOOK), rounded by the pair of its era (COBOL truncates, Neuron NG
rounds half up). Checked on every unit of the 407,636 PRM bookings of the train policies: all exact. Charges
cancel units in ledger_cancel.
"""
from tables import day, scaled
from conventions_fx_dates import net_share
from conventions_pot import pot, shares
from tables import MICRO


def premium_parts(ledger, item):
    """One premium item over the funds: [(fund, trade date, pot, gross share, net amount, entry rate)]."""
    rule, history, money = ledger.rule, ledger.history, day(item['PR_RCVDT'])
    gross, net = scaled(item['PR_AMTRC'], 2), net_share(ledger, rule.T3_ENTRY_DATE(item, history))
    unit_pot, parts = pot(ledger, rule.T3_POT_DATE(item, history)), []
    for share in shares(ledger, rule.T3_ALLOCATION_DATE(item, history)):
        fund, fraction = share['AL_FNDID'], scaled(share['AL_PCTG'])
        trade = rule.T3_TRADE_DATE(ledger.market, fund, money)
        rounding = ledger.era(rule.T3_AMOUNT_ROUNDING, rule.T3_AMOUNT_ERA_DATE, trade, money)
        amount = rule.T3_SPLIT(gross, fraction, net, rounding, trade)
        parts.append((fund, trade, unit_pot, gross * fraction, amount, 1 - net))
    return parts


def share_then_net(gross, share, net, rounding, date):
    """round(gross x share x net): one rounding."""
    return rounding(gross * share * net, date)


def rounded_share_then_net(gross, share, net, rounding, date):
    """The share of the fund rounded to the cent first, then the net amount rounded."""
    return rounding(rounding(gross * share, date) * net, date)


def net_then_share(gross, share, net, rounding, date):
    """The net premium rounded first, then the share of the fund rounded."""
    return rounding(rounding(gross * net, date) * share, date)


SPLITS = {'gross x share x net, rounded once': share_then_net, 'share rounded, then net': rounded_share_then_net,
          'net rounded, then share': net_then_share}


def fx(ledger, fund, date):
    """Fund currency per policy currency on `date`, read and rounded as the rules say."""
    rule = ledger.rule
    return ledger.market.fx(ledger.ccy, fund, date, rule.T3_RATE_LOOKUP, rule.T3_CROSS_RATE)


def bought(ledger, fund, trade, money, amount):
    """Units of `fund` that `amount` buys on the trade date."""
    rule = ledger.rule
    price = rule.T3_PREMIUM_PRICE(ledger.market, fund, trade)
    units = amount * fx(ledger, fund, rule.T3_PREMIUM_FX_DATE(trade, money)) / price
    return ledger.era(rule.T3_UNITS_ROUNDING, rule.T3_UNITS_ERA_DATE, trade, money)(units, trade, MICRO)
