"""Candidate tax on gains accumulated in different rate periods.

All dates and rates come from NRTAXR. Boundary fund values reuse the same
accounting replay as t3. There are no policy identifiers or reference outputs.
"""
import datetime as dt
from functools import cache
from decimal import Decimal as D
from tables import day, grouped, by_key, received, scaled
from tax_rate_rows import rows_of
from tax_residence import rate
from tax_money import convert
from tax_payouts import payouts
from tax_birth import paid_in
from tax_premiums import premiums, era
from eras import rounded
from orders import customer_orders
from accounts_replay import replay
from accounts_surrender import surrender_value


def flat_rate(folder,payout,base,at):
    return rounded(base*rate(folder,'IT','SOS',payout.date,at),era(payout))


@cache
def boundaries(folder):
    rows=rows_of(folder).get(('IT','SOS'),[])
    starts=sorted({day(r['TX_VLDFR']) for r in rows})
    return tuple(d-dt.timedelta(days=1) for d in starts[1:])


@cache
def snapshots(folder,policy):
    dates=boundaries(folder)
    orders=customer_orders(folder)
    paid=by_key(received(folder),'PR_POLNR')
    ledger,values=replay(folder,policy,paid[policy],orders[policy],dates)
    return ledger,values


def historical_tax(folder,payout,base,at,clamp=False,net=False,round_parts=False,payout_fx=False):
    ledger,values=snapshots(folder,payout.policy)
    current=rate(folder,'IT','SOS',payout.date,at)
    terms=[base*current]
    for boundary in boundaries(folder):
        if boundary>=payout.date or boundary not in values:continue
        value=values[boundary]
        if net:value=surrender_value(folder,ledger,boundary,value)
        fxdate=payout.date if payout_fx else boundary
        value=convert(folder,value,payout.currency,'EUR',fxdate,era(payout))
        returned=D(0)
        remaining=D(1)
        for earlier in payouts(folder)[payout.policy]:
            if earlier.event>=payout.event:break
            if earlier.date<=boundary:
                capital=paid_in(folder,earlier,'EUR')-returned
                returned+=rounded(capital*earlier.share,era(earlier)) if earlier.kind=='withdrawal' else capital
            else:
                remaining*=1-earlier.share if earlier.kind=='withdrawal' else 0
        premium=sum((convert(folder,p.amount,payout.currency,'EUR',p.date,p.date)
                     for p in premiums(folder)[payout.policy] if p.date<=boundary),D(0))
        gain=value-(premium-returned)
        if clamp:gain=max(gain,D(0))
        share=payout.share if payout.kind=='withdrawal' else D(1)
        older=rate(folder,'IT','SOS',boundary,at)
        newer=rate(folder,'IT','SOS',boundary+dt.timedelta(days=1),at)
        terms.append(gain*remaining*share*(older-newer))
    amount=sum((rounded(v,era(payout)) if round_parts else v for v in terms),D(0))
    return max(D('0.00'),rounded(amount,era(payout)))


def historical_signed(folder,payout,base,at):return historical_tax(folder,payout,base,at)
def historical_positive(folder,payout,base,at):return historical_tax(folder,payout,base,at,clamp=True)
def historical_net(folder,payout,base,at):return historical_tax(folder,payout,base,at,net=True)
def historical_parts(folder,payout,base,at):return historical_tax(folder,payout,base,at,round_parts=True)
def historical_fx_at_payout(folder,payout,base,at):return historical_tax(folder,payout,base,at,payout_fx=True)


IT_TAXES={'flat rate':flat_rate,'historical signed':historical_signed,'historical positive':historical_positive,
          'historical surrender value':historical_net,'historical rounded components':historical_parts,
          'historical current FX':historical_fx_at_payout}
