import json,statistics,csv,platform
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parent
manifest=json.loads((B/'manifest.json').read_text());docs=manifest['documents']; rows=[]
for engine in ['baseline','unstructured']:
 for d in docs:
  p=B/'results'/engine/(d['sha256']+d['extension']+'.json')
  if not p.exists():continue
  r=json.loads(p.read_text());r.update(extension=d['extension'],sha256=d['sha256'],bytes=d['bytes'],source_count=len(d['sources']),group='business' if any('/MyDocuments/' in s or '/Documents/' in s or '/Downloads/' in s for s in d['sources']) else 'other')
  rows.append(r)
fields=['engine','sha256','extension','group','bytes','status','init_s','parse_s','total_s','wall_s','process_request_index','peak_rss_mb','chars','blocks','tables','table_rows','table_html','headings','located_blocks','error_type','error']
with (B/'results.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
lines=['# 本地文档解析对照测试','',f'运行环境：{platform.platform()}。Apple M1 / 16 GiB RAM；现有代码 vs Unstructured 0.27.36。','',f"扫描命中 {sum(len(d['sources']) for d in docs)} 条已复制来源；按 SHA256+后缀去重 {len(docs)} 份。扫描错误 {len(manifest['scan_errors'])}，复制错误 {len(manifest['copy_errors'])}。",'', '## 范围和口径','', '- 原文件未修改；corpus 为副本，manifest.json 保存每份副本与所有原路径。','- PDF 对照使用 Unstructured fast 模式，不代表 hi_res 表格识别能力。扫描页能否 OCR 以实际结果为准。','- 现有实现保留其 20 MiB、200 页和 20 万单元格限制；限制失败与库能力失败需分开看。旧 DOC/XLS 原实现不支持。','- 单引擎串行、长驻进程，首次请求含冷启动。parse_s 可能含第一次按格式加载依赖；不是纯内核性能。','- 单文件 90 秒超时。peak_rss_mb 是当前进程累计峰值，不是单文件独占内存。','- business 仅按路径粗分（MyDocuments/Documents/Downloads），不是人工判断业务有效性。','- 真实文件未提供人工标注，字符数/表格数不能当准确率；输出需人工核验。','', '## 真实文件结果','', '|引擎|格式|已测|成功非空|空内容|失败/超时|解析耗时中位数(s)|P95(s)|','|---|---|---:|---:|---:|---:|---:|---:|']
for engine in ['baseline','unstructured']:
 for ext in sorted(set(d['extension'] for d in docs)):
  rs=[r for r in rows if r['engine']==engine and r['extension']==ext]; ts=sorted(r['parse_s'] for r in rs if r.get('status')=='ok' and 'parse_s'in r)
  c=Counter(r['status'] for r in rs)
  lines.append(f"|{engine}|{ext}|{len(rs)}|{c['ok']}|{c['empty']}|{len(rs)-c['ok']-c['empty']}|{statistics.median(ts):.3f}|{ts[min(len(ts)-1,int(len(ts)*.95))]:.3f}|" if ts else f"|{engine}|{ext}|{len(rs)}|{c['ok']}|{c['empty']}|{len(rs)-c['ok']-c['empty']}|—|—|")
lines+=['','## 控制样例功能检查','','|样例|引擎|状态|关键词覆盖|表格/行/HTML|标题数|','|---|---|---|---|---|---|']
expected=json.loads((B/'fixtures/expected.json').read_text())
for name,exp in expected.items():
 for engine in ['baseline','unstructured']:
  p=B/'results'/engine/(name+'.json');parsed=p.with_suffix('.parsed.json')
  if not p.exists():continue
  r=json.loads(p.read_text());data=json.loads(parsed.read_text()) if parsed.exists() else {};blocks=data.get('blocks',[])
  text='\n'.join(b.get('text','') for b in blocks)
  found=sum(term.lower() in text.lower() for term in exp['terms'])
  lines.append(f"|{name}|{engine}|{r['status']}|{found}/{len(exp['terms'])}|{r.get('tables',0)}/{r.get('table_rows',0)}/{r.get('table_html',0)}|{r.get('headings',0)}|")
lines+=['','## 同一文件双引擎成功的可比子集','']
pairs={}
for r in rows:pairs.setdefault((r['sha256'],r['extension']),{})[r['engine']]=r
for ext in sorted(set(d['extension'] for d in docs)):
 matches=[p for (sha,e),p in pairs.items() if e==ext and all(p.get(k,{}).get('status')=='ok' for k in ['baseline','unstructured'])]
 if matches:
  lines.append(f"- {ext}：{len(matches)} 份；baseline 解析中位数 {statistics.median(p['baseline']['parse_s'] for p in matches):.3f}s；Unstructured {statistics.median(p['unstructured']['parse_s'] for p in matches):.3f}s。")
lines+=['','## 控制样例的边界检查','']
for engine in ['baseline','unstructured']:
 p=B/'results'/engine/'merged.xlsx.parsed.json'
 if p.exists():
  blocks=json.loads(p.read_text()).get('blocks',[])
  text='\n'.join(b.get('text','') for b in blocks)
  lines.append(f"- {engine}：公式原式 `=1+1` {'保留' if '=1+1' in text else '未保留'}。合并表头和 0/False 的行列对应需查看结构 JSON，不以词命中代替。")
p=B/'results/unstructured_ocr/scan.pdf.json'
if p.exists():
 r=json.loads(p.read_text());lines.append(f"- Unstructured 单独 OCR 测试：{r['status']}，字符数 {r.get('chars',0)}，解析耗时 {r.get('parse_s',0):.3f}s；不混入 fast 性能表。")
lines+=['','## 错误分类','']
for engine in ['baseline','unstructured']:
 counter=Counter((r.get('error_type',r['status']),r.get('error','')[:160]) for r in rows if r['engine']==engine and r['status'] not in {'ok','empty'})
 lines.append(f'### {engine}')
 for (kind,msg),count in counter.most_common(12):lines.append(f'- {count} 次：{kind} — {msg}')
lines+=['','原始统计：results.csv；结构结果：results/<engine>/*.parsed.json；可重跑：.venv/bin/python run.py（已完成文件跳过）。']
(B/'REPORT.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[15:]))

selection=json.loads((B/'benchmark-selection.json').read_text())['documents']
lines += ['', '## 测试覆盖与具体判断', '', f'- 本轮选择 {len(selection)} 份去重原文件，另有 4 份自制控制样例；不是全量性能测试。选择清单见 benchmark-selection.json。']
for engine in ['baseline','unstructured']:
 done=sum((B/'results'/engine/(d['sha256']+d['extension']+'.json')).exists() for d in selection)
 lines.append(f'- {engine}：本轮选定原文件完成 {done}/{len(selection)}。')
lines += [
 '- 扫描覆盖主目录但不完整遍历 OrbStack 虚拟挂载（多次超时后停止，保留已发现路径）；macOS 拒绝访问的目录见 inventory.json，不能声称这些目录已完整扫描。',
 '- 部分测试与文件扫描/复制同时运行，本次耗时用于本机选型初筛，不是隔离资源后的严格性能排名。',
 '- Word 控制样例两者均保留关键文字、标题和表格；真实文档仍须检查阅读顺序、跨页内容等。',
 '- 原生 PDF 控制样例两者可提取关键文字，但均未还原为表格。本轮 Unstructured fast 不代表 hi_res 的表格识别效果，hi_res 未测。',
 '- Excel 控制样例：现有实现保留字符串 00123、数值 0、布尔 False、公式原式和合并来源；Unstructured 0.27.36 在本例把 count=0 输出为 False，未保留公式原式与显式合并关系。具体见 functional-checks.json。',
 '- Excel 公式：读取缓存计算值与保留公式原式是两种需求；样例公式没有缓存结果，空值不能直接推断所有公式都丢失。0/False 则是本例确实出现的值混淆，需要在目标版本与真实文件复验。',
 '- 扫描 PDF：现有实现和 fast 均无文字；单独启用本机 Tesseract OCR 能识别测试页。这里是英文扫描页，尚不能说明中文扫描件准确率。',
 '- DOC/XLS、格式损坏、体积/页数限制及超时要分别看待。运行环境缺少 LibreOffice 时的转换失败属于部署缺依赖，不代表安装齐全后仍不支持。',
 '', '## OCR 缓存后复测', '', '|次数|状态|导入(s)|解析(s)|字符数|', '|---|---|---:|---:|---:|'
]
for p in sorted((B/'results/ocr-repeat').glob('scan-*.json')):
 if '.parsed.' in p.name:continue
 r=json.loads(p.read_text());lines.append(f"|{p.stem}|{r['status']}|{r.get('init_s',0):.3f}|{r.get('parse_s',0):.3f}|{r.get('chars',0)}|")
lines += ['', '首次 OCR 记录含依赖/字体缓存初始化，不能视为稳定性能；复测为同一进程连续三次，不同文件与中文复杂版面需另测。', '', '## 选型建议', '', '当前数据不足以证明统一解析库普遍更好。现有实现对 Office 原始字段和表格溯源更可控；Unstructured 提供统一元素接口及可选 OCR，但需要接受额外依赖，并对值保真和复杂版面补充回归。先保留现有实现，用实际中文扫描件、跨页表格和多级表头补齐标注集后再决定是否替换。']
(B/'REPORT.md').write_text('\n'.join(lines)+'\n')
counts={engine:sum(r['engine']==engine for r in rows) for engine in ['baseline','unstructured']}
coverage=f"累计实际测试：baseline {counts['baseline']} 份，Unstructured {counts['unstructured']} 份（含扫描期间的早期抽样）；另有 4 份控制样例。表中耗时只统计成功非空文件，失败与超时另列。"
v=B/'corpus-verification.json'
if v.exists():
 verification=json.loads(v.read_text());coverage+=f" 副本哈希校验 {verification['checked']} 份，不一致 {len(verification['mismatches'])} 份。"
p=B/'REPORT.md';p.write_text(p.read_text().replace('## 真实文件结果',coverage+'\n\n## 真实文件结果'))
p=B/'REPORT.md'
p.write_text(p.read_text()+'\n## 补充：内容保真测试\n\n已对 16 份 Word、17 份 Excel 做源 XML 对照，并对 2 份 PDF 的第一页进行渲染核验。结果、评分口径与限制见 [内容保真测试](accuracy/REPORT.md)。复跑：`.venv/bin/python accuracy_test.py`。\n')
