"""Small typed synthetic domain reusing exact, read-only friend functions.

This is a supplied-primitive composition experiment, not recovery of t0-t6.
"""
import ast as python_ast
import datetime as dt
import functools
import hashlib
import itertools
import json
from dataclasses import dataclass
from decimal import Decimal, localcontext, ROUND_DOWN, ROUND_HALF_UP
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'friend_primitives'
DECIMAL_PRECISION = 50
PROVENANCE = {}

def _foreign(filename, functions, environment, constants=()):
    """Execute original selected function ASTs unchanged, not hand transcriptions.

    Imports/data I/O from the original runtime are intentionally not executed.
    Every file used, including transitive primitives, is hashed.
    """
    path = SOURCE / filename
    source = path.read_bytes()
    PROVENANCE[str(path.relative_to(ROOT))] = hashlib.sha256(source).hexdigest()
    parsed = python_ast.parse(source, filename=str(path))
    body = [node for node in parsed.body if
            isinstance(node, (python_ast.FunctionDef, python_ast.AsyncFunctionDef)) and node.name in functions or
            isinstance(node, python_ast.Assign) and any(isinstance(t, python_ast.Name) and t.id in constants for t in node.targets)]
    present = {n.name for n in body if isinstance(n, python_ast.FunctionDef)}
    if present != set(functions):
        raise ValueError('Original function missing: ' + filename)
    scope = dict(environment)
    exec(compile(python_ast.Module(body=body, type_ignores=[]), str(path), 'exec'), scope)
    return scope

_base = {'dt': dt, 'D': Decimal, 'cache': functools.cache}
_easter = _foreign('dates_easter.py', ['easter'], _base)['easter']
_hol = _foreign('dates_holidays.py', ['holidays', 'following'], dict(_base, easter=_easter), ['FIXED_HOLIDAYS', 'EASTER_HOLIDAYS'])
_months = _foreign('dates.py', ['add_months'], dict(_base, calendar=__import__('calendar')))['add_months']
_round = _foreign('eras.py', ['rounded'], dict(_base, CENT=Decimal('.01'), ROUND_DOWN=ROUND_DOWN, ROUND_HALF_UP=ROUND_HALF_UP), ['CONVERSION'])['rounded']
_scaled = _foreign('tables_numbers.py', ['scaled'], _base)['scaled']
_deduct = _foreign('projection_month.py', ['deduct'], _base)['deduct']
_management = _foreign('projection_charges.py', ['management_charge'], dict(_base, scaled=_scaled, rounded=_round))['management_charge']

@dataclass(frozen=True)
class State:
    value: Decimal
    month: int

def encode(value):
    if isinstance(value, bool) or isinstance(value, int): return value
    if isinstance(value, Decimal): return {'decimal': str(value)}
    if isinstance(value, dt.date): return {'date': value.isoformat()}
    if isinstance(value, State): return {'state': {'value': str(value.value), 'month': value.month}}
    raise TypeError('Unsupported domain value')

def decode(value):
    if isinstance(value, (Decimal, dt.date, State, bool, int)): return value
    if isinstance(value, dict) and set(value) == {'decimal'}: return Decimal(value['decimal'])
    if isinstance(value, dict) and set(value) == {'date'}: return dt.date.fromisoformat(value['date'])
    if isinstance(value, dict) and set(value) == {'state'}:
        return State(Decimal(value['state']['value']), int(value['state']['month']))
    raise TypeError('Invalid encoded domain value')

def value_type(value):
    value = decode(value)
    if isinstance(value, bool): return 'bool'
    if isinstance(value, int): return 'int'
    if isinstance(value, Decimal):
        if not value.is_finite(): raise ValueError('Finite Decimal required')
        return 'money'
    if isinstance(value, dt.date): return 'date'
    if isinstance(value, State):
        if not value.value.is_finite() or not isinstance(value.month, int): raise ValueError('Invalid State')
        return 'state'
    raise TypeError('Unknown domain type')

def _amc(value, rate, when):
    terms = SimpleNamespace(charges={'CG_AMCP2': str(rate * Decimal(1000000))}, applied=when)
    return _management(value, terms)

PRIMITIVES = {}
def _register(name, inputs, output, function, source):
    PRIMITIVES[name] = {'inputs': tuple(inputs), 'output': output, 'function': function, 'source': source}

