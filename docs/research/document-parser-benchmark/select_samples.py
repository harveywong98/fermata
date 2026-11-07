"""Deterministic sample: all priority docs plus format/size-stratified additions."""
import json
from pathlib import Path
B=Path(__file__).resolve().parent
all_docs=json.loads((B/'manifest.json').read_text())['documents']
priority={x['path'] for x in json.loads((B/'inventory-priority.json').read_text())['files']}
selected={}
for d in all_docs:
 if priority.intersection(d['sources']):selected[d['file']]={**d,'selection_reason':'priority personal directories'}
for ext in ['.pdf','.docx','.xlsx','.doc','.xls']:
 candidates=sorted([d for d in all_docs if d['extension']==ext and d['file'] not in selected],key=lambda d:(d['bytes'],d['sha256']))
 # Quantiles of the remaining distinct files, rather than whichever directory was scanned first.
 for i in range(min(6,len(candidates))):
  d=candidates[round(i*(len(candidates)-1)/5)] if len(candidates)>=6 else candidates[i]
  selected[d['file']]={**d,'selection_reason':'format/size quantile'}
(B/'benchmark-selection.json').write_text(json.dumps({'documents':list(selected.values()),'policy':'All priority-directory files plus up to 6 size quantiles per extension; not every collected file is tested.'},ensure_ascii=False,indent=2))
print('Selected',len(selected),'of',len(all_docs))
