import json
from pathlib import Path
from lxml import html
B=Path(__file__).resolve().parent
checks=[]
for engine in ['baseline','unstructured']:
 p=B/'results'/engine/'merged.xlsx.parsed.json'
 if not p.exists():continue
 blocks=json.loads(p.read_text())['blocks']
 if engine=='baseline':
  rows=[b['cells'] for b in blocks if b.get('cells')]
  values={r[1]['value']:r[3]['value'] for r in rows if len(r)>3}
  merged=any(c.get('merged_from') for r in rows for c in r)
 else:
  rows=[]
  for b in blocks:
   table=b.get('metadata',{}).get('text_as_html')
   if table:
    for tr in html.fromstring(table).xpath('//tr'):rows.append([''.join(c.itertext()) for c in tr])
  values={r[1]:r[3] for r in rows if len(r)>3}
  merged=any('colspan="2"' in b.get('metadata',{}).get('text_as_html','') for b in blocks)
 for key,expected in [('account_id','00123'),('count','0'),('enabled','False'),('formula','=1+1')]:
  checks.append({'engine':engine,'feature':key,'expected':expected,'actual':values.get(key),'pass':values.get(key)==expected})
 checks.append({'engine':engine,'feature':'explicit_merged_header_relation','pass':merged})
for engine in ['baseline','unstructured','unstructured_ocr']:
 p=B/'results'/engine/'scan.pdf.parsed.json'
 if p.exists():
  text='\n'.join(b.get('text','') for b in json.loads(p.read_text())['blocks'])
  checks.append({'engine':engine,'feature':'scan_text','pass':'Customer phone'.lower() in text.lower()})
(B/'functional-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
