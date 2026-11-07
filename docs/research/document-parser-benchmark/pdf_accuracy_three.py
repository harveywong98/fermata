"""Re-use the previously visually verified 13 PDF checkpoints; no new gold from parsers."""
import json,re,unicodedata
from pathlib import Path
B=Path(__file__).resolve().parent; gold=json.loads((B/'accuracy/pdf-gold.json').read_text());rows=[]
norm=lambda x:re.sub(r'\s+','',x)
for sha,phrases in gold.items():
 for engine in ['baseline','unstructured','docling','docling_native']:
  p=B/'results'/engine/(sha+'.pdf.json')
  if not p.exists():continue
  r=json.loads(p.read_text());blocks=[]
  if r['status'] in {'ok','partial','empty'}:blocks=json.loads(p.with_suffix('.parsed.json').read_text())['blocks']
  text=norm(''.join(b.get('text','') for b in blocks));clean=unicodedata.normalize('NFKC',re.sub(r'[\x00-\x1f]','',text))
  rows.append({'engine':engine,'sha256':sha,'status':r['status'],'checks':len(phrases),'strict_pass':sum(norm(x) in text for x in phrases),'normalized_pass':sum(norm(unicodedata.normalize('NFKC',x)) in clean for x in phrases),'check_details':[{'expected':x,'strict_pass':norm(x) in text,'normalized_pass':norm(unicodedata.normalize('NFKC',x)) in clean} for x in phrases]})
(B/'accuracy-docling/pdf-checks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for e in ['baseline','unstructured','docling','docling_native']:
 rr=[r for r in rows if r['engine']==e];print(e,sum(r['strict_pass'] for r in rr),sum(r['normalized_pass'] for r in rr),'of',sum(r['checks'] for r in rr))
