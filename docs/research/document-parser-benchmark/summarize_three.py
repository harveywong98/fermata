"""Report all 73 documents, and content/performance on identical successful subsets."""
import json,statistics,collections,csv
from pathlib import Path
B=Path(__file__).resolve().parent
engines=['baseline','unstructured','docling']; docs=json.loads((B/'docling-selection.json').read_text())['documents'];results={};lines=['# 三方文档解析对比','', '主对比：现有实现 / Unstructured 0.27.36（PDF fast）/ Docling 2.146.0（PDF Native；Office 原生转换）。Apple M1、16 GiB RAM。','', '## 执行覆盖','','|指标|现有实现|Unstructured|Docling|','|---|---:|---:|---:|']
for e in engines:
 results[e]={}
 for d in docs:
  result_engine='docling_native' if e=='docling' and d['extension']=='.pdf' else e
  p=B/'results'/result_engine/(d['sha256']+d['extension']+'.json')
  if p.exists():results[e][d['file']]=json.loads(p.read_text())
for label,states in [('成功且非空',{'ok'}),('空结果',{'empty'}),('部分结果',{'partial'}),('失败/超时',{'error','timeout_or_crash','crash'})]:
 cells=[]
 for e in engines:
  n=sum(r['status'] in states for r in results[e].values());cells.append(f'{n}/{len(docs)} ({n/len(docs):.2%})')
 lines.append('|'+label+'|'+'|'.join(cells)+'|')
lines.append('|实际完成|'+'|'.join(str(len(results[e])) for e in engines)+'|')
lines+=['','## 内容保真（三方均成功的同一批文件）','','|指标|现有实现|Unstructured|Docling|','|---|---:|---:|---:|']
a=json.loads((B/'accuracy-docling/results.json').read_text())
for fmt,nkey,dkey,label in [('docx','recalled','units','Word 文本单元召回'),('docx','ordered','units','Word 按原文顺序匹配召回'),('docx','correct_table_cells','table_cells','Word 表格位置与内容匹配'),('xlsx','recalled_text_cells','text_cells','Excel 文本值严格召回'),('xlsx','normalized_recalled_text_cells','text_cells','Excel 换行表示统一后召回')]:
 cells=[]
 for e in engines:
  rr=[r for r in a if r['format']==fmt and r['engine']==e];n=sum(r[nkey] for r in rr);den=sum(r[dkey] for r in rr)
  cells.append(f'{n/den:.3%} ({n}/{den}; {len(rr)}文件)' if den else '无可比样本')
 lines.append('|'+label+'|'+'|'.join(cells)+'|')
lines+=['','## 主性能：三方均成功的相同文件，解析耗时中位数','','|格式|文件数|现有实现(s)|Unstructured(s)|Docling(s)|','|---|---:|---:|---:|---:|']
for ext in ['.docx','.pdf','.xlsx']:
 ds=[d for d in docs if d['extension']==ext and all(results[e].get(d['file'],{}).get('status')=='ok' for e in engines)]
 vals=[f"{statistics.median(results[e][d['file']]['parse_s'] for d in ds):.3f}" if ds else '—' for e in engines]
 lines.append('|'+ext+'|'+str(len(ds))+'|'+'|'.join(vals)+'|')
lines+=['','## Docling 各格式执行结果','','|格式|成功|空|部分|失败/超时|','|---|---:|---:|---:|---:|']
for ext in sorted(set(d['extension'] for d in docs)):
 rr=[results['docling'][d['file']] for d in docs if d['extension']==ext and d['file'] in results['docling']];c=collections.Counter(r['status'] for r in rr)
 lines.append(f"|{ext}|{c['ok']}|{c['empty']}|{c['partial']}|{sum(v for k,v in c.items() if k not in {'ok','empty','partial'})}|")
