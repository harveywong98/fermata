"""Copy distinct document contents, retaining every original path in the manifest."""
import hashlib,json,shutil,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
inventory=json.loads((BASE/(sys.argv[1] if len(sys.argv)>1 else 'inventory.json')).read_text())
seen={}; errors=[]
for item in inventory['files']:
 p=Path(item['path'])
 try:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  key=(h.hexdigest(),item['extension'])
  if key not in seen:
   target=BASE/'corpus'/item['extension'][1:]/(key[0]+item['extension'])
   target.parent.mkdir(parents=True,exist_ok=True)
   if shutil.disk_usage(BASE).free < item['bytes'] + 2*1024**3:
    raise OSError('Insufficient free space; keep 2 GiB reserve')
   if not target.exists():
    shutil.copy2(p,target)
   elif target.stat().st_size != item['bytes']:
    raise OSError('Existing corpus copy size mismatch')
   seen[key]={'sha256':key[0],'extension':item['extension'],'bytes':target.stat().st_size,'file':str(target.relative_to(BASE)),'sources':[]}
  seen[key]['sources'].append(item['path'])
 except Exception as exc:errors.append({'path':str(p),'error':str(exc)})
manifest={'documents':list(seen.values()),'copy_errors':errors,'scan_errors':inventory['errors']}
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'unique_documents':len(seen),'original_paths':sum(len(x['sources']) for x in seen.values()),'bytes':sum(x['bytes'] for x in seen.values()),'copy_errors':len(errors)}))
