"""Source XML / visually transcribed gold; no parser output used as gold."""
import json,re,zipfile,collections,posixpath,unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from lxml import html
B=Path(__file__).resolve().parent; A=B/'accuracy-docling'; A.mkdir(exist_ok=True)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
norm=lambda s:re.sub(r'\s+','',str(s))
def load(d,e):
 p=B/'results'/e/(d['sha256']+d['extension']+'.json')
 if not p.exists() or json.loads(p.read_text())['status']!='ok':return None
 return json.loads(p.with_suffix('.parsed.json').read_text())['blocks']
def expand_html(table):
 grid={};last=-1
 for ri,tr in enumerate(html.fromstring(table).xpath('//tr')):
  ci=0
  for c in tr:
   while (ri,ci) in grid:ci+=1
   value=''.join(c.itertext());rs=int(c.get('rowspan','1'));cs=int(c.get('colspan','1'))
   for y in range(ri,ri+rs):
    for x in range(ci,ci+cs):grid[y,x]=value;last=max(last,y)
   ci+=cs
 return [[grid.get((r,c),'') for c in range(max((x for y,x in grid if y==r),default=-1)+1)] for r in range(last+1)]
def tables(blocks,e):
 if e in {'baseline','docling'}:return [b['rows'] for b in blocks if b.get('kind')=='table']
 return [expand_html(b['metadata']['text_as_html']) for b in blocks if b.get('type')=='Table' and b.get('metadata',{}).get('text_as_html')]
def wordgrid(table):
 rows=[]
 for tr in table.findall(W+'tr'):
  row=[]
  before=tr.find(W+'trPr/'+W+'gridBefore')
  row.extend(['']*(int(before.get(W+'val')) if before is not None else 0))
  for c in tr.findall(W+'tc'):
   span=c.find(W+'tcPr/'+W+'gridSpan');span=int(span.get(W+'val')) if span is not None else 1
   merge=c.find(W+'tcPr/'+W+'vMerge');value=xmltext(c)
   for _ in range(span):
    ci=len(row)
    row.append(rows[-1][ci] if merge is not None and merge.get(W+'val','continue')=='continue' and rows and ci<len(rows[-1]) else value)
  rows.append(row)
 return rows
def xmltext(node):
 # Floating text boxes and their compatibility fallbacks are outside body scope.
 def walk(n):
  if n.tag in {W+'drawing',W+'pict',W+'txbxContent'}:return ''
  if n.tag==W+'t':return n.text or ''
  return ''.join(walk(c) for c in n)
 return walk(node)
results=[];docs=json.loads((B/'manifest.json').read_text())['documents']
for d in docs:
 outputs={e:load(d,e) for e in ['baseline','unstructured','docling']}
 if not all(v is not None for v in outputs.values()) or d['extension'] not in {'.docx','.xlsx'}:continue
 with zipfile.ZipFile(B/d['file']) as z:
  if d['extension']=='.docx':
   body=ET.fromstring(z.read('word/document.xml')).find(W+'body')
   # Explicit scope: top-level body paragraphs and tables, not headers/text boxes/footnotes.
   units=[];goldtables=[]
   for child in body:
    if child.tag==W+'p':units.append(xmltext(child))
    elif child.tag==W+'tbl':
     tab=wordgrid(child);goldtables.append(tab)
     units.extend(xmltext(c) for row in child.findall(W+'tr') for c in row.findall(W+'tc'))
   units=[norm(x) for x in units if norm(x)]
   for e,blocks in outputs.items():
    text=norm(''.join(b.get('text','') for b in blocks));cursor=0;ordered=0;hits=0;miss=[]
    for unit in units:
     hits+=unit in text
     pos=text.find(unit,cursor)
     if pos>=0:ordered+=1;cursor=pos+len(unit)
     elif len(miss)<5:miss.append(unit[:160])
    actual=tables(blocks,e);correct=0;total=0
    for ti,tab in enumerate(goldtables):
     for ri,row in enumerate(tab):
      for ci,cell in enumerate(row):
       total+=1
       try:correct+=norm(cell)==norm(actual[ti][ri][ci])
       except IndexError:pass
    results.append({'file':d['file'],'name':Path(d['sources'][0]).name,'engine':e,'format':'docx','units':len(units),'recalled':hits,'ordered':ordered,'table_cells':total,'correct_table_cells':correct,'missing_or_out_of_order_examples':miss})
  else:
   shared=[]
   if 'xl/sharedStrings.xml' in z.namelist():shared=[''.join(n.text or '' for n in si.iter(S+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
   gold=[]
   for name in z.namelist():
    if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):continue
    for c in ET.fromstring(z.read(name)).iter(S+'c'):
     t=c.get('t');v=c.find(S+'v')
     if t=='s' and v is not None:value=shared[int(v.text)]
     elif t=='inlineStr':value=''.join(n.text or '' for n in c.iter(S+'t'))
     else:continue
     if norm(value):gold.append(norm(value))
   expected=collections.Counter(gold)
   for e,blocks in outputs.items():
    if e=='baseline':values=[c['value'] for b in blocks for c in b.get('cells',[])]
    else:
     values=[c for tab in tables(blocks,e) for row in tab for c in row]
     values.extend(b.get('text','') for b in blocks if b.get('type')!='Table')
    actual=collections.Counter(norm(v) for v in values if norm(v));matched=sum((expected&actual).values()); normalized_actual=collections.Counter(norm(v).replace('\\n','') for v in values if norm(v));normalized_expected=collections.Counter(norm(v).replace('\\n','') for v in gold);normalized_matched=sum((normalized_expected&normalized_actual).values())
    results.append({'file':d['file'],'name':Path(d['sources'][0]).name,'engine':e,'format':'xlsx','text_cells':sum(expected.values()),'recalled_text_cells':matched,'normalized_recalled_text_cells':normalized_matched,'missing_examples':list((expected-actual).items())[:5]})

(A/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('Scored',len(results),'file-engine pairs')