lines+=['','## 配置、冷启动与限制','','- 同一批 73 份原文件，另有 4 份控制样例；每文件外部硬超时 90 秒。部分结果单列，不冒充完整成功。','- 主测试 Docling PDF 使用 NativePdfPipeline，无版面/OCR/表格模型；Office 使用原生转换。模型辅助标准模式仅对 2 份异常 PDF 和 2 份 PDF 控制样例另做补测，不混入主表。','- Docling 独立虚拟环境安装，依赖版本见 requirements-docling.lock.txt；未改变前两者的依赖。','- 主测试不需要模型；标准模式补测先单独下载模型，首次进程使用仍包含模型加载。parse_s 含转换和评分适配，convert_s/adapter_s 可分开查看；主测试的一部分与模型下载重叠，存在背景负载。','- 旧格式、损坏文件、缺少依赖和超时分别记录，执行失败率不等于内容错误率。','- Word/Excel 标准来自源 XML，正文不含浮动文本框；合并格统一展开。Excel 只评估字符串值，不覆盖数字/公式或所有行列错误；严格召回与换行归一化后召回分开。','- 召回不惩罚全部多余输出；按单元汇总，大文件权重大。PDF 没有全量人工标注，不能给出总体准确率。','- 主测试及标准模式补测都关闭 OCR；空扫描页属于配置覆盖不足，不是 Docling OCR 能力失败。','- 前两者沿用前次实测；测试时间和后台负载不同，性能用于选型初筛。', '', '## Docling 冷启动预热记录','']
p=B/'smoke-docling-pdf.json'
if p.exists():
 r=json.loads(p.read_text());lines.append(f"PDF 控制页预热：状态 {r['status']}；导入 {r.get('init_s',0):.3f}s，解析/首次模型准备 {r.get('parse_s',0):.3f}s。不是稳定单页耗时。")
