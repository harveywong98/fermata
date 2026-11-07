"""Sequential CPU llama.cpp retrieval ablation, exact cosine, no answer LLM."""
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
URL='http://127.0.0.1:18087'
CONTAINER='privacy-embedding-benchmark'
IMAGE='privacy-embedding-benchmark:b8576'
DATA=json.loads((ROOT/'dataset.json').read_text())

def dump(path,data):
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2))

def api(path,body=None):
 raw=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
 req=urllib.request.Request(URL+path,data=raw,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)

def command(args,**kw):return subprocess.run(args,check=True,text=True,**kw)

def normalized(v):
 assert all(math.isfinite(x) for x in v)
 n=math.sqrt(sum(x*x for x in v));assert n>0
 return [x/n for x in v]

def embed(texts):
 t=time.perf_counter();r=api('/v1/embeddings',{'input':texts,'model':'benchmark','encoding_format':'float'})
 rows=sorted(r['data'],key=lambda x:x['index'])
 assert len(rows)==len(texts)
 return [normalized(x['embedding']) for x in rows],time.perf_counter()-t,r.get('usage',{})

def query_text(key,text):
 if key=='qwen':return 'Instruct: Given a field description, retrieve the matching data types in an electricity business data catalog.\nQuery: '+text
 return '为这个句子生成表示以用于检索相关文章：'+text

def percentile(xs,p):
 xs=sorted(xs);pos=(len(xs)-1)*p;lo=int(pos);hi=min(lo+1,len(xs)-1)
 return xs[lo]+(xs[hi]-xs[lo])*(pos-lo)

def metrics(rows,kind):
 if kind=='single':
  return {'n':len(rows),**{f'hit@{k}':statistics.mean(r['rank']<=k for r in rows) for k in [1,3,5,10]},'mrr@10':statistics.mean(1/r['rank'] if r['rank']<=10 else 0 for r in rows)}
 return {'n':len(rows),**{f'{metric}@{k}':statistics.mean(r[f'{metric}@{k}'] for r in rows) for metric in ['recall','complete'] for k in [3,5,10,20]}}

def evaluate(key,vecs):
 entries=DATA['entries']; names={e['id']:e['name'] for e in entries};rows=[];groups={}
 for mode in ['names','descriptions']:
  for qmode in ['short','context']:
   subset=[q for q in DATA['queries'] if qmode in q]
   for q in subset:
    v=vecs[f'{qmode}:{q["id"]}'];scores=[sum(a*b for a,b in zip(v,vecs[f'{mode}:{e["id"]}'])) for e in entries]
    indices=sorted(range(len(entries)),key=lambda i:scores[i],reverse=True)
    ranked=[entries[i]['id'] for i in indices]
    r={'model':key,'catalog':mode,'query_mode':qmode,'query_id':q['id'],'query':q[qmode],'kind':q['kind'],'group':q['group'],'targets':q['target_names'],'top10':[{'id':entries[i]['id'],'name':entries[i]['name'],'score':scores[i]} for i in indices[:10]]}
    if q['kind']=='single':r['rank']=min(ranked.index(t)+1 for t in q['acceptable_ids'])
    else:
     relevant=set(q['relevant_ids']);r['all_target_ranks']={names[t]:ranked.index(t)+1 for t in relevant}
     for k in [3,5,10,20]:
      found=relevant.intersection(ranked[:k]);r[f'recall@{k}']=len(found)/len(relevant);r[f'complete@{k}']=int(found==relevant)
    rows.append(r)
   for kind in ['single','multi']:
    selected=[r for r in rows if r['catalog']==mode and r['query_mode']==qmode and r['kind']==kind]
    if selected:groups[f'{mode}/{qmode}/{kind}']=metrics(selected,kind)
 return rows,groups