_register('add', ['money','money'], 'money', lambda a,b:a+b, 'Decimal exact addition under context50')
_register('sub', ['money','money'], 'money', lambda a,b:a-b, 'Decimal subtraction under context50')
_register('mul', ['money','money'], 'money', lambda a,b:a*b, 'Numeric multiplication; money also represents a dimensionless rate/factor')
_register('rounded', ['money','date'], 'money', _round, 'friend eras.rounded; truncate before2007-08-11, halfupafter')
_register('deduct', ['money','money'], 'money', _deduct, 'friend projection_month.deduct')
_register('management', ['money','money','date'], 'money', _amc, 'friend projection_charges.management_charge; supplied annualrate')
_register('add_months', ['date','int'], 'date', _months, 'friend dates.add_months; clamped month-end')
_register('following', ['date'], 'date', _hol['following'], 'friend dates_holidays.following; Ticino calendar1900-2199')
_register('add_days', ['date','int'], 'date', lambda d,n:d+dt.timedelta(days=n), 'datetime.timedelta exact days')
_register('int_add', ['int','int'], 'int', lambda a,b:a+b, 'integer addition')
_register('le_money', ['money','money'], 'bool', lambda a,b:a<=b, 'Decimal comparison')
_register('if_money', ['bool','money','money'], 'money', lambda c,a,b:a if c else b, 'pure typed conditional')
_register('state_credit', ['state','money'], 'state', lambda s,p:State(s.value+p,s.month), 'generic credit; supplied incomingpremium')
_register('state_fee', ['state','money'], 'state', lambda s,c:State(_deduct(s.value,c),s.month), 'friend deduct on state balance')
_register('state_management', ['state','money','date'], 'state', lambda s,r,d:State(_deduct(s.value,_amc(s.value,r,d)),s.month), 'friend management_charge then friend deduct')
_register('state_grow', ['state','money','date'], 'state', lambda s,g,d:State(_round(s.value*g,d),s.month+1), 'friend rounded on growth; explicit month+1 transition')
_register('state_value', ['state'], 'money', lambda s:s.value, 'explicit balance projection; not a hidden answer')

def primitive_signatures():
    return {name:{k:v for k,v in spec.items() if k!='function'} for name,spec in PRIMITIVES.items()}

def eval_primitive(name, args):
    spec = PRIMITIVES[name]
    args = [decode(a) for a in args]
    if tuple(value_type(a) for a in args) != spec['inputs']:
        raise TypeError('Primitive type mismatch: ' + name)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        result = spec['function'](*args)
    if value_type(result) != spec['output']: raise TypeError('Primitive returned wrong type')
    return result

def P(i): return {'k':'param','i':i}
def C(name, *args): return {'k':'call','op':name,'args':list(args)}
def L(type_name, value): return {'k':'lit','type':type_name,'value':encode(value)}
def tree_size(node): return 1 + sum(tree_size(c) for c in node.get('args', []))

def literal_bank():
    """Global, train-independent constants. Never derived from task answers."""
    return ([L('money',Decimal(x)) for x in ['0','1','0.01','0.05','0.12','1.01']]
            +[L('int',n) for n in [1,2,3,6,12]]+[L('bool',False),L('bool',True)])

def infer_type(node, input_types):
    kind = node.get('k')
    if kind == 'param':
        if isinstance(node['i'], bool) or not isinstance(node['i'],int) or not 0<=node['i']<len(input_types): raise TypeError('Invalid parameter')
        return input_types[node['i']]
    if kind == 'lit':
        if value_type(node['value']) != node['type']: raise TypeError('Literal type mismatch')
        return node['type']
    if kind != 'call' or node.get('op') not in PRIMITIVES: raise TypeError('Invalid AST operation')
    spec = PRIMITIVES[node['op']]
    if tuple(infer_type(c,input_types) for c in node['args']) != spec['inputs']: raise TypeError('AST signature mismatch')
    return spec['output']

def eval_ast(node, args):
    args = [decode(a) for a in args]
    infer_type(node, [value_type(a) for a in args])
    if tree_size(node)>100: raise ValueError('AST evaluation bound')
    def go(t):
        if t['k']=='param': return args[t['i']]
        if t['k']=='lit': return decode(t['value'])
        # Both branches are pure and total on generated inputs; no side effects.
        return eval_primitive(t['op'],[go(c) for c in t['args']])
    return go(node)

