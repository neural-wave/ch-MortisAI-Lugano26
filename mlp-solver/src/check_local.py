"""Feature invariance, training-only forcing and independent arithmetic checks."""
import json,random,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from domain import domain as d
from features import Context
from search import solve
from base_features import features as old_features
import corpus,oracle

def main():
    tasks=json.loads((Path(__file__).parent/'seed_corpus/validation.json').read_text())
    checked=groups=0;profiles=[]
    for family in ('money','calendar','state'):
        t=next(t for t in tasks if t['family']==family)
        xs=[tuple(d.decode(v) for v in e['args']) for e in t['examples']];ys=tuple(d.decode(e['y']) for e in t['examples'])
        cs=[SimpleNamespace(ast=n,values=tuple(d.eval_ast(n,x) for x in xs),type=d.infer_type(n,t['input_types']),size=d.tree_size(n)) for n in corpus.walk(t['ast'])]
        context=Context(ys,t['output_type'],t['input_types'],xs);a=context.batch(cs)
        b=np.concatenate([context.batch([c]) for c in cs]);assert np.allclose(a,b,atol=1e-6)
        perm=list(reversed(range(len(xs))));rev=Context(tuple(ys[i] for i in perm),t['output_type'],t['input_types'],[xs[i] for i in perm])
        cr=[SimpleNamespace(ast=c.ast,values=tuple(c.values[i] for i in perm),type=c.type,size=c.size) for c in cs]
        assert np.allclose(a,rev.batch(cr),atol=1e-6),'Order dependence'
        original=[3*f[37]-f[38]+.2*f[42]-.03*f[30] for f in [old_features(c.ast,c.values,ys,c.type,t['output_type']) for c in cs]]
        assert np.allclose(original,context.heuristic(cs),atol=1e-7),'Heuristic ranking changed'
        tick=time.perf_counter();context.batch((cs*100)[:512]);profiles.append((time.perf_counter()-tick)*1000)
        public={k:v for k,v in t.items() if k not in ('ast','template_key')};events=[]
        def observe(items,labels,ctx,kind,size):
            assert all(c.type==kind and c.size==size for c in items)
            assert any(labels) and not all(labels)
            assert np.isfinite(ctx.batch(items)).all();events.append(len(items))
        solve(public,{'mode':'heuristic','time_ms':500,'max_size':9},teacher=t['ast'],on_group=observe)
        groups+=len(events)
        result=solve(public,{'mode':'heuristic','time_ms':100,'max_size':9})
        if result['ast']:
            assert all(d.eval_ast(result['ast'],x)==y for x,y in zip(xs,ys))
        for i in range(20):
            args=corpus.private_sample(family,random.Random(i),i)
            assert oracle.canonical(d.eval_ast(t['ast'],args))==oracle.canonical(oracle.evaluate(t['ast'],args));checked+=1
    assert groups>0
    print(json.dumps({'status':'passed','oracle_checks':checked,'matched_training_groups':groups,
        'batch_single_equivalence':True,'example_permutation_invariant':True,
        'heuristic_matches_original_formula':True,'batch512_feature_ms':profiles},indent=2))

if __name__=='__main__':main()
