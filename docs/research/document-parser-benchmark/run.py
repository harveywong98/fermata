"""Sequential warm-process timing, per-file timeout; local files never uploaded."""
import json,subprocess,sys,time,os,signal,selectors
from pathlib import Path
B=Path(__file__).resolve().parent
rows=json.loads((B/(sys.argv[1] if len(sys.argv)>1 else 'benchmark-selection.json')).read_text())['documents']
rows.sort(key=lambda d:(not any('/MyDocuments/' in s or '/Documents/' in s or '/Downloads/' in s for s in d['sources']),d['bytes']))
fixtures=[{'sha256':p.stem,'extension':p.suffix,'file':str(p.relative_to(B))} for p in (B/'fixtures').iterdir() if p.suffix in {'.pdf','.docx','.xlsx'}]
if os.environ.get('BENCH_EXTENSIONS'):
 allowed=set(os.environ['BENCH_EXTENSIONS'].split(','));rows=[r for r in rows if r['extension'] in allowed];fixtures=[r for r in fixtures if r['extension'] in allowed]
for engine in (sys.argv[2:] or ['baseline','unstructured']):
 proc=None;seq=0
 for i,d in enumerate(fixtures+rows):
  out=B/'results'/engine/(d['sha256']+d['extension']+'.json');out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists():continue
  if proc is None or proc.poll() is not None:
   log=(B/f'{engine}.log').open('a');proc=subprocess.Popen([sys.executable,str(B/'persistent_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1,start_new_session=True)
   selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ);seq=0
  seq+=1;start=time.monotonic();proc.stdin.write(json.dumps([engine,str(B/d['file']),str(out)])+'\n');proc.stdin.flush()
  finished=False
  while time.monotonic()-start<90:
   if not selector.select(timeout=1):
    if proc.poll() is not None:break
    continue
   msg=proc.stdout.readline()
   if msg.strip()=='BENCH_DONE':finished=True;break
   if not msg:break
  if not finished:
   if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL)
   proc.wait();proc=None
   out.write_text(json.dumps({'engine':engine,'source':d['file'],'status':'timeout_or_crash','total_s':time.monotonic()-start}))
  else:
   result=json.loads(out.read_text());result.update(process_request_index=seq,wall_s=time.monotonic()-start);out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
  if (i+1)%10==0:print(f'{engine}: {i+1}/{len(rows)+len(fixtures)}',flush=True)
 if proc is not None and proc.poll() is None:proc.stdin.close();proc.wait(timeout=10)
print('DONE',flush=True)
