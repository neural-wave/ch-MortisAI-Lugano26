"""Independent Fraction interpreter. No imports from domain or friend runtime."""
import calendar
import datetime as dt
from dataclasses import dataclass
from fractions import Fraction as F
from decimal import Decimal

@dataclass(frozen=True)
class Balance:
    value: F
    month: int

def decode(x):
    if isinstance(x,(bool,int,dt.date,F)): return x
    if isinstance(x,Decimal): return F(x)
    if hasattr(x,'value') and hasattr(x,'month'): return Balance(decode(x.value),x.month)
    if 'decimal' in x: return F(x['decimal'])
    if 'date' in x: return dt.date.fromisoformat(x['date'])
    if 'state' in x: return Balance(F(x['state']['value']),int(x['state']['month']))
    raise ValueError('Oracle unsupported value')

def canonical(x):
    x=decode(x)
    if isinstance(x,Balance): return ('state',x.value,x.month)
    if isinstance(x,dt.date): return ('date',x)
    if isinstance(x,bool): return ('bool',x)
    return ('number',F(x))

def rounded(x,date):
    n,d=(x*100).as_integer_ratio(); sign=-1 if n<0 else 1
    q,r=divmod(abs(n),d)
    if date>=dt.date(2007,8,11) and 2*r>=d: q+=1
    return F(sign*q,100)

def easter(year):
    a=year%19; b=year//100; c=year%100; d=b//4; e=b%4
    f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
    i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    return dt.date(year,(h+l-7*m+114)//31,1+(h+l-7*m+114)%31)

def following(date):
    fixed={(1,1),(1,6),(3,19),(5,1),(6,29),(8,1),(8,15),(11,1),(12,8),(12,25),(12,26)}
    while date.weekday()>=5 or (date.month,date.day) in fixed or (date-easter(date.year)).days in (1,39,50,60):
        date+=dt.timedelta(days=1)
    return date

def apply(op,a):
    if op=='add': return a[0]+a[1]
    if op=='sub': return a[0]-a[1]
    if op=='mul': return a[0]*a[1]
    if op=='rounded': return rounded(*a)
    if op=='deduct': return max(F(0),a[0]-a[1])
    if op=='management': return rounded(a[0]*a[1]/12,a[2])
    if op=='add_months':
        date,n=a; year,month=divmod(date.year*12+date.month-1+n,12);month+=1
        return dt.date(year,month,min(date.day,calendar.monthrange(year,month)[1]))
    if op=='following': return following(a[0])
    if op=='add_days': return a[0]+dt.timedelta(days=a[1])
    if op=='int_add': return a[0]+a[1]
    if op=='le_money': return a[0]<=a[1]
    if op=='if_money': return a[1] if a[0] else a[2]
    if op=='state_credit': return Balance(a[0].value+a[1],a[0].month)
    if op=='state_fee': return Balance(max(F(0),a[0].value-a[1]),a[0].month)
    if op=='state_management': return Balance(max(F(0),a[0].value-rounded(a[0].value*a[1]/12,a[2])),a[0].month)
    if op=='state_grow': return Balance(rounded(a[0].value*a[1],a[2]),a[0].month+1)
    if op=='state_value': return a[0].value
    raise ValueError(op)

def evaluate(tree,args):
    args=[decode(x) for x in args]
    def go(t):
        if t['k']=='param': return args[t['i']]
        if t['k']=='lit': return decode(t['value'])
        return apply(t['op'],[go(c) for c in t['args']])
    return go(tree)
