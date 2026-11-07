"""Heuristic character audit, not an accuracy score."""
import json,re,collections
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'manifest.json').read_text())['documents'];out=[]
patterns={'replacement':r'\ufffd','control':r'[\x00-\x08\x0b\x0c\x0e-\x1f]','private_use':r'[\ue000-\uf8ff]','cid_literal':r'\(cid:\d+\)','cjk_spaced':r'[\u4e00-\u9fff](?:[ \t]+[\u4e00-\u9fff]){4,}'}
for d in m:
 for engine in ['baseline','unstructured']:
  p=B/'results'/engine/(d['sha256']+d['extension']+'.parsed.json')
  if not p.exists():continue
  metric=json.loads(p.with_name(p.name.replace('.parsed.json','.json')).read_text())
  if metric['status'] not in {'ok','empty'}:continue
  data=json.loads(p.read_text());text='\n'.join(b.get('text','') for b in data['blocks']);flags={};examples={}
  for name,pat in patterns.items():
   matches=list(re.finditer(pat,text))
   if matches:
    flags[name]=len(matches);examples[name]=[text[max(0,x.start()-50):min(len(text),x.end()+80)] for x in matches[:3]]
  r={'engine':engine,'file':d['file'],'sources':d['sources'],'chars':len(text),'flags':flags,'examples':examples};out.append(r)
(B/'character-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
for e in ['baseline','unstructured']:
 rows=[r for r in out if r['engine']==e];print(e,'outputs',len(rows),'flagged',sum(bool(r['flags']) for r in rows))
 for r in rows:
  if r['flags']:print(json.dumps({'name':Path(r['sources'][0]).name,'file':r['file'],'flags':r['flags'],'examples':r['examples']},ensure_ascii=False))
