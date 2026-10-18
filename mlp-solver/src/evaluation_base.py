"""Freeze checkpoints, generate excluded test tasks, time CPU search, then oracle-check."""
import argparse,collections,datetime,hashlib,json,os,random,subprocess,sys,time
from pathlib import Path
from corpus import generate,digest,private_sample
import oracle

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2)+'\n')


def exclusions(data):
    paths=[data/'corpus/exclusions.json',HERE/'prior_exclusions.json'];templates=set();semantics=set()
    for path in paths:
        if not path.exists():raise FileNotFoundError('Missing exclusion registry: '+str(path))
        content=json.loads(path.read_text());templates.update(content['templates']);semantics.update(content['sampled_semantics'])
    return templates,semantics


def run_search(tasks,kind,model,ms,out,label):
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,'-B',str(HERE/'worker.py'),'--mode',kind,'--ms',str(ms)]
    if model:command+=['--model',str(model)]
    start=time.monotonic();rows=[]
    with (out/(label+'.stderr.log')).open('w') as errors:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,env=env)
        try:
            with(out/(label+'.jsonl')).open('w') as stream:
                for index,task in enumerate(tasks):
                    if 'ast' in task or 'template_key' in task:raise ValueError('Teacher supplied to search')
                    process.stdin.write(json.dumps(task)+'\n');process.stdin.flush();line=process.stdout.readline()
                    if not line:raise RuntimeError('Worker stopped: '+label)
                    result=json.loads(line);rows.append(result);stream.write(line);stream.flush()
                    if (index+1)%20==0:print(json.dumps({'phase':'cpu_search','mode':label,'tasks':index+1,'total':len(tasks)}),flush=True)
            process.stdin.close()
            if process.wait(timeout=30):raise RuntimeError('Search worker failed')
        finally:
            if process.poll() is None:process.terminate();process.wait(timeout=10)
    return rows,time.monotonic()-start


