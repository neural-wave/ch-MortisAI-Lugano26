"""Matched-frontier MLP training. Synthetic data only; no sealed test is read."""
import argparse
import collections
from contextlib import nullcontext
import hashlib
import json
import math
import multiprocessing as mp
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np
from domain import domain as d
import corpus
import oracle
from features import features
from search import solve, heuristic
# v2 collector owns all supervision; old collector is not called.

ARCH = {'mlp10m': (256, 2078, 2240, 2144, 2), 'small_control': (256, 256, 128, 64, 2)}


def save(path, obj):
    path = Path(path); temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2) + '\n'); temp.replace(path)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sig(kind, values): return kind, tuple(oracle.canonical(v) for v in values)


def offline_worker():
    import sys
    def audit(event, args):
        if event.startswith('socket.'):
            raise PermissionError('Offline synthetic worker')
        if event == 'open' and args and isinstance(args[0], (str, bytes)):
            name = str(args[0])
            if name.endswith(('test.json', 'test_public.json')) or '/targets/' in name:
                raise PermissionError('Training cannot read tests or official targets')
    sys.addaudithook(audit)


def collect_task(task):
    rng = random.Random(int(corpus.digest(task['template_key'] + ':matched-frontier-v2'), 16))
    xs = [tuple(d.decode(v) for v in e['args']) for e in task['examples']]
    ys = tuple(d.decode(e['y']) for e in task['examples'])
    probes = [corpus.private_sample(task['family'], rng, i + 40) for i in range(12)]
    goal = sig(task['output_type'], ys)
    positives = collections.defaultdict(dict)
    for node in corpus.walk(task['ast']):
        if node['k'] != 'call': continue
        kind = d.infer_type(node, task['input_types']); size = d.tree_size(node)
        values = tuple(d.eval_ast(node, x) for x in xs)
        if sig(kind, values) == goal: continue
        semantic = sig(kind, [oracle.evaluate(node, x) for x in probes])
        positives[kind, size].setdefault(semantic, (node, values))
    if not positives: return {'groups': [], 'reason': 'no_partial_call'}
    public = {k:v for k,v in task.items() if k not in ('ast', 'template_key')}
    observed = []
    for mode in ('fifo', 'heuristic'):
        _, frontier = solve(public, {'mode': mode, 'time_ms': 80, 'max_candidates': 1400,
                                     'max_size': 9, 'beam': 32}, collect=True)
        observed.extend((c.ast, c.values, c.type, c.size, 'runtime_' + mode) for c in frontier)
    candidates = list(observed)
    for (kind, size), nodes in positives.items():
        for node, _ in nodes.values():
            candidates.extend((n, None, kind, d.tree_size(n), 'typed_subtree_mutation')
                              for n in mutations(node, task['input_types'])
                              if d.tree_size(n) == size)
        for _ in range(20):
            try:
                node = corpus.build(rng, task['input_types'], kind, size)
                if d.tree_size(node) == size:
                    candidates.append((node, None, kind, size, 'typed_generated'))
            except (ValueError, TypeError, ArithmeticError, IndexError): pass
    negative = collections.defaultdict(dict)
    for node, values, kind, size, source in candidates:
        group = kind, size
        if group not in positives: continue
        try:
            if d.infer_type(node, task['input_types']) != kind: continue
            if values is None: values = tuple(d.eval_ast(node, x) for x in xs)
            observed_key = sig(kind, values)
            if observed_key == goal: continue
            positive_public = {sig(kind, v) for _, v in positives[group].values()}
            if observed_key in positive_public: continue
            semantic = sig(kind, [oracle.evaluate(node, x) for x in probes])
            if semantic in positives[group]: continue
            f = features(node, values, ys, kind, task['output_type'], task['input_types'], xs)
            negative[group].setdefault(observed_key, (heuristic(f), f, source))
        except (ValueError, TypeError, ArithmeticError, IndexError, OverflowError): pass
    groups = []
    for (kind, size), nodes in positives.items():
        negatives = sorted(negative[kind, size].values(), key=lambda item: -item[0])
        if not negatives: continue
        chosen = negatives[:16]
        tail = negatives[16:]
        chosen += rng.sample(tail, min(16, len(tail)))
        pos = [features(n, v, ys, kind, task['output_type'], task['input_types'], xs)
               for n, v in nodes.values()]
        groups.append({'X': pos + [f for _, f, _ in chosen], 'Y': [1]*len(pos) + [0]*len(chosen),
                       'kind': kind, 'size': size, 'family': task['family'],
                       'provenance': dict(collections.Counter(s for _, _, s in chosen))})
    return {'groups': groups, 'eligible': len(positives), 'observed_frontier': len(observed)}


