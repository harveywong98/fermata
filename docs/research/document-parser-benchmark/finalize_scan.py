"""Build final inventory from NUL-delimited rg results, preserving scan errors."""
import json
from pathlib import Path
B=Path(__file__).resolve().parent
files=[];errors=[];seen=set()
for raw in ((B/'inventory-paths.bin').read_bytes()+(B/'inventory-mount-partial.bin').read_bytes()).split(b'\0'):
 if not raw:continue
 p=Path(raw.decode(errors='surrogateescape'))
 if p.is_relative_to(B) or p.is_symlink() or str(p) in seen:continue
 seen.add(str(p))
 try:files.append({'path':str(p),'extension':p.suffix.lower(),'bytes':p.stat().st_size})
 except OSError as e:errors.append({'path':str(p),'error':str(e)})
errors += [{'error':line} for line in ((B/'scan-rg-errors.log').read_text(errors='replace')+'\n'+(B/'scan-host-errors.log').read_text(errors='replace')).splitlines() if line]
errors.append({'path':'/Users/mac/OrbStack','error':'Virtual mount scan stopped after repeated directory timeouts; only discovered paths included. Host rescan excludes this mount.'})
(B/'inventory.json').write_text(json.dumps({'files':files,'errors':errors},ensure_ascii=True,indent=2))
print('Inventory',len(files),'errors',len(errors))
