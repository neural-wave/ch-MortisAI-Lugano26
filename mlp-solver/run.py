#!/usr/bin/env python3
"""Run the supplied financial submission or the separate MLP V2 experiment."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'
sys.path.insert(0,str(SRC))
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'

def timestamp(prefix):return ROOT/'runs'/(prefix+'_'+time.strftime('%Y%m%d_%H%M%S'))

def expression(node,names):
    if node['k']=='param':return names[node['i']]
    if node['k']=='lit':return json.dumps(node['value'],ensure_ascii=False)
    args=[expression(v,names) for v in node['args']]
    if node['op'] in ('add','sub','mul','int_add','le_money'):
        op={'add':'+','sub':'-','mul':'*','int_add':'+','le_money':'<='}[node['op']]
        return '('+(' '+op+' ').join(args)+')'
    return node['op']+'('+', '.join(args)+')'

def invoke(script,args):
    return subprocess.run([sys.executable,'-B','-u',str(script),*map(str,args)],cwd=ROOT).returncode

def validate_task(task):
    from domain import domain as d
    if not isinstance(task,dict) or 'ast' in task or 'template_key' in task:
        raise ValueError('Provide public input/output examples without ast or template_key')
    types=task.get('input_types');kind=task.get('output_type');examples=task.get('examples')
    allowed={'money','date','int','state','bool'}
    if not isinstance(types,list) or not types or len(types)>4 or any(t not in allowed for t in types) or kind not in allowed:
        raise ValueError('Expected 1 to 4 typed inputs and a supported output type')
    if not isinstance(examples,list) or not examples:raise ValueError('No examples')
    for row in examples:
        if len(row['args'])!=len(types) or [d.value_type(v) for v in row['args']]!=types or d.value_type(row['y'])!=kind:
            raise ValueError('Example types do not match task schema')
    return task

def solve_task(a):
    from search import solve
    from inference import load
    from domain import domain as d
    task=validate_task(json.loads(a.task.read_text()))
    if a.mode in ('neural','hybrid') and not a.model:raise ValueError('--model is required for neural/hybrid search')
    if a.time_ms<1 or a.max_candidates<1:raise ValueError('Positive search budgets required')
    model=load(a.model) if a.model else None
    result=solve(task,{'mode':a.mode,'time_ms':a.time_ms,'max_size':a.max_size,'max_candidates':a.max_candidates},model)
    out=(a.out or timestamp('solve')).resolve();out.mkdir(parents=True,exist_ok=False)
    result.update({'exact_fit_on_provided_examples':result['status']=='fit',
                   'generalization_proven':False,'teacher_ast_supplied':False,
                   'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest() if a.model else None})
    if result['ast']:
        exact=all(d.eval_ast(result['ast'],row['args'])==d.decode(row['y']) for row in task['examples'])
        if not exact:raise RuntimeError('Candidate failed exact replay')
        (out/'program.json').write_text(json.dumps({'ast':result['ast'],'input_types':task['input_types'],
             'output_type':task['output_type'],'input_names':task.get('input_names')},indent=2)+'\n')
        names=task.get('input_names') or ['x'+str(i) for i in range(len(task['input_types']))]
        result['formula']=expression(result['ast'],names)
        (out/'formula.txt').write_text(result['formula']+'\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));print('OUTPUT',out)
    return 0 if result['status']=='fit' else 2

def import_models(a):
    from inference import load,score_batch
    import numpy as np
    digest=hashlib.sha256(a.archive.read_bytes()).hexdigest()
    if a.sha256 and a.sha256.lower()!=digest:raise ValueError('Archive SHA-256 mismatch')
    destination=(a.out or ROOT/'models/colab_v2').resolve()
    if destination.exists():raise FileExistsError(destination)
    with zipfile.ZipFile(a.archive) as z:
        members=z.infolist()
        if len({m.filename for m in members})!=len(members):raise ValueError('Duplicate ZIP paths')
        for m in members:
            p=PurePosixPath(m.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in m.filename:raise ValueError('Unsafe ZIP path')
        checkpoints={}
        for variant in ('round1','round2','small'):
            matches=[m for m in members if m.filename.endswith('models/'+variant+'/best.npz')]
            if len(matches)==1:checkpoints[variant]=matches[0]
            elif len(matches)>1:raise ValueError('Ambiguous model '+variant)
        if not checkpoints:raise ValueError('No V2 model weights found. The SOURCE archive contains no trained weights.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.model-import-',dir=destination.parent) as temp:
            staged=Path(temp)
            records={}
            for variant,member in checkpoints.items():
                if member.file_size>100_000_000:raise ValueError('Unexpectedly large model')
                path=staged/(variant+'.npz');path.write_bytes(z.read(member));model=load(path)
                expected=107074 if variant=='small' else 10000000
                if model.parameters!=expected:raise ValueError('Unexpected parameter count '+variant)
                if not np.isfinite(score_batch(np.zeros((2,256),np.float32),model)).all():raise ValueError('Invalid neural forward')
                records[variant]={'file':path.name,'parameters':model.parameters,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            (staged/'manifest.json').write_text(json.dumps({'archive_sha256':digest,'models':records,
                'quality_independently_verified':False},indent=2)+'\n')
            staged.rename(destination)
    print('IMPORTED',destination);return 0

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('check');sub.add_parser('status')
    pipeline=sub.add_parser('pipeline',add_help=False);pipeline.add_argument('options',nargs=argparse.REMAINDER)
    train=sub.add_parser('train',add_help=False);train.add_argument('options',nargs=argparse.REMAINDER)
    evaluate=sub.add_parser('evaluate',add_help=False);evaluate.add_argument('options',nargs=argparse.REMAINDER)
    smoke=sub.add_parser('smoke');smoke.add_argument('--out',type=Path);smoke.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    solve=sub.add_parser('solve');solve.add_argument('--task',type=Path,required=True);solve.add_argument('--out',type=Path)
    solve.add_argument('--mode',choices=['fifo','heuristic','neural','hybrid'],default='heuristic');solve.add_argument('--model',type=Path)
    solve.add_argument('--time-ms',type=int,default=2000);solve.add_argument('--max-size',type=int,default=9);solve.add_argument('--max-candidates',type=int,default=100000)
    predict=sub.add_parser('predict');predict.add_argument('--program',type=Path,required=True);predict.add_argument('--args',required=True,help='JSON list of encoded inputs')
    imported=sub.add_parser('import-models');imported.add_argument('--archive',type=Path,required=True);imported.add_argument('--sha256');imported.add_argument('--out',type=Path)
    check=sub.add_parser('check-submission');check.add_argument('--legacy',type=Path,required=True);check.add_argument('--targets',type=Path,required=True)
    check.add_argument('--tasks',nargs='+')
    # Forward script-specific options without reinterpreting their flags.
    if len(sys.argv)>1 and sys.argv[1] in ('pipeline','train','evaluate'):
        command=sys.argv[1];script={'pipeline':'run_all.py','train':'train_v2.py','evaluate':'benchmark_v2.py'}[command]
        return invoke(SRC/script,sys.argv[2:])
    a=p.parse_args()
    if a.command=='doctor':
        import numpy as np
        report={'python':sys.version,'executable':sys.executable,'numpy':np.__version__,
                'submission_present':(ROOT/'submission/submission.py').exists(),'source_present':(SRC/'train_v2.py').exists()}
        if importlib.util.find_spec('torch'):
            import torch
            report.update(torch=torch.__version__,cuda=torch.cuda.is_available(),training_device='cuda' if torch.cuda.is_available() else 'cpu')
        else:report.update(torch=None,training_ready=False)
        report['available_checkpoints']=[str(x.relative_to(ROOT)) for folder in ('models','runs') for x in (ROOT/folder).rglob('*.npz') if x.name!='training.npz']
        print(json.dumps(report,indent=2));return 0
    if a.command=='check':return invoke(SRC/'check_local.py',[])
    if a.command=='status':
        for file in sorted((ROOT/'runs').glob('*/STATUS.json')):print(file.parent.name,file.read_text())
        return 0
    if a.command=='smoke':
        return invoke(SRC/'run_all.py',['--out',a.out or timestamp('smoke'),'--tasks',24,'--workers',2,'--device',a.device,
              '--epochs',2,'--round-seconds',30,'--small-seconds',15,'--refresh-tasks',24,
              '--test-tasks',6,'--test-ms',200,'--validation-per-family',1,'--validation-ms',150,'--long-tasks',0])
    if a.command=='solve':return solve_task(a)
    if a.command=='predict':
        from domain import domain as d
        program=json.loads(a.program.read_text());args=json.loads(a.args)
        if [d.value_type(v) for v in args]!=program['input_types']:raise ValueError('Input type mismatch')
        print(json.dumps(d.encode(d.eval_ast(program['ast'],args))));return 0
    if a.command=='import-models':return import_models(a)
    if a.command=='check-submission':
        args=['--submission',ROOT/'submission','--legacy',a.legacy.resolve(),'--targets',a.targets.resolve()]
        if a.tasks:args+=['--tasks',*a.tasks]
        return invoke(ROOT.parent/'starter_kit/check.py',args)

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,FileNotFoundError,FileExistsError) as error:raise SystemExit(str(error))
