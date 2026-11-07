import json,runpy,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
outdir=B/'results/ocr-repeat';outdir.mkdir(exist_ok=True)
for i in range(3):
 out=outdir/f'scan-{i}.json'
 sys.argv=['worker.py','unstructured_ocr',str(B/'fixtures/scan.pdf'),str(out)]
 runpy.run_path(str(B/'worker.py'),run_name='__main__')
 r=json.loads(out.read_text());print(i,{k:r.get(k) for k in ['status','init_s','parse_s','total_s','chars']},flush=True)
