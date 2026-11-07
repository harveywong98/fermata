import sys,json,runpy
from pathlib import Path
script=str(Path(__file__).with_name('worker.py'))
for line in sys.stdin:
 request=json.loads(line);sys.argv=[script,*request]
 try:
  runpy.run_path(script,run_name='__main__')
 except BaseException as exc:
  Path(request[2]).write_text(json.dumps({'engine':request[0],'status':'crash','error':str(exc)}))
 print('BENCH_DONE',flush=True)
