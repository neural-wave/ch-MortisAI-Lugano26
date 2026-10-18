"""Two-round teacher-forced frontier imitation. Synthetic tasks only."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import argparse,collections,json,multiprocessing as mp,random,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import corpus,training_base
from search import solve
from inference import load
from training_base import save,sha,offline_worker

MODEL=None
def init_worker(path):
    global MODEL
    offline_worker();MODEL=load(path) if path else None

def collect(task):
    rng=random.Random(int(corpus.digest(task['template_key']+':v2-frontier'),16))
    public={k:v for k,v in task.items() if k not in ('ast','template_key')};groups=[]
    def callback(items,labels,context,kind,size):
        pos=[i for i,y in enumerate(labels) if y];neg=[i for i,y in enumerate(labels) if not y]
        hard=sorted(neg,key=lambda i:-items[i].priority)[:24]
        tail=[i for i in neg if i not in hard];chosen=pos+hard+rng.sample(tail,min(16,len(tail)))
        groups.append((context.batch([items[i] for i in chosen]),np.asarray([labels[i] for i in chosen],dtype=np.int8)))
    result=solve(public,{'mode':'hybrid' if MODEL else 'heuristic','time_ms':450,
        'max_candidates':12000,'max_size':9,'beam':32,'shortlist':16},MODEL,
        teacher=task['ast'],on_group=callback)
    return groups,result['max_size_reached'],result['tested']

def collect_data(pools,out,workers,model=None,refresh=False,refresh_limit=2000):
    out.mkdir();matrices=[];labels=[];groups=[];splits=[];taskids=[];coverage=collections.Counter();n=0
    started=time.monotonic();tasknumber=0
    for stage,tasks in pools.items():
        if refresh:
            tasks=tasks[:refresh_limit] if stage=='train' else []
        if not tasks:continue
        with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn'),
                                 initializer=init_worker,initargs=(str(model) if model else None,)) as pool:
            for index,(gs,size,tested) in enumerate(pool.map(collect,tasks,chunksize=4)):
                coverage['tasks']+=1;coverage['tasks_with_groups']+=bool(gs);coverage['tested_candidates']+=tested
                coverage['reached_size_'+str(size)]+=1
                for x,y in gs:
                    groups.append((n,len(y)));n+=len(y);matrices.append(x);labels.append(y)
                    splits.append(stage=='train');taskids.append(tasknumber)
                tasknumber+=1
                if (index+1)%100==0:
                    status={'phase':'own_policy_frontiers' if refresh else 'heuristic_frontiers','split':stage,
                            'tasks':index+1,'total':len(tasks),'groups':len(groups),'rows':n,'seconds':time.monotonic()-started}
                    save(out/'progress.json',status);print(json.dumps(status),flush=True)
    assert matrices
    np.savez_compressed(out/'training.npz',X=np.concatenate(matrices),Y=np.concatenate(labels),
        groups=np.asarray(groups,dtype=np.int64),train=np.asarray(splits,bool),task_ids=np.asarray(taskids,dtype=np.int64))
    report={'status':'complete','groups':len(groups),'rows':n,'coverage':dict(coverage),
        'seconds':time.monotonic()-started,'teacher_only_at_training':True,'official_data_used':False,
        'matched':'task,kind,size; actual pending frontier + teacher value injection',
        'labels':'Known useful teacher values versus competing observations; not a global utility proof',
        'policy':'own MLP hybrid16' if refresh else 'heuristic','sha256':sha(out/'training.npz')}
    save(out/'manifest.json',report);return report

def merge(first,second,out):
    out.mkdir()
    with np.load(first/'training.npz',allow_pickle=False) as a,np.load(second/'training.npz',allow_pickle=False) as b:
        np.savez_compressed(out/'training.npz',X=np.concatenate([a['X'],b['X']]),Y=np.r_[a['Y'],b['Y']],
            groups=np.concatenate([a['groups'],b['groups']+np.asarray([len(a['Y']),0])]),
            train=np.r_[a['train'],b['train']],task_ids=np.r_[a['task_ids'],b['task_ids']])
    save(out/'manifest.json',{'sources':[sha(first/'training.npz'),sha(second/'training.npz')],
        'validation':'Unchanged first-pass groups only; refresh training tasks only'})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--tasks',type=int,default=12000)
    ap.add_argument('--workers',type=int,default=min(8,os.cpu_count() or 1));ap.add_argument('--data-only',action='store_true')
    ap.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    ap.add_argument('--epochs',type=int,default=80)
    ap.add_argument('--round-seconds',type=float,default=240)
    ap.add_argument('--small-seconds',type=float,default=120)
    ap.add_argument('--refresh-tasks',type=int,default=2000)
    args=ap.parse_args()
    if args.tasks<12 or args.workers<1 or args.epochs<1 or args.refresh_tasks<1 or min(args.round_seconds,args.small_seconds)<=0:ap.error('Use tasks>=12 and positive workers, epochs and budgets')
    if not args.data_only:
        import torch
        if args.device=='cuda' and not torch.cuda.is_available():ap.error('CUDA is unavailable; use --device cpu or auto')
    out=args.out;out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    pools,report=training_base.prepare_corpus(out/'corpus',args.tasks,18100837)
    print(json.dumps({'phase':'corpus_ready',**report}),flush=True)
    collect_data(pools,out/'data_round1',args.workers)
    if args.data_only:return
    models=out/'models';models.mkdir()
    training_base.train_model(out/'data_round1',models/'round1','mlp10m',18101001,args.round_seconds,args.device,args.epochs)
    collect_data(pools,out/'data_refresh',args.workers,models/'round1/best.npz',True,args.refresh_tasks)
    merge(out/'data_round1',out/'data_refresh',out/'data_round2')
    training_base.WARM_START=models/'round1'
    training_base.train_model(out/'data_round2',models/'round2','mlp10m',18101002,args.round_seconds,args.device,args.epochs)
    training_base.WARM_START=None
    training_base.train_model(out/'data_round2',models/'small','small_control',18101003,args.small_seconds,args.device,args.epochs)
    save(out/'training_complete.json',{'status':'complete','seconds':time.monotonic()-started,'official_data_used':False})
    print('TRAINING_COMPLETE',flush=True)

if __name__=='__main__':main()