def verify_formulas(private,predictions,budget_ms=1000):
    checks=0;passed={};reports={}
    for mode,rows in predictions.items():
        results=[];falsefits=0;families=collections.defaultdict(lambda:{'tasks':0,'passed':0})
        for task,result in zip(private,rows):
            good=result['status']=='fit'
            if good:
                rng=random.Random(int(digest('new-private-256:'+task['id']),16))
                used={tuple(oracle.canonical(v) for v in e['args']) for e in task['examples']}
                for index in range(256):
                    while True:
                        args=private_sample(task['family'],rng,index)
                        key=tuple(oracle.canonical(v) for v in args)
                        if key not in used:break
                    used.add(key);checks+=1
                    try:
                        if oracle.canonical(oracle.evaluate(result['ast'],args))!=oracle.canonical(oracle.evaluate(task['ast'],args)):
                            good=False;break
                    except (ValueError,TypeError,ArithmeticError,OverflowError):good=False;break
                if not good:falsefits+=1
            results.append(bool(good));families[task['family']]['tasks']+=1;families[task['family']]['passed']+=bool(good)
        passed[mode]=results
        reports[mode]={'tasks':len(rows),'fits_public_examples':sum(r['status']=='fit' for r in rows),
                       'passes_256_new_inputs':sum(results),'false_fits':falsefits,'family':dict(families),
                       'search_seconds':sum(r['wall_ms'] for r in rows)/1000,
                       'feature_ms':sum(r['feature_ms'] for r in rows),'inference_ms':sum(r['inference_ms'] for r in rows),
                       'budget_overrun_tasks':sum(r['wall_ms']>budget_ms*1.05 for r in rows)}
    return reports,passed,checks


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--models',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--tasks',type=int,default=120);ap.add_argument('--time-ms',type=int,default=1000)
    ap.add_argument('--long-tasks',type=int,default=30);ap.add_argument('--seed',type=int,default=38109143)
    a=ap.parse_args();a.data=a.data.resolve();a.models=a.models.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
    model_manifest=json.loads((a.models/'manifest.json').read_text())
    if model_manifest['status']!='checkpoints_frozen':raise ValueError('Training must finish and freeze models before evaluation')
    models={name:(a.models/relative).resolve() for name,relative in model_manifest['models'].items()}
    for name,path in models.items():
        if sha(path)!=model_manifest['sha256'][name]:raise ValueError('Checkpoint drift before freeze')
    # No test generated or opened until the policies, code and model hashes freeze.
    modes={'heuristic':('heuristic',None),'mlp10m':('neural',models['mlp10m']),
           'hybrid10m':('hybrid',models['mlp10m']),'small_control':('neural',models['small_control'])}
    frozen={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'model_hashes':{name:sha(path) for name,path in models.items()},
            'source_hashes':{str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*.py')) if '__pycache__' not in p.parts},
            'policies':{'fifo_fraction':.2,'beam':32,'hybrid_heuristic_reserve':12,'hybrid_neural_shortlist':64,
                        'leaf_ranking':'heuristic; call-only matched supervision'},
            'checkpoint_selection':model_manifest['selection'],'mode_selection_on_test':False,
            'budget_ms':a.time_ms,'long_budget_ms':3000,'long_subset':a.long_tasks,'test_tasks':a.tasks,'seed':a.seed}
    save(a.out/'frozen_before_test.json',frozen)
    exclude,semantic=exclusions(a.data)
    generate(a.out/'sealed_test',counts=(0,0,a.tasks),seed=a.seed,exclude=exclude,exclude_semantics=semantic)
    public=json.loads((a.out/'sealed_test/test_public.json').read_text())
    predictions={};timings={}
    # Balanced, declared rotation of mode order for the second budget.
    for name,(kind,model) in modes.items():
        predictions[name],timings[name]=run_search(public,kind,model,a.time_ms,a.out,name)
    long_predictions={};long_timings={}
    for name in reversed(modes):
        kind,model=modes[name]
        if a.long_tasks:
            long_predictions[name],long_timings[name]=run_search(public[:a.long_tasks],kind,model,3000,a.out,'long_'+name)
    # Teachers and fresh oracle answers are read only after ALL predictions freeze.
    for name,path in models.items():assert sha(path)==frozen['model_hashes'][name]
    for relative,expected in frozen['source_hashes'].items():assert sha(HERE/relative)==expected
    save(a.out/'predictions_frozen.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'sha256':{p.name:sha(p) for p in sorted(a.out.glob('*.jsonl'))}})
    private=json.loads((a.out/'sealed_test/test.json').read_text());assert [t['id'] for t in private]==[t['id'] for t in public]
    report,passed,checks=verify_formulas(private,predictions,a.time_ms)
    long_report,long_passed,long_checks=verify_formulas(private[:a.long_tasks],long_predictions,3000)
    for name in report:report[name]['seconds_with_model_load']=timings[name]
    for name in long_report:long_report[name]['seconds_with_model_load']=long_timings[name]
    paired={};rng=random.Random(5178003)
    for name in ('mlp10m','hybrid10m','small_control'):
        differences=[int(x)-int(y) for x,y in zip(passed[name],passed['heuristic'])]
        boot=sorted(sum(rng.choice(differences) for _ in differences)/len(differences) for _ in range(3000))
        paired[name]={'wins':sum(x==1 for x in differences),'losses':sum(x==-1 for x in differences),
                      'difference_pp':100*sum(differences)/len(differences),
                      'paired_bootstrap95_pp':[100*boot[75],100*boot[2924]]}
    result={'status':'complete','modes':report,'long_budget_modes':long_report,'paired_vs_heuristic':paired,
            'passed_by_task':passed,'long_passed_by_task':long_passed,'independent_oracle_checks':checks+long_checks,
            'checkpoint_and_source_integrity':True,'cpu_search':True,'runtime_llm_calls':0,
            'official_lifeware_data_used':False,'test_generated_after_checkpoint_freeze':True,
            'scope':'New AST compositions of supplied typed primitives; not full Lifeware formula recovery',
            'accuracy_meaning':'Exact on public examples and256 fresh Fraction-oracle inputs, not proof for every input',
            'recommendation':'Compare recovery and CPU cost; do not replace a stronger heuristic automatically'}
    save(a.out/'results.json',result)
    print('EVALUATION_COMPLETE '+json.dumps({k:v for k,v in result.items() if 'by_task' not in k}),flush=True)


if __name__=='__main__':main()
