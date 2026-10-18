"""Public I/O only; teacher files and network access forbidden."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import argparse,json,sys
from search import solve
from inference import load

def guard(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system'):raise PermissionError('Offline search')
    if event=='open' and args and isinstance(args[0],(str,bytes)):
        p=str(args[0])
        if p.endswith(('/test.json','/train.json','/validation.json')) or '/targets/' in p:
            raise PermissionError('Search cannot read teacher files')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--mode',required=True);ap.add_argument('--ms',type=int,default=1000);ap.add_argument('--model');a=ap.parse_args()
    sys.addaudithook(guard);model=load(a.model) if a.model else None
    for line in sys.stdin:
        task=json.loads(line)
        if 'ast' in task or 'template_key' in task:raise ValueError('Teacher in runtime task')
        kind='hybrid' if a.mode.startswith('hybrid') else a.mode
        shortlist=int(a.mode[6:]) if a.mode.startswith('hybrid') else 64
        print(json.dumps(solve(task,{'mode':kind,'shortlist':shortlist,'time_ms':a.ms,
            'max_candidates':100000,'max_size':9},model)),flush=True)
