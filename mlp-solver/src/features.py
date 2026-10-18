"""Batched semantic property signatures; immutable I/O context computed once.

256 documented features: structure32, value16, target relation32,
four input relations128, task context48. No IDs, teacher or private probes.
"""
import calendar
import datetime as dt
import math
import numpy as np
from base_features import scalar, structure, squash

KINDS=('money','date','int','state','bool','other')
OPS=('param','lit','add','sub','mul','rounded','deduct','management',
     'add_months','following','add_days','int_add','le_money','if_money',
     'state_credit','state_fee','state_management','state_grow','state_value')
STAT_NAMES=('mean','std','min','max','range','zero','positive','negative',
            'integer','cent','unique','abs_mean','median_abs','abs_max','weekday','month_end')
PAIR_NAMES=('eq','lt','le','sign','relative_abs','relative_rms','relative_max','bias',
            'correlation','abs_correlation','affine_abs','affine_rms','std_ratio','range_ratio',
            'difference_mean','difference_std','ratio_mean','ratio_std','zero_equal','integer_delta',
            'cent_delta','same_year','same_month','same_day','same_weekday','month_end_equal',
            'clock_equal','clock_difference','compatible_type','shift_constant','scale_constant','nonzero_target')
NAMES=([f'type_{k}' for k in KINDS]+[f'root_{op}' for op in OPS]+
       ['size','depth','params','literals','unary','multi','input_count']+
       [f'value_{n}' for n in STAT_NAMES]+[f'target_{n}' for n in PAIR_NAMES]+
       [f'input_{i}_{n}' for i in range(4) for n in PAIR_NAMES]+
       [f'task_output_{n}' for n in STAT_NAMES]+
       [f'task_input_{i}_{n}' for i in range(4) for n in STAT_NAMES[:8]])
assert len(NAMES)==256

def log(x):
    z=np.log1p(np.abs(x)); return np.sign(x)*z/(1+z)

class Vector:
    def __init__(self, values, kind):
        self.kind=kind;self.values=values
        self.x=np.asarray([scalar(v) for v in values],dtype=np.float64)
        self.center=self.x-self.x.mean(); self.std=float(np.std(self.x))
        self.range=float(np.ptp(self.x));self.mean=float(self.x.mean())
        neutral=np.full(len(values),-1)
        if kind=='date':
            self.year=np.asarray([v.year for v in values]);self.month=np.asarray([v.month for v in values])
            self.day=np.asarray([v.day for v in values]);self.weekday=np.asarray([v.weekday() for v in values])
            self.end=np.asarray([v.day==calendar.monthrange(v.year,v.month)[1] for v in values])
        else:
            self.year=self.month=self.day=self.weekday=neutral;self.end=np.zeros(len(values),bool)
        self.clock=np.asarray([v.month for v in values]) if kind=='state' else neutral

def stats(v):
    x=v.x; a=np.abs(x)
    return np.asarray([log(v.mean),log(v.std),log(x.min()),log(x.max()),log(v.range),
        np.mean(x==0),np.mean(x>0),np.mean(x<0),np.mean(np.abs(x-np.rint(x))<1e-8),
        np.mean(np.abs(x*100-np.rint(x*100))<1e-6),len(set(x))/len(x),log(a.mean()),
        log(np.median(a)),log(a.max()),np.mean(v.weekday/6) if v.kind=='date' else 0,
        np.mean(v.end)],dtype=np.float32)

def batch_stats(vectors):
    x=np.stack([v.x for v in vectors]);a=np.abs(x)
    return np.stack([log(x.mean(1)),log(x.std(1)),log(x.min(1)),log(x.max(1)),log(np.ptp(x,axis=1)),
        (x==0).mean(1),(x>0).mean(1),(x<0).mean(1),(np.abs(x-np.rint(x))<1e-8).mean(1),
        (np.abs(x*100-np.rint(x*100))<1e-6).mean(1),
        np.asarray([len(set(v.x))/len(v.x) for v in vectors]),log(a.mean(1)),log(np.median(a,axis=1)),
        log(a.max(1)),np.asarray([np.mean(v.weekday/6) if v.kind=='date' else 0 for v in vectors]),
        np.asarray([np.mean(v.end) for v in vectors])],axis=1)

