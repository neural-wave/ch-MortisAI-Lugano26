"""Portable two-round training, independent search evaluation and NPZ export."""
import argparse,datetime,hashlib,json,subprocess,sys,time,traceback,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--tasks',type=int,default=12000)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--device',choices=['auto','cpu','cuda'],default='auto')
    p.add_argument('--epochs',type=int,default=80)
    p.add_argument('--round-seconds',type=float,default=240)
    p.add_argument('--small-seconds',type=float,default=120)
    p.add_argument('--refresh-tasks',type=int,default=2000)
    p.add_argument('--test-tasks',type=int,default=120)
    p.add_argument('--test-ms',type=int,default=1000)
    p.add_argument('--validation-per-family',type=int,default=20)
    p.add_argument('--validation-ms',type=int,default=750)
    p.add_argument('--long-tasks',type=int,default=30)
    p.add_argument('--long-ms',type=int,default=3000)
    p.add_argument('--skip-benchmark',action='store_true')
    a=p.parse_args();root=a.out.resolve();root.mkdir(parents=True,exist_ok=False)
    def status(**data):
        data['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        (root/'STATUS.json').write_text(json.dumps(data,indent=2)+'\n')
    def run(script,phase,options):
        status(phase=phase,status='running')
        print('RUN',phase,root/(phase+'.log'),flush=True)
        with (root/(phase+'.log')).open('w') as log:
            subprocess.run([sys.executable,'-u',str(HERE/script),*map(str,options)],cwd=HERE,stdout=log,stderr=subprocess.STDOUT,check=True)
    started=time.monotonic()
    try:
        training=['--out',root/'run1']
        for key in ['tasks','workers','device','epochs','round_seconds','small_seconds','refresh_tasks']:
            training+=['--'+key.replace('_','-'),getattr(a,key)]
        run('train_v2.py','training',training)
        if not a.skip_benchmark:
            evaluation=['--run',root/'run1','--out',root/'evaluation']
            for key in ['test_tasks','test_ms','validation_per_family','validation_ms','long_tasks','long_ms']:
                evaluation+=['--'+key.replace('_','-'),getattr(a,key)]
            run('benchmark_v2.py','evaluation',evaluation)
        status(phase='complete',status='complete',seconds=time.monotonic()-started,
               requested_tasks=a.tasks,smoke_run=a.tasks<12000,evaluation_run=not a.skip_benchmark)
    except Exception as error:
        status(phase='failed',status='failed',error=str(error),traceback=traceback.format_exc());raise
    finally:
        path=root/'MLP10M_V2_RESULTS.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
            for f in sorted(root.rglob('*')):
                if f.is_file() and f!=path and f.name not in ('training.npz','DOWNLOAD_READY.json') and f.suffix!='.pt' and '__pycache__' not in f.parts:
                    archive.write(f,f.relative_to(root))
            for f in sorted(HERE.rglob('*')):
                if f.is_file() and (f.suffix=='.py' or f.name in ('SOURCE_MANIFEST.json','prior_exclusions.json')) and '__pycache__' not in f.parts:
                    archive.write(f,Path('source')/f.relative_to(HERE))
        state=json.loads((root/'STATUS.json').read_text())
        (root/'DOWNLOAD_READY.json').write_text(json.dumps({'file':str(path),'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pipeline_status':state['status'],
            'raw_training_arrays_included':False,'numpy_models_included':True},indent=2)+'\n')
        print('RESULTS',path,flush=True)

if __name__=='__main__':main()
