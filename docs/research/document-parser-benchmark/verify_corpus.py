"""Verify collected copies against content hashes; originals remain untouched."""
import hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
m=json.loads((B/'manifest.json').read_text());bad=[]
for d in m['documents']:
 p=B/d['file'];h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 if h.hexdigest()!=d['sha256'] or p.stat().st_size!=d['bytes']:bad.append(d['file'])
r={'checked':len(m['documents']),'mismatches':bad,'bytes':sum(d['bytes'] for d in m['documents'])}
(B/'corpus-verification.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
