import argparse,json,sys,time,resource,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('engine');p.add_argument('source');p.add_argument('output');a=p.parse_args()
t=time.perf_counter(); result={'engine':a.engine,'source':a.source}
try:
 if a.engine=='baseline':
  baseline = os.environ.get('BASELINE_PARSER_DIR')
  if not baseline or not (Path(baseline)/'document_parser.py').is_file():
   raise RuntimeError('复现历史 baseline 前，请恢复旧解析器并设置 BASELINE_PARSER_DIR；见 docs/DECISIONS.md')
  sys.path.insert(0,baseline)
  from document_parser import parse_document
  loaded=time.perf_counter(); data=parse_document(a.source)
  blocks=data['blocks']; texts=[b['text'] for b in blocks]
  tables=[b for b in blocks if b['kind']=='table']; headings=[b for b in blocks if b['kind']=='heading']
  located=sum(bool(b.get('source')) for b in blocks)
 elif a.engine in {'docling','docling_native'}:
  from docling_adapter import parse
  import docling.document_converter
  loaded=time.perf_counter(); data=parse(a.source,native=a.engine=='docling_native')
  blocks=data['blocks'];texts=[b['text'] for b in blocks]
  tables=[b for b in blocks if b['kind']=='table'];headings=[b for b in blocks if b['kind']=='heading']
  located=sum(bool(b.get('source')) for b in blocks)
  result.update(conversion_status=data['conversion_status'],conversion_errors=data['conversion_errors'],convert_s=data['convert_s'],adapter_s=data['adapter_s'],config=data['config'])
 else:
  from unstructured.partition.auto import partition
  loaded=time.perf_counter()
  kwargs={'filename':a.source}
  if Path(a.source).suffix.lower()=='.pdf':kwargs.update(strategy='ocr_only' if a.engine=='unstructured_ocr' else 'fast',languages=['chi_sim','eng'])
  elements=partition(**kwargs)
  blocks=[e.to_dict() for e in elements]; texts=[str(e) for e in elements]
  tables=[b for b in blocks if b['type']=='Table']; headings=[b for b in blocks if b['type']=='Title']
  located=sum(bool(b.get('metadata',{}).get('page_number') or b.get('metadata',{}).get('page_name')) for b in blocks)
  data={'blocks':blocks}
 end=time.perf_counter(); text='\n'.join(texts)
 result.update(status='ok' if text.strip() else 'empty',init_s=loaded-t,parse_s=end-loaded,total_s=end-t,chars=len(text),blocks=len(blocks),tables=len(tables),headings=len(headings),located_blocks=located,replacement_chars=text.count('\ufffd'),warnings=data.get('warnings',[]),table_rows=sum(b.get('kind')=='table_row' for b in blocks),table_html=sum(bool(b.get('metadata',{}).get('text_as_html')) for b in blocks))
 if a.engine in {'docling','docling_native'} and data['conversion_status'] not in {'success'}:result['status']='partial' if text.strip() else 'error'
 Path(a.output).with_suffix('.parsed.json').write_text(json.dumps(data,ensure_ascii=False,default=str))
except Exception as e:result.update(status='error',error_type=type(e).__name__,error=str(e)[:1500],total_s=time.perf_counter()-t)
result['peak_rss_mb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024/1024
Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2))
