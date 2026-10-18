"""New template-disjoint tasks, boundary inputs and executable supervision."""
import datetime as dt
import hashlib
import json
import random
from decimal import Decimal as D
from pathlib import Path
from domain import domain as d
import oracle

FAMILIES={'money':(['money','money','date'],'money'),
          'calendar':(['date','int','int'],'date'),
          'state':(['state','money','money','date'],'state')}

def digest(text): return hashlib.sha256(text.encode()).hexdigest()

def sample(family,rng,index,future=False):
    edge=[dt.date(2007,8,10),dt.date(2007,8,11),dt.date(2024,2,29),dt.date(2025,1,31),
          dt.date(2026,4,3),dt.date(2026,4,6),dt.date(2026,12,25),dt.date(2006,12,31)]
    date=edge[index%8] if index<16 else dt.date((2040 if future else 1990)+rng.randrange(31),1,1)+dt.timedelta(days=rng.randrange(365))
    amounts=['0','.005','1.005','-1.005','12.345','999.99','-.005','12345.6789']
    a=D(amounts[index%8]) if index<16 else D(rng.randrange(-10000000,10000001))/10000
    b=D(['0','.01','.12','1','1.05','-.03','1.00005','.33333'][(index+index//8)%8]) if index<16 else D(rng.randrange(-20000,20001))/10000
    if family=='money': return [a,b,date]
    if family=='calendar': return [date,[-12,-3,0,1,2,6,12,24][index%8],rng.randrange(-12,25)]
    return [d.State(abs(a),rng.randrange(36)),abs(b)*10,D(['.001','.01','.12','1.01','2','0','-.01','1.0005'][index%8]),date]

def private_sample(family,rng,index):
    args=sample(family,rng,index+32,future=index>=128)
    if index<64:
        edge=[dt.date(2007,8,10),dt.date(2007,8,11),dt.date(2024,2,29),dt.date(2025,1,31),
              dt.date(2026,4,3),dt.date(2026,4,6),dt.date(2026,12,25),dt.date(2006,12,31)]
        args[0 if family=='calendar' else -1]=edge[index%8]
    return args

def semantic_fingerprint(tree,family):
    rng=random.Random(119003)
    probes=[private_sample(family,rng,i) for i in range(32)]
    return digest(family+repr([oracle.canonical(oracle.evaluate(tree,x)) for x in probes]))

def walk(t):
    yield t
    for c in t.get('args',[]): yield from walk(c)

def build(rng,types,out,budget):
    leaves={k:[d.P(i) for i,t in enumerate(types) if t==k]+[x for x in d.literal_bank() if x['type']==k]
            for k in ('money','date','int','bool','state')}
    available={k for k,v in leaves.items() if v}
    def go(kind,n):
        options=[(name,s) for name,s in d.PRIMITIVES.items() if s['output']==kind
                 and set(s['inputs'])<=available and len(s['inputs'])+1<=n]
        if not options or (leaves[kind] and rng.random()<.18): return rng.choice(leaves[kind])
        name,s=rng.choice(options); parts=[1]*len(s['inputs'])
        for _ in range(n-1-len(parts)): parts[rng.randrange(len(parts))]+=1
        return d.C(name,*(go(k,b) for k,b in zip(s['inputs'],parts)))
    return d.normalize(go(out,budget))

def generate(out,counts=(6000,750,180),seed=181026,exclude=(),exclude_semantics=()):
    out=Path(out);out.mkdir(exist_ok=False)
    pools={k:[] for k in ('train','validation','test')};seen=set(exclude);behaviors=set(exclude_semantics);rng=random.Random(seed)
    families=list(FAMILIES); attempts=0; oracle_checks=0
    while any(len(pools[s])<n for s,n in zip(pools,counts)):
        attempts+=1
        if attempts>2000000: raise RuntimeError('Not enough unique templates')
        family=families[attempts%3];types,typ=FAMILIES[family]
        try: ast=build(rng,types,typ,rng.choice([5,7,7,9,9]))
        except (ValueError,TypeError,ArithmeticError,IndexError): continue
        if d.tree_size(ast)<4 or sum(n['k']=='call' for n in walk(ast))<2: continue
        key=d.template_key(ast,types)
        if key in seen: continue
        bucket=int(digest(key)[:8],16)%100
        stage='train' if bucket<80 else 'validation' if bucket<90 else 'test'
        if len(pools[stage])>=counts[list(pools).index(stage)]: continue
        identifier=f'{stage}-{family}-{len(pools[stage]):05d}'
        rr=random.Random(int(digest(str(seed)+identifier),16)); rows=[]
        try:
            for i in range(24):
                args=sample(family,rr,i);value=d.eval_ast(ast,args)
                if oracle.canonical(value)!=oracle.canonical(oracle.evaluate(ast,args)):
                    raise AssertionError('Independent generation oracle disagreement')
                oracle_checks+=1
                rows.append({'args':[d.encode(x) for x in args],'y':d.encode(value)})
        except (ValueError,TypeError,ArithmeticError,IndexError): continue
        if len({json.dumps(e['y'],sort_keys=True) for e in rows})<3: continue
        behavior=semantic_fingerprint(ast,family)
        if behavior in behaviors:
            seen.add(key);continue
        seen.add(key);behaviors.add(behavior)
        pools[stage].append({'id':identifier,'family':family,'input_types':types,'output_type':typ,
                             'ast':ast,'template_key':key,'max_size':9,'examples':rows})
        total=sum(map(len,pools.values()))
        if total%500==0:
            print(json.dumps({'stage':'generate','tasks':total,'attempts':attempts}),flush=True)
    keys={s:{t['template_key'] for t in ts} for s,ts in pools.items()}
    assert not(keys['train']&keys['test'] or keys['validation']&keys['test'] or keys['train']&keys['validation'])
    for stage,tasks in pools.items():
        (out/(stage+'.json')).write_text(json.dumps(tasks,separators=(',',':')))
        if stage=='test':
            public=[{k:v for k,v in t.items() if k not in ('ast','template_key')} for t in tasks]
            (out/'test_public.json').write_text(json.dumps(public,separators=(',',':')))
    manifest={'seed':seed,'counts':{s:len(v) for s,v in pools.items()},'attempts':attempts,
              'examplesPerTask':24,'maximumAstNodes':9,'templateOverlap':0,
              'excludedPreviousTrainingTemplates':len(exclude),'excludedPreviousBehaviorFingerprints':len(exclude_semantics),
              'sampledBehaviorFingerprintsDisjoint':True,'fingerprintProbeInputs':32,
              'fingerprintLimit':'Sampled semantic deduplication, not a proof of functional equivalence',
              'independentOracleChecks':oracle_checks,
              'testUse':'sealed until all checkpoints frozen','officialFinancialDataUsed':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest
