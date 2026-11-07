import urllib.request,json,concurrent.futures,re
from pathlib import Path
root=Path(__file__).parent;s=json.loads((root/'sources.json').read_text());(root/'images').mkdir(exist_ok=True)
jobs=[]
for k,v in s.items():
 seen=set()
 for i,x in enumerate(v.get('images',[])):
  u=x['src']
  keep=(k=='dify' and 'manage-' in u) or (k=='ragflow' and 'raw.githubusercontent' in u) or (k=='fastgpt' and any(f'image-{n:02}.png' in u for n in range(12,18))) or (k=='maxkb' and '/FAQ/' in u) or (k=='bailian' and 'help-static-' in u) or (k=='qianfan' and '/doc/bce-doc/' in u)
  if keep and u not in seen:seen.add(u);jobs.append((k,i,x,v['url']))
def run(job):
 k,i,x,page=job;name=f'{k}-{i:02}.png' if not x['src'].split('?')[0].endswith('.jpg') else f'{k}-{i:02}.jpg';p=root/'images'/name
 try:
  b=urllib.request.urlopen(urllib.request.Request(x['src'],headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read();p.write_bytes(b)
  return {'product':k,'file':'images/'+name,'image_url':x['src'],'page_url':page,'caption':x['alt'],'bytes':len(b)}
 except Exception as e:return {'product':k,'error':str(e),'image_url':x['src']}
res=list(concurrent.futures.ThreadPoolExecutor(10).map(run,jobs));(root/'manifest.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps(res,ensure_ascii=False,indent=2))