def run(model):
 key=model['key'];out=OUT/key;out.mkdir(exist_ok=True)
 if (out/'summary.json').exists():print(key,'already complete',flush=True);return
 model_path=ROOT/'models'/model['file'];assert model_path.exists()
 context=512 if key!='qwen' else 2048
 cmd=['docker','run','-d','--name',CONTAINER,'--cpus','4','-p','127.0.0.1:18087:8080','-v',str(ROOT/'models')+':/models:ro','-e','MODEL_FILE='+model['file'],'-e','POOLING='+('last' if key=='qwen' else 'cls'),'-e',f'CONTEXT={context}',IMAGE]
 started=time.perf_counter();command(cmd,stdout=subprocess.DEVNULL)
 try:
  for _ in range(120):
   try:
    if api('/health').get('status')=='ok':break
   except Exception:pass
   state=command(['docker','inspect',CONTAINER,'--format','{{.State.Running}}'],capture_output=True).stdout.strip()
   if state!='true':raise RuntimeError('server exited; see server.log')
   time.sleep(1)
  else:raise RuntimeError('server startup timeout')
  load_seconds=time.perf_counter()-started
  print(key,'ready',round(load_seconds,2),flush=True)
  items=[]
  for mode in ['names','descriptions']:
   for e in DATA['entries']:
    text=e['name'] if mode=='names' else e['name']+'：'+e['description']
    items.append((mode+':'+e['id'],text))
  for mode in ['short','context']:
   items.extend((mode+':'+q['id'],query_text(key,q[mode])) for q in DATA['queries'] if mode in q)
  lengths={id_:len(api('/tokenize',{'content':text,'add_special':True})['tokens']) for id_,text in items}
  assert max(lengths.values())<=context, max(lengths.values())
  dump(out/'token_lengths.json',lengths)
  embed([items[0][1]]);embed([query_text(key,'查找联系信息')])
  vecs={};timings=[]
  for mode in ['names','descriptions','short','context']:
   selected=[x for x in items if x[0].startswith(mode+':')]
   batch=8 if mode in ['names','descriptions'] else 1
   for start in range(0,len(selected),batch):
    part=selected[start:start+batch];vectors,elapsed,usage=embed([x[1] for x in part])
    for (id_,_),v in zip(part,vectors):vecs[id_]=v
    timings.append({'mode':mode,'ids':[x[0] for x in part],'seconds':elapsed,'usage':usage})
   dump(out/'vectors.json',vecs);dump(out/'timings.json',timings)
   print(key,mode,'done',len(selected),flush=True)
  assert len({len(v) for v in vecs.values()})==1
  # Batch and singleton pooling consistency smoke check.
  single,_,_=embed([items[0][1]])
  consistency=sum(a*b for a,b in zip(single[0],vecs[items[0][0]]))
  assert consistency>0.999,consistency
  rows,scores=evaluate(key,vecs);dump(out/'rankings.json',rows)
  perf={}
  for mode in ['names','descriptions','short','context']:
   ts=[x for x in timings if x['mode']==mode];secs=[x['seconds'] for x in ts]
   perf[mode]={'requests':len(ts),'items':sum(len(x['ids']) for x in ts),'total_s':sum(secs),'items_per_s':sum(len(x['ids']) for x in ts)/sum(secs),'request_p50_ms':percentile(secs,.5)*1000,'request_p95_ms':percentile(secs,.95)*1000}
  memory=command(['docker','exec',CONTAINER,'cat','/sys/fs/cgroup/memory.peak'],capture_output=True).stdout.strip()
  info={'model':model,'file_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'image':command(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],capture_output=True).stdout.strip(),'dataset_sha256':hashlib.sha256((ROOT/'dataset.json').read_bytes()).hexdigest(),'dimension':len(single[0]),'max_tokens':max(lengths.values()),'startup_s':load_seconds,'container_memory_peak_bytes':int(memory),'batch_single_cosine':consistency,'metrics':scores,'performance':perf,'docker_command':cmd}
  dump(out/'summary.json',info)
  print(key,'COMPLETE',json.dumps(scores.get('descriptions/context/single')),flush=True)
 finally:
  with (out/'server.log').open('w') as f:subprocess.run(['docker','logs',CONTAINER],stdout=f,stderr=subprocess.STDOUT)
  subprocess.run(['docker','stop',CONTAINER],stdout=subprocess.DEVNULL)
  subprocess.run(['docker','rm',CONTAINER],stdout=subprocess.DEVNULL)

if __name__=='__main__':
 models=json.loads((ROOT/'models.json').read_text())
 for model in models:
  if len(sys.argv)==1 or model['key'] in sys.argv[1:]:run(model)
