import runpy,difflib,json,collections,zipfile,re
from pathlib import Path
s=runpy.run_path('accuracy_test.py');B=s['B'];S=s['S'];ET=s['ET'];norm=s['norm'];tables=s['tables']
d=next(d for d in s['docs'] if d['sha256'].startswith('b4d089'))
with zipfile.ZipFile(B/d['file']) as z:
 shared=[''.join(n.text or '' for n in si.iter(S+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))];gold=[]
 for name in z.namelist():
  if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):continue
  for c in ET.fromstring(z.read(name)).iter(S+'c'):
   v=c.find(S+'v');t=c.get('t')
   if t=='s' and v is not None:val=shared[int(v.text)]
   elif t=='inlineStr':val=''.join(n.text or '' for n in c.iter(S+'t'))
   else:continue
   if norm(val):gold.append(norm(val))
blocks=s['load'](d,'unstructured');actual=[norm(c) for tab in tables(blocks,'unstructured') for row in tab for c in row]+[norm(b.get('text','')) for b in blocks if b.get('type')!='Table']
missing=collections.Counter(gold)-collections.Counter(actual)
clean=collections.Counter(v.replace('\\n','') for v in actual)
expected=collections.Counter(gold)
print('STRICT MISSING',sum(missing.values()),'AFTER LITERAL NEWLINE NORMALIZATION',sum((expected-clean).values()))
print('MISSING VALUE TYPES',len(missing))
(B/'accuracy/newline-diagnosis.json').write_text(json.dumps({'strict_missing_cells':sum(missing.values()),'missing_distinct_values':len(missing),'after_literal_newline_normalization_missing':sum((expected-clean).values())},indent=2))
