"""Validation search selection followed by a freshly generated excluded test."""
import argparse,datetime,json,random,time
from pathlib import Path
from evaluation_base import run_search,verify_formulas,sha,save
from corpus import generate

def public(tasks):return [{k:v for k,v in t.items() if k not in ('ast','template_key')} for t in tasks]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--test-tasks',type=int,default=120);ap.add_argument('--test-ms',type=int,default=1000)
    ap.add_argument('--validation-per-family',type=int,default=20);ap.add_argument('--validation-ms',type=int,default=750)
    ap.add_argument('--long-tasks',type=int,default=30);ap.add_argument('--long-ms',type=int,default=3000)
    a=ap.parse_args()
    if min(a.test_tasks,a.test_ms,a.validation_per_family,a.validation_ms,a.long_ms)<1 or a.long_tasks<0:ap.error('Invalid positive counts or budgets')
    a.long_tasks=min(a.long_tasks,a.test_tasks)
    a.run=a.run.resolve();a.out=a.out.resolve()
    a.out.mkdir(parents=True,exist_ok=False);root=a.run;models=root/'models';started=time.monotonic()
    validation=json.loads((root/'corpus/validation.json').read_text());rng=random.Random(18105004)
    selected=[]
    for family in ('money','calendar','state'):
        pool=[t for t in validation if t['family']==family];selected+=rng.sample(pool,min(a.validation_per_family,len(pool)))
    if not selected:raise ValueError('No validation tasks')
    candidates={'heuristic':('heuristic',None),
        'round1_neural':('neural',models/'round1/best.npz'),
        'round1_hybrid16':('hybrid16',models/'round1/best.npz'),
        'round2_neural':('neural',models/'round2/best.npz'),
        'round2_hybrid16':('hybrid16',models/'round2/best.npz'),
        'round2_hybrid64':('hybrid64',models/'round2/best.npz'),
        'small':('neural',models/'small/best.npz')}
    save(a.out/'selection_protocol.json',{'tasks':[t['id'] for t in selected], 'milliseconds':a.validation_ms,
        'candidates':{k:[mode,str(path)] for k,(mode,path) in candidates.items()},
        'criterion':'Max oracle passes, then fewer false fits, then lower total wall time',
        'training_refresh_uses_train_only':True,'test_generated':False})
    preds={}
    for name,(mode,path) in candidates.items():preds[name],_=run_search(public(selected),mode,path,a.validation_ms,a.out,'validation_'+name)
    validation_report,_,_=verify_formulas(selected,preds,a.validation_ms);save(a.out/'validation_results.json',validation_report)
    order=lambda k:(-validation_report[k]['passes_256_new_inputs'],validation_report[k]['false_fits'],validation_report[k]['search_seconds'])
    recommendation=min(candidates,key=order)
    neural=min(('round1_neural','round2_neural'),key=order)
    hybrid=min(('round1_hybrid16','round2_hybrid16','round2_hybrid64'),key=order)
    modes={k:candidates[k] for k in ('heuristic',neural,hybrid,'small')}
    here=Path(__file__).parent
    frozen={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recommended':recommendation,
        'selected_neural':neural,'selected_hybrid':hybrid,'selection':'Validation search+256 independent oracle inputs',
        'models':{k:sha(path) for k,(_,path) in candidates.items() if path},
        'source_hashes':{str(p.relative_to(here)):sha(p) for p in sorted(here.rglob('*.py'))},
        'test_ms':a.test_ms,'test_tasks':a.test_tasks,'long_tasks':a.long_tasks,'long_ms':a.long_ms,'seed':18106099,
        'max_candidates':100000,'test_read':False}
    save(a.out/'frozen_before_test.json',frozen)
    old=json.loads((here/'prior_exclusions.json').read_text());new=json.loads((root/'corpus/exclusions.json').read_text())
    generate(a.out/'sealed_test',counts=(0,0,a.test_tasks),seed=frozen['seed'],
        exclude=set(old['templates'])|set(new['templates']),
        exclude_semantics=set(old['sampled_semantics'])|set(new['sampled_semantics']))
    tasks=json.loads((a.out/'sealed_test/test_public.json').read_text());preds={};long={}
    for name,(mode,path) in modes.items():preds[name],_=run_search(tasks,mode,path,a.test_ms,a.out,name)
    for name in reversed(modes):
        if a.long_tasks:
            mode,path=modes[name];long[name],_=run_search(tasks[:a.long_tasks],mode,path,a.long_ms,a.out,'long_'+name)
    save(a.out/'predictions_frozen.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'hashes':{p.name:sha(p) for p in a.out.glob('*.jsonl') if not p.name.startswith('validation')}})
    for k,expected in frozen['source_hashes'].items():assert sha(here/k)==expected
    for k,expected in frozen['models'].items():assert sha(candidates[k][1])==expected
    private=json.loads((a.out/'sealed_test/test.json').read_text())
    report,passed,checks=verify_formulas(private,preds,a.test_ms);lr,lp,lc=verify_formulas(private[:a.long_tasks],long,a.long_ms)
    paired={};rng=random.Random(811567)
    for name in report:
        if name=='heuristic':continue
        diff=[int(x)-int(y) for x,y in zip(passed[name],passed['heuristic'])]
        boot=sorted(sum(rng.choice(diff) for _ in diff)/len(diff) for _ in range(3000))
        paired[name]={'wins':diff.count(1),'losses':diff.count(-1),'difference_pp':100*sum(diff)/len(diff),
                      'bootstrap95_pp':[100*boot[75],100*boot[2924]]}
    result={'status':'complete','seconds':time.monotonic()-started,'validation_recommendation':recommendation,
        'modes':report,'long_budget_modes':lr,'passed_by_task':passed,'long_passed_by_task':lp,
        'paired_vs_heuristic':paired,'oracle_checks':checks+lc,'runtime_llm_calls':0,
        'scope':'Supplied DSL compositions; not t0-t7 accuracy or proof of universal recovery',
        'test_generated_after_selection':True,'model_source_hashes_unchanged':True}
    save(a.out/'results.json',result);print('BENCHMARK_COMPLETE '+json.dumps(result),flush=True)

if __name__=='__main__':main()