class Context:
    def __init__(self, targets, output_type, input_types=(), xs=()):
        self.y=Vector(targets,output_type);self.output_type=output_type
        self.inputs=[Vector([x[i] for x in xs],t) for i,t in enumerate(input_types)]
        # Absent columns have explicit neutral representations and type=other.
        self.missing=Vector([0]*len(targets),'other')
        self.fixed=np.r_[stats(self.y),*[stats(self.inputs[i])[:8] if i<len(self.inputs)
                       else stats(self.missing)[:8] for i in range(4)]]

    def relation(self, vectors, target):
        x=np.stack([v.x for v in vectors]);y=target.x[None,:]
        delta=x-y;rel=delta/(1+np.abs(y));xc=x-x.mean(1,keepdims=True)
        sx=x.std(1);sy=target.std;cov=(xc*target.center).mean(1)
        corr=np.divide(cov,sx*sy,out=np.zeros_like(sx),where=sx*sy>0)
        slope=np.divide(cov,sx*sx,out=np.zeros_like(sx),where=sx>0)
        affine=(target.mean+slope[:,None]*xc-y)/(1+np.abs(y))
        ratio=np.divide(x,y,out=np.zeros_like(x),where=y!=0)
        compatible=np.asarray([v.kind==target.kind for v in vectors])
        date=compatible & (target.kind=='date');state=compatible & (target.kind=='state')
        eq=np.asarray([sum(a==b for a,b in zip(v.values,target.values))/len(v.values)
                       if c else 0 for v,c in zip(vectors,compatible)])
        prop=lambda name:np.stack([getattr(v,name) for v in vectors])
        return np.stack([eq,(x<y).mean(1),(x<=y).mean(1),(np.sign(x)==np.sign(y)).mean(1),
            log(np.abs(rel).mean(1)),log(np.sqrt((rel*rel).mean(1))),log(np.abs(rel).max(1)),
            log(rel.mean(1)),np.clip(corr,-1,1),np.abs(np.clip(corr,-1,1)),
            log(np.abs(affine).mean(1)),log(np.sqrt((affine*affine).mean(1))),
            log(np.log1p(sx)-math.log1p(sy)),log(np.log1p(np.ptp(x,axis=1))-math.log1p(target.range)),
            log(delta.mean(1)),log(delta.std(1)),log(ratio.mean(1)),log(ratio.std(1)),
            ((x==0)==(y==0)).mean(1),(np.abs(delta-np.rint(delta))<1e-8).mean(1),
            (np.abs(delta*100-np.rint(delta*100))<1e-6).mean(1),
            date*(prop('year')==target.year).mean(1),date*(prop('month')==target.month).mean(1),
            date*(prop('day')==target.day).mean(1),date*(prop('weekday')==target.weekday).mean(1),
            date*(prop('end')==target.end).mean(1),state*(prop('clock')==target.clock).mean(1),
            state*log((prop('clock')-target.clock).mean(1)),compatible,
            (np.ptp(delta,axis=1)<1e-8),((ratio.std(1)<1e-8)&np.all(y!=0)),
            np.full(len(vectors),np.mean(y!=0))],axis=1)

    def batch(self, candidates):
        if not candidates:return np.empty((0,256),dtype=np.float32)
        vectors=[Vector(c.values,c.type) for c in candidates]
        rows=[]
        for c in candidates:
            total,depth,p,l,u,m=structure(c.ast);root=c.ast.get('op',c.ast['k'])
            rows.append([float(c.type==k) for k in KINDS]+[float(root==op) for op in OPS]+
                [total/10,depth/10,p/total,l/total,u/total,m/total,len(self.inputs)/4])
        result=np.concatenate([np.asarray(rows),batch_stats(vectors),
            self.relation(vectors,self.y),*[self.relation(vectors,self.inputs[i] if i<len(self.inputs)
            else self.missing) for i in range(4)],np.broadcast_to(self.fixed,(len(candidates),48))],axis=1)
        assert result.shape==(len(candidates),256) and np.isfinite(result).all()
        return result.astype(np.float32)

    def heuristic(self,candidates):
        # Same ranking formula as old heuristic, computed together with cached target statistics.
        if not candidates:return np.empty(0)
        x=np.asarray([[scalar(v) for v in c.values] for c in candidates]);y=self.y.x
        date=self.output_type=='date'
        origin=y.min() if date else 0
        shifts=np.asarray([origin if c.type=='date' else 0 for c in candidates])[:,None]
        x=x-shifts;yy=y[None,:]-shifts
        xn=x/np.maximum(1,np.abs(x).max(1))[:,None];yn=yy/np.maximum(1,np.abs(yy).max(1))[:,None]
        xc=xn-xn.mean(1,keepdims=True);yc=yn-yn.mean(1,keepdims=True)
        den=np.sqrt((xc*xc).mean(1)*(yc*yc).mean(1))
        corr=np.divide((xc*yc).mean(1),den,out=np.zeros(len(candidates)),where=den>0)
        errors=np.abs((x-yy)/(1+np.abs(yy))).mean(1);z=np.log1p(errors);mae=z/(1+z)
        exact=np.asarray([sum(a==b for a,b in zip(c.values,self.y.values))/len(c.values)
                          if c.type==self.output_type else 0 for c in candidates])
        sizes=np.log1p([c.size for c in candidates]);sizes=sizes/(1+sizes)
        return 3*exact-mae+.2*corr-.03*sizes

def features(ast,values,targets,candidate_type,output_type,input_types=(),xs=()):
    from types import SimpleNamespace
    return Context(targets,output_type,input_types,xs).batch([SimpleNamespace(ast=ast,values=values,type=candidate_type)])[0].tolist()
