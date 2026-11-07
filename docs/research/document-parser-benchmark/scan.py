"""Inventory all local PDF/Word/Excel files beneath home, without following symlinks."""
import os,json,time,shutil
from pathlib import Path
from collections import Counter
root=Path.home();out=Path(__file__).resolve().parent
rows=[];errors=[];t=time.time();visited=0
for folder,dirs,files in os.walk(root,followlinks=False,onerror=lambda e:errors.append({'path':e.filename,'error':str(e)})):
 dirs[:]=[d for d in dirs if Path(folder,d)!=out]
 visited+=1
 if visited%10000==0:print(f'scanned {visited} directories; found {len(rows)} documents',flush=True)
 for name in files:
  p=Path(folder,name)
  if p.suffix.lower() not in {'.pdf','.doc','.docx','.xls','.xlsx'}:continue
  try:
   if p.is_symlink():continue
   st=p.stat();rows.append({'path':str(p),'extension':p.suffix.lower(),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns})
  except OSError as e:errors.append({'path':str(p),'error':str(e)})
(out/'inventory.json').write_text(json.dumps({'files':rows,'errors':errors},ensure_ascii=False,indent=2))
print(json.dumps({'files':len(rows),'extensions':dict(Counter(r['extension'] for r in rows)),'total_bytes':sum(r['bytes'] for r in rows),'scan_errors':len(errors),'seconds':time.time()-t,'free_bytes':shutil.disk_usage(out).free}))
