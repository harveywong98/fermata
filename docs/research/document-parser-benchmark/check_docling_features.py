import json
from pathlib import Path
B=Path(__file__).resolve().parent;checks=[]
for name in ['structured.docx','merged.xlsx','text-table.pdf','scan.pdf']:
 p=B/'results/docling'/(name+'.json')
 if not p.exists():continue
 r=json.loads(p.read_text());parsed=p.with_suffix('.parsed.json')
 blocks=json.loads(parsed.read_text()).get('blocks',[]) if parsed.exists() and r['status'] in {'ok','empty','partial'} else []
 text='\n'.join(b['text'] for b in blocks);tables=[b['rows'] for b in blocks if b.get('kind')=='table']
 if name=='merged.xlsx':
  values={row[1]:row[3] for tab in tables for row in tab if len(row)>3}
  for k,v in [('account_id','00123'),('count','0'),('enabled','False'),('formula','=1+1')]:checks.append({'file':name,'check':k,'expected':v,'actual':values.get(k),'pass':values.get(k)==v})
  native=json.loads(parsed.read_text())['native'];checks.append({'file':name,'check':'merged_header_span','pass':any(c.get('col_span',1)==2 and c.get('text')=='Identity' for t in native['tables'] for c in t['data']['table_cells'])})
 elif name=='structured.docx':
  checks.extend([{'file':name,'check':'negation_preserved','pass':'Account ID is not automatically a national identity number.' in text},{'file':name,'check':'table_relation','pass':any(row==['customer_phone','Sensitive'] for tab in tables for row in tab)}])
 elif name=='text-table.pdf':checks.append({'file':name,'check':'table_relation','pass':any(row==['customer_phone','Sensitive'] for tab in tables for row in tab)})
 else:checks.append({'file':name,'check':'scan_text_with_ocr_disabled','pass':'Customer phone' in text,'note':'OCR disabled in main comparison; not an OCR capability test'})
(B/'docling-functional-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(json.dumps(checks,ensure_ascii=False,indent=2))