def _normalize_once(node):
    if node['k']!='call': return dict(node)
    name=node['op']; a=[normalize(c) for c in node['args']]
    if all(t['k']=='lit' for t in a):
        result=eval_primitive(name,[decode(t['value']) for t in a])
        return L(value_type(result),result)
    if name=='if_money' and a[0]['k']=='lit': return a[1] if decode(a[0]['value']) else a[2]
    def literal(t,value): return t['k']=='lit' and t.get('type')=='money' and decode(t['value'])==Decimal(value)
    if name in ('add','mul'):
        # Flatten only exact Decimal +/* in this bounded low-magnitude corpus.
        flat=[]
        def collect(child):
            if child.get('k')=='call' and child.get('op')==name:
                for sub in child['args']:collect(sub)
            else:flat.append(child)
        for child in a:collect(child)
        flat.sort(key=lambda t:json.dumps(t,sort_keys=True,separators=(',',':')))
        # Canonical binary tree keeps the interpreter's arity unchanged.
        out=flat[0]
        for child in flat[1:]: out=C(name,out,child)
        a=out['args']
    if name=='add':
        if literal(a[0],0): return a[1]
        if literal(a[1],0): return a[0]
    if name=='sub':
        if literal(a[1],0): return a[0]
        if a[0]==a[1]: return L('money',Decimal(0))
    if name=='mul':
        if literal(a[0],0) or literal(a[1],0): return L('money',Decimal(0))
        if literal(a[0],1): return a[1]
        if literal(a[1],1): return a[0]
    if name=='following' and a[0].get('op')=='following': return a[0]
    if name in ('add_days','add_months') and a[1]['k']=='lit' and decode(a[1]['value'])==0: return a[0]
    if name=='state_credit' and literal(a[1],0): return a[0]
    if name=='rounded' and a[0].get('op')=='rounded': return a[0]
    if name=='if_money' and a[1]==a[2]: return a[1]
    return C(name,*a)

def normalize(node):
    """Canonical fixed point; saved AST and split key see the SAME normal form."""
    current=node
    for _ in range(100):
        updated=_normalize_once(current)
        if updated==current:return updated
        current=updated
    raise ValueError('Normalization failed to reach a fixed point')

def template_key(node, input_types):
    """Ignore literal values, global same-type input renaming and +/* ordering.

    Skeleton classes, not task IDs/seeds/constant variations, determine split.
    """
    node=normalize(node)
    groups={t:[i for i,v in enumerate(input_types) if v==t] for t in set(input_types)}
    maps=[{}]
    for ids in groups.values():
        maps=[dict(m,**{})|dict(zip(ids,p)) for m in maps for p in itertools.permutations(range(len(ids)))]
    def encode_node(t,m):
        if t['k']=='param': return ['p',input_types[t['i']],m[t['i']]]
        if t['k']=='lit': return ['literal',t['type']]
        name=t['op']; a=[encode_node(c,m) for c in t['args']]
        if name in ('add','mul'):
            flat=[]
            for child in a: flat.extend(child[1:] if child[0]==name else [child])
            a=sorted(flat,key=lambda x:json.dumps(x,separators=(',',':')))
        return [name,*a]
    return min(json.dumps([sorted(input_types),encode_node(node,m)],sort_keys=True,separators=(',',':')) for m in maps)

def bounded_search(examples,input_types,output_type,max_size=7,max_candidates=10000):
    """Small reference enumerator; no MLP, test files, or external answers."""
    import time
    started=time.monotonic(); pools={};seen={};tested=0
    ys=[decode(e['y']) for e in examples];xs=[[decode(a) for a in e['args']] for e in examples]
    def accept(node,size):
        nonlocal tested
        tested+=1;typ=infer_type(node,input_types);vs=[eval_ast(node,x) for x in xs]
        if typ==output_type and vs==ys:return {'status':'fit-consistent','ast':node,'tested':tested,'seconds':time.monotonic()-started}
        key=(typ,json.dumps([encode(v) for v in vs],sort_keys=True))
        if key not in seen:seen[key]=node;pools.setdefault((size,typ),[]).append(node)
    for size in range(1,max_size+1):
        if size==1:
            leaves=[P(i) for i in range(len(input_types))]+[L('money',Decimal(0)),L('money',Decimal(1)),L('int',1),L('int',12)]
            for node in leaves:
                result=accept(node,size)
                if result:return result
        else:
            for name,spec in PRIMITIVES.items():
                arity=len(spec['inputs'])
                for partition in itertools.product(range(1,size),repeat=arity):
                    if sum(partition)+1!=size:continue
                    for args in itertools.product(*(pools.get((n,t),[]) for n,t in zip(partition,spec['inputs']))):
                        if tested>=max_candidates:return {'status':'candidate-limit','tested':tested,'seconds':time.monotonic()-started}
                        result=accept(C(name,*args),size)
                        if result:return result
    return {'status':'bound-exhausted','tested':tested,'seconds':time.monotonic()-started}