lines+=['','## Docling 错误分类','']
c=collections.Counter((r.get('error_type',r['status']),(r.get('error') or '; '.join(r.get('conversion_errors',[])) or r.get('conversion_status',''))[:250]) for r in results['docling'].values() if r['status'] not in {'ok','empty'})
for (k,v),n in c.most_common():lines.append(f'- {n} 次：{k}：{v}')
lines+=['','参考配置：[Docling 官方 Pipeline Options](https://docling-project.github.io/docling/reference/pipeline_options/)。','复跑：`BENCH_EXTENSIONS=.docx,.xlsx,.doc,.xls .venv-docling/bin/python run.py docling-selection.json docling`，PDF：`BENCH_EXTENSIONS=.pdf .venv-docling/bin/python run.py docling-selection.json docling_native`；评分：`.venv/bin/python accuracy_three.py`；报告：`.venv/bin/python summarize_three.py`。']
(B/'COMPARISON-THREE.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:38]))
lines=['','## 主性能对比：Docling Native PDF（无版面/OCR/表格模型）','', '|指标|结果|','|---|---:|']
native={}
for d in docs:
 if d['extension']!='.pdf':continue
 p=B/'results/docling_native'/(d['sha256']+d['extension']+'.json')
 if p.exists():native[d['file']]=json.loads(p.read_text())
c=collections.Counter(r['status'] for r in native.values())
lines.extend([f'|完成|{len(native)}/23|',f"|成功/空/失败|{c['ok']}/{c['empty']}/{sum(v for k,v in c.items() if k not in {'ok','empty'})}|"])
matched=[d for d in docs if d['extension']=='.pdf' and native.get(d['file'],{}).get('status')=='ok' and all(results[e].get(d['file'],{}).get('status')=='ok' for e in ['baseline','unstructured'])]
if matched:
 vals={e:statistics.median(results[e][d['file']]['parse_s'] for d in matched) for e in ['baseline','unstructured']};vals['docling_native']=statistics.median(native[d['file']]['parse_s'] for d in matched)
 lines+=['',f"三方均成功的 {len(matched)} 份 PDF：现有实现 {vals['baseline']:.3f}s，Unstructured fast {vals['unstructured']:.3f}s，Docling Native {vals['docling_native']:.3f}s（中位数）。"]
lines+=['','## 控制样例与结构差异解释','','- Docling 的 Word 文本全部召回不意味着原网格结构完全保留：9 个单格代码表变成代码内容，3 个嵌套表格编号移到单独的子表。表格原位匹配把这些算作结构差异，不能解释成丢了 12 段文字。','- Docling 控制 Excel 保留 00123、0、False 和合并表头；未缓存公式单元格为空，不保留公式原式。这与只读取缓存值的行为相符。详见 docling-functional-checks.json。','- Docling PDF 首次下载采用 Xet 时出现长时间停滞，终止后改普通 HTTP 下载；中断日志保留在 docling-warmup-xet.log，不能把后一次预热时长当作全部安装准备时间。']
p=B/'COMPARISON-THREE.md';p.write_text(p.read_text()+'\n'.join(lines)+'\n')
fields=['engine','file','status','init_s','parse_s','total_s','wall_s','convert_s','adapter_s','peak_rss_mb','chars','blocks','tables','error_type','error']
with (B/'comparison-three.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
 for e,rr in {**results,'docling_native':native}.items():
  for file,r in rr.items():w.writerow({**r,'file':file,'engine':e})
p=B/'accuracy-docling/pdf-checks.json'
if p.exists():
 rr=json.loads(p.read_text());lines=['','## PDF 定向异常页人工检查（不是随机准确率）','','|引擎|完成文件数|直接片段匹配|NFKC/去控制符后|','|---|---:|---:|---:|']
 for e in ['baseline','unstructured','docling','docling_native']:
  er=[r for r in rr if r['engine']==e];den=sum(r['checks'] for r in er);lines.append(f"|{e}|{len(er)}/2|{sum(r['strict_pass'] for r in er)}/{den}|{sum(r['normalized_pass'] for r in er)}/{den}|")
 lines+=['','仅沿用前次人工转录的两页、13 项（含表单可见值）；超时或失败按未获取计。不能外推整体 PDF 内容准确率。']
 p=B/'COMPARISON-THREE.md';p.write_text(p.read_text()+'\n'.join(lines)+'\n')

full=[]
for d in json.loads((B/'docling-full-selection.json').read_text())['documents']:
 p=B/'results/docling'/(d['sha256']+'.pdf.json')
 if p.exists():full.append(json.loads(p.read_text()))
p=B/'COMPARISON-THREE.md';p.write_text(p.read_text()+f"\n标准模式补充真实 PDF 已完成 {len(full)}/2（另有 2 份 PDF 控制样例），不包含在主表成功率中。\n")

p=B/'COMPARISON-THREE.md';p.write_text(p.read_text()+"\n异常页复核：Docling Native 在课程大纲中未出现此前的 U+0001 控制符；但中文字体表单仍输出 `更新�文本框从顸面重用`，存在替换符和有效汉字误映射，不能把没有 `(cid:N)` 当成没有错误。\n")
lines=['','## 模型版样例耗时（单次，非总体性能）','','|文件|页数|Native(s)|标准模型版(s)|','|---|---:|---:|---:|']
for sha,name,pages in [('b4820565976175b8f7c620addff59d15e429de36bdd314252de911dee65dafc1','课程大纲',29),('dc764a7577a85ebd3e9eb124427730828d887477aab387a99802aba7011b4cd3','中文字体表单',2)]:
 vals=[]
 for e in ['docling_native','docling']:
  p=B/'results'/e/(sha+'.pdf.json');r=json.loads(p.read_text()) if p.exists() else {};vals.append(f"{r['parse_s']:.3f}" if r.get('status')=='ok' else r.get('status','未完成'))
 lines.append(f'|{name}|{pages}|'+ '|'.join(vals)+'|')
p=B/'COMPARISON-THREE.md';p.write_text(p.read_text()+'\n'.join(lines)+'\n')