def prepare_corpus(out, maximum, seed):
    """Reuse synthetic seeds; fresh generated tasks are hash-split by template."""
    started = time.monotonic(); out.mkdir()
    pools = {stage: json.loads((Path(__file__).parent/'seed_corpus'/(stage+'.json')).read_text())
             for stage in ('train','validation')}
    prior=json.loads((Path(__file__).parent/'prior_exclusions.json').read_text())
    seen = {t['template_key'] for rows in pools.values() for t in rows} | set(prior['templates'])
    # Existing seed corpus was already semantically deduplicated across splits.
    semantics = set(prior['sampled_semantics'])
    for stage in pools:
        for task in pools[stage]:
            semantics.add(corpus.semantic_fingerprint(task['ast'], task['family']))
    rng = random.Random(seed); attempts = 0; new = 0
    while sum(map(len,pools.values())) < maximum and time.monotonic()-started < 150:
        attempts += 1
        family = tuple(corpus.FAMILIES)[attempts % 3]
        types, kind = corpus.FAMILIES[family]
        try:
            tree = corpus.build(rng, types, kind, rng.choice((5,7,9,9)))
            if d.tree_size(tree)<4 or sum(n['k']=='call' for n in corpus.walk(tree))<2: continue
            template = d.template_key(tree, types)
            if template in seen: continue
            behavior = corpus.semantic_fingerprint(tree, family)
            if behavior in semantics: continue
            examples=[]
            for i in range(24):
                args = corpus.sample(family, rng, i); value = d.eval_ast(tree, args)
                if oracle.canonical(value) != oracle.canonical(oracle.evaluate(tree, args)):
                    raise AssertionError('Generation oracle disagreement')
                examples.append({'args':[d.encode(v) for v in args], 'y':d.encode(value)})
            if len({json.dumps(e['y'],sort_keys=True) for e in examples})<3: continue
            stage = 'validation' if int(corpus.digest(template)[:8],16)%10==0 else 'train'
            task={'id':f'fresh-{family}-{new}', 'family':family, 'input_types':types,
                  'output_type':kind, 'ast':tree, 'template_key':template, 'max_size':9,
                  'examples':examples}
            pools[stage].append(task);seen.add(template);semantics.add(behavior);new+=1
        except (ValueError,TypeError,ArithmeticError,IndexError,OverflowError): continue
        if new and new%250==0: print(json.dumps({'phase':'corpus','fresh':new,'seconds':round(time.monotonic()-started,1)}),flush=True)
    # For deliberately small smoke runs use a deterministic task prefix only.
    if maximum < sum(map(len,pools.values())):
        nval=max(2, maximum//10); pools['validation']=pools['validation'][:nval]; pools['train']=pools['train'][:maximum-nval]
    keys=[{t['template_key'] for t in pools[s]} for s in pools]
    assert keys[0].isdisjoint(keys[1])
    for stage, tasks in pools.items(): save(out/(stage+'.json'),tasks)
    save(out/'exclusions.json',{'templates':sorted(seen),'sampled_semantics':sorted(semantics)})
    result={'seed':seed,'counts':{k:len(v) for k,v in pools.items()},'fresh_tasks_added':new,
            'reused_synthetic_seed_tasks':min(maximum,6750),'seconds':time.monotonic()-started,
            'template_overlap':0,'sampled_semantics_split_disjoint':True,
            'sampled_semantics_is_not_equivalence_proof':True,'official_data_used':False,'test_read':False}
    save(out/'manifest.json',result);return pools,result


def collect_data(pools, out, workers):
    out.mkdir();X=[];Y=[];groups=[];splits=[];task_ids=[];meta=[];coverage=collections.Counter();sources=collections.Counter()
    started=time.monotonic();task_number=0
    for stage,tasks in pools.items():
        with ProcessPoolExecutor(max_workers=workers,mp_context=mp.get_context('spawn'),initializer=offline_worker) as executor:
            for index,result in enumerate(executor.map(collect_task,tasks,chunksize=4)):
                coverage['tasks_seen']+=1;coverage['tasks_with_groups']+=bool(result['groups'])
                coverage['eligible_groups']+=result.get('eligible',0)
                for g in result['groups']:
                    groups.append((len(Y),len(g['Y'])));splits.append(stage=='train');task_ids.append(task_number)
                    X.extend(g['X']);Y.extend(g['Y']);sources.update(g['provenance'])
                    meta.append({'stage':stage,'kind':g['kind'],'size':g['size'],'family':g['family']})
                task_number+=1
                if (index+1)%250==0:
                    progress={'phase':'matched_traces','split':stage,'processed':index+1,'total':len(tasks),
                              'groups':len(groups),'rows':len(Y),'seconds':round(time.monotonic()-started,1)}
                    save(out/'progress.json',progress);print(json.dumps(progress),flush=True)
    matrix=np.asarray(X,dtype=np.float32);labels=np.asarray(Y,dtype=np.int8)
    assert matrix.ndim==2 and matrix.shape[1]==256 and np.isfinite(matrix).all()
    np.savez_compressed(out/'training.npz',X=matrix,Y=labels,groups=np.asarray(groups,dtype=np.int64),
                        train=np.asarray(splits,dtype=bool),task_ids=np.asarray(task_ids,dtype=np.int64))
    result={'groups':len(groups),'rows':len(Y),'positive_rows':int(labels.sum()),'coverage':dict(coverage),
            'negative_provenance':dict(sources),'competition_group':'task,type,exact_AST_size; call nodes only',
            'supervision':'Teacher-subexpression usefulness; not proof of necessity or search improvement',
            'seconds':time.monotonic()-started,'train_groups':sum(splits),'validation_groups':len(splits)-sum(splits),
            'training_sha256':sha(out/'training.npz'),'test_read':False,'official_data_used':False}
    save(out/'manifest.json',result);save(out/'group_metadata.json',meta);return result


def train_model(data, out, name, seed, seconds, device='auto', epochs=80):
    import torch
    from torch import nn
    started=time.monotonic();out.mkdir();rng=np.random.default_rng(seed)
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(1);torch.set_float32_matmul_precision('high')
    if device=='auto':device='cuda' if torch.cuda.is_available() else 'cpu'
    if device not in ('cpu','cuda'):raise ValueError('device must be auto, cpu or cuda')
    if device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA requested but unavailable; use --device cpu or auto')
    if epochs<1 or seconds<=0:raise ValueError('Positive epochs and time budget required')
    class Network(nn.Module):
        def __init__(self):
            super().__init__();self.layers=nn.ModuleList([nn.Linear(a,b) for a,b in zip(ARCH[name],ARCH[name][1:])])
        def forward(self,x):
            for layer in self.layers[:-1]:x=nn.functional.dropout(nn.functional.relu(layer(x)),p=.05,training=self.training)
            return self.layers[-1](x)
    with np.load(data/'training.npz',allow_pickle=False) as loaded:
        X=loaded['X'];Y=loaded['Y'];groups=loaded['groups'];train=loaded['train'];taskids=loaded['task_ids']
    train_groups=np.flatnonzero(train);val_groups=np.flatnonzero(~train)
    mask=np.zeros(len(Y),bool)
    for i in train_groups:
        start,n=groups[i];mask[start:start+n]=True
    mean=X[mask].mean(axis=0,dtype=np.float64).astype(np.float32)
    scale=np.maximum(X[mask].std(axis=0,dtype=np.float64),.05).astype(np.float32)
    values=torch.as_tensor((X-mean)/scale,device=device)
    positives=[];negatives=[]
    for start,n in groups:
        indices=np.arange(start,start+n);positives.append(indices[Y[indices]==1]);negatives.append(indices[Y[indices]==0])
    def sample(selected, generator):
        return np.asarray([np.r_[generator.choice(positives[g],2,replace=len(positives[g])<2),generator.choice(negatives[g],14,replace=len(negatives[g])<14)] for g in selected],dtype=np.int64)
    bytask=collections.defaultdict(list)
    for g in train_groups:bytask[int(taskids[g])].append(g)
    if not len(train_groups) or not len(val_groups):raise ValueError('Both TRAIN and validation competition groups are required; increase --tasks')
    model=Network().to(device)
    warm=globals().get('WARM_START')
    if warm and name=='mlp10m':
        checkpoint=torch.load(warm/'best.pt',map_location=device,weights_only=True);model.load_state_dict(checkpoint['state_dict'])
        with np.load(warm/'best.npz',allow_pickle=False) as z:mean=z['mean'];scale=z['scale']
        values=torch.as_tensor((X-mean)/scale,device=device)
    parameters=sum(p.numel() for p in model.parameters())
    assert parameters==sum((a+1)*b for a,b in zip(ARCH[name],ARCH[name][1:]))
    if name=='mlp10m':assert parameters==10000000
    optimizer=torch.optim.AdamW(model.parameters(),lr=3e-4,weight_decay=.01,fused=device=='cuda')
    bf16=device=='cuda' and torch.cuda.is_bf16_supported()
    dtype=(torch.bfloat16 if bf16 else torch.float16) if device=='cuda' else torch.float32
    scaler=torch.amp.GradScaler('cuda',enabled=device=='cuda' and not bf16)
    autocast=lambda:torch.autocast('cuda',dtype=dtype) if device=='cuda' else nullcontext()
    val_indices=torch.as_tensor(sample(val_groups,np.random.default_rng(739103)),device=device)
    def objective(scores):
        return (torch.logsumexp(scores,dim=1)-torch.logsumexp(scores[:,:2],dim=1)).mean()
    history=[];best=float('inf');stale=0;gradient_evidence=None
    protocol={'architecture':ARCH[name],'parameters':parameters,'seed':seed,'dtype':str(dtype),'device':device,
              'gpu':torch.cuda.get_device_name(0) if device=='cuda' else None,
              'torch':torch.__version__,'train_groups':len(train_groups),'validation_groups':len(val_groups),
              'loss':'multi-positive listwise matched-type-size 2positive14negative','sampling':'uniform tasks then one eligible competition group',
              'normalization_fit':'train rows only','selection':'minimum matched validation loss only',
              'limit':'Ranking loss is not actual search improvement; a separate CPU benchmark is required',
              'training_sha256':sha(data/'training.npz'),'sealed_test_read':False}
    save(out/'protocol.json',protocol)
    for epoch in range(1,epochs+1):
        tick=time.monotonic();model.train();losses=[]
        selected=[rng.choice(bytask[t]) for t in rng.permutation(list(bytask))]
        sampled=torch.as_tensor(sample(selected,rng),device=device)
        factor=min(1,epoch/3)*(.15+.85*.5*(1+math.cos(math.pi*(epoch-1)/80)))
        for group in optimizer.param_groups:group['lr']=3e-4*factor
        for batch in sampled.split(128):
            if time.monotonic()-started>seconds and history:break
            optimizer.zero_grad(set_to_none=True)
            with autocast():
                raw=model(values[batch.reshape(-1)]);scores=(raw[:,1]-raw[:,0]).float().reshape(-1,16);loss=objective(scores)
            scaler.scale(loss).backward();scaler.unscale_(optimizer)
            if gradient_evidence is None:
                gradient_evidence={n:{'numel':p.numel(),'finite':bool(torch.isfinite(p.grad).all()),'nonzero':int(torch.count_nonzero(p.grad))}
                                   for n,p in model.named_parameters()}
                assert all(v['finite'] for v in gradient_evidence.values())
                # Listwise ranking is invariant to a constant output offset.
                # Its output bias may therefore have an exactly zero gradient
                # on CPU. Every dense weight matrix must still receive gradients.
                assert all(v['nonzero']>0 for n,v in gradient_evidence.items() if n.endswith('.weight'))
                save(out/'gradient_evidence.json',gradient_evidence)
            nn.utils.clip_grad_norm_(model.parameters(),1);scaler.step(optimizer);scaler.update();losses.append(float(loss.detach()))
        model.eval();v_loss=0;top=0;count=0
        with torch.no_grad():
            for batch in val_indices.split(128):
                with autocast():raw=model(values[batch.reshape(-1)])
                scores=(raw[:,1]-raw[:,0]).float().reshape(-1,16)
                v_loss+=float(objective(scores))*len(batch);top+=int((scores.argmax(1)<2).sum());count+=len(batch)
        val=v_loss/count;entry={'epoch':epoch,'train_loss':sum(losses)/max(1,len(losses)),
                               'validation_loss':val,'validation_top1':top/count,'seconds':time.monotonic()-tick}
        history.append(entry)
        if val<best-1e-5:
            best=val;stale=0
            arrays={'mean':mean,'scale':scale}
            for i,layer in enumerate(model.layers):arrays['w'+str(i)]=layer.weight.detach().cpu().numpy().T.copy();arrays['b'+str(i)]=layer.bias.detach().cpu().numpy().copy()
            temp=out/'best.tmp.npz';np.savez_compressed(temp,**arrays);temp.replace(out/'best.npz')
            torch.save({'architecture':ARCH[name],'state_dict':model.state_dict()},out/'best.pt')
            save(out/'best_metrics.json',entry)
        else:stale+=1
        save(out/'history.json',history);save(out/'progress.json',{'phase':'training','model':name,**entry,'elapsed':time.monotonic()-started})
        print(json.dumps({'phase':'training','model':name,**entry}),flush=True)
        if stale>=15 or time.monotonic()-started>=seconds:break
    # Check the actual saved checkpoint against its autonomous NumPy export.
    checkpoint=torch.load(out/'best.pt',map_location=device,weights_only=True);model.load_state_dict(checkpoint['state_dict']);model.eval()
    check=X[:17]
    with torch.no_grad():expected=model(torch.as_tensor((check-mean)/scale,device=device)).float().cpu().numpy()
    v=(check-mean)/scale
    with np.load(out/'best.npz',allow_pickle=False) as z:
        exported=sum(z['w'+str(i)].size+z['b'+str(i)].size for i in range(4))
        for i in range(4):v=v@z['w'+str(i)]+z['b'+str(i)];v=np.maximum(v,0) if i<3 else v
    assert np.allclose(v,expected,rtol=2e-3,atol=2e-3),(v-expected).max()
    result={'status':'trained','parameters':parameters,'exported_parameters':exported,'epochs':len(history),
            'best':json.loads((out/'best_metrics.json').read_text()),'seconds':time.monotonic()-started,
            'checkpoint_sha256':sha(out/'best.npz'),'numpy_torch_parity':True,'max_parity_error':float(np.max(abs(v-expected))),
            'gradient_evidence_saved':True,'bytes':(out/'best.npz').stat().st_size,'sealed_test_read':False}
    result['device']=device
    save(out/'status.json',result);del model,optimizer,values
    if device=='cuda':torch.cuda.empty_cache()
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--minutes',type=float,default=40);ap.add_argument('--tasks',type=int,default=8500)
    ap.add_argument('--seed',type=int,default=18100711);ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--data-only',action='store_true');a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    pools,corpus_report=prepare_corpus(a.out/'corpus',a.tasks,a.seed)
    print(json.dumps({'phase':'corpus_ready',**corpus_report}),flush=True)
    trace_report=collect_data(pools,a.out/'data',min(8,max(1,a.workers)))
    if a.data_only:return
    remaining=max(90,a.minutes*60-(time.monotonic()-started));models={};models_root=a.out/'models';models_root.mkdir()
    for name,ratio in (('mlp10m',.8),('small_control',.2)):
        result=train_model(a.out/'data',models_root/name,name,a.seed,remaining*ratio)
        models[name]=name+'/best.npz';print(json.dumps({'phase':'model_complete','model':name,**result}),flush=True)
    manifest={'status':'checkpoints_frozen','models':models,'selection':'validation_loss_only','test_read':False,
              'sha256':{k:sha(models_root/v) for k,v in models.items()},'freeze_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
    save(models_root/'manifest.json',manifest)
    save(a.out/'training_complete.json',{'status':'training_complete','seconds':time.monotonic()-started,'corpus':corpus_report,'traces':trace_report,'models':manifest})
    print('TRAINING_COMPLETE '+json.dumps(manifest),flush=True)


if __name__=='__main__':main()
