"""Source XML / visually transcribed gold; no parser output used as gold."""
import json,re,zipfile,collections,posixpath,unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET
from lxml import html
B=Path(__file__).resolve().parent; A=B/'accuracy'; A.mkdir(exist_ok=True)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
norm=lambda s:re.sub(r'\s+','',str(s))
def load(d,e):
 p=B/'results'/e/(d['sha256']+d['extension']+'.json')
 if not p.exists() or json.loads(p.read_text())['status']!='ok':return None
 return json.loads(p.with_suffix('.parsed.json').read_text())['blocks']
def expand_html(table):
 grid={};last=-1
 for ri,tr in enumerate(html.fromstring(table).xpath('//tr')):
  ci=0
  for c in tr:
   while (ri,ci) in grid:ci+=1
   value=''.join(c.itertext());rs=int(c.get('rowspan','1'));cs=int(c.get('colspan','1'))
   for y in range(ri,ri+rs):
    for x in range(ci,ci+cs):grid[y,x]=value;last=max(last,y)
   ci+=cs
 return [[grid.get((r,c),'') for c in range(max((x for y,x in grid if y==r),default=-1)+1)] for r in range(last+1)]
def tables(blocks,e):
 if e=='baseline':return [b['rows'] for b in blocks if b.get('kind')=='table']
 return [expand_html(b['metadata']['text_as_html']) for b in blocks if b.get('type')=='Table' and b.get('metadata',{}).get('text_as_html')]
def wordgrid(table):
 rows=[]
 for tr in table.findall(W+'tr'):
  row=[]
  before=tr.find(W+'trPr/'+W+'gridBefore')
  row.extend(['']*(int(before.get(W+'val')) if before is not None else 0))
  for c in tr.findall(W+'tc'):
   span=c.find(W+'tcPr/'+W+'gridSpan');span=int(span.get(W+'val')) if span is not None else 1
   merge=c.find(W+'tcPr/'+W+'vMerge');value=xmltext(c)
   for _ in range(span):
    ci=len(row)
    row.append(rows[-1][ci] if merge is not None and merge.get(W+'val','continue')=='continue' and rows and ci<len(rows[-1]) else value)
  rows.append(row)
 return rows
def xmltext(node):
 # Floating text boxes and their compatibility fallbacks are outside body scope.
 def walk(n):
  if n.tag in {W+'drawing',W+'pict',W+'txbxContent'}:return ''
  if n.tag==W+'t':return n.text or ''
  return ''.join(walk(c) for c in n)
 return walk(node)
results=[];docs=json.loads((B/'manifest.json').read_text())['documents']
for d in docs:
 outputs={e:load(d,e) for e in ['baseline','unstructured']}
 if not all(v is not None for v in outputs.values()) or d['extension'] not in {'.docx','.xlsx'}:continue
 with zipfile.ZipFile(B/d['file']) as z:
  if d['extension']=='.docx':
   body=ET.fromstring(z.read('word/document.xml')).find(W+'body')
   # Explicit scope: top-level body paragraphs and tables, not headers/text boxes/footnotes.
   units=[];goldtables=[]
   for child in body:
    if child.tag==W+'p':units.append(xmltext(child))
    elif child.tag==W+'tbl':
     tab=wordgrid(child);goldtables.append(tab)
     units.extend(xmltext(c) for row in child.findall(W+'tr') for c in row.findall(W+'tc'))
   units=[norm(x) for x in units if norm(x)]
   for e,blocks in outputs.items():
    text=norm(''.join(b.get('text','') for b in blocks));cursor=0;ordered=0;hits=0;miss=[]
    for unit in units:
     hits+=unit in text
     pos=text.find(unit,cursor)
     if pos>=0:ordered+=1;cursor=pos+len(unit)
     elif len(miss)<5:miss.append(unit[:160])
    actual=tables(blocks,e);correct=0;total=0
    for ti,tab in enumerate(goldtables):
     for ri,row in enumerate(tab):
      for ci,cell in enumerate(row):
       total+=1
       try:correct+=norm(cell)==norm(actual[ti][ri][ci])
       except IndexError:pass
    results.append({'file':d['file'],'name':Path(d['sources'][0]).name,'engine':e,'format':'docx','units':len(units),'recalled':hits,'ordered':ordered,'table_cells':total,'correct_table_cells':correct,'missing_or_out_of_order_examples':miss})
  else:
   shared=[]
   if 'xl/sharedStrings.xml' in z.namelist():shared=[''.join(n.text or '' for n in si.iter(S+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
   gold=[]
   for name in z.namelist():
    if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):continue
    for c in ET.fromstring(z.read(name)).iter(S+'c'):
     t=c.get('t');v=c.find(S+'v')
     if t=='s' and v is not None:value=shared[int(v.text)]
     elif t=='inlineStr':value=''.join(n.text or '' for n in c.iter(S+'t'))
     else:continue
     if norm(value):gold.append(norm(value))
   expected=collections.Counter(gold)
   for e,blocks in outputs.items():
    if e=='baseline':values=[c['value'] for b in blocks for c in b.get('cells',[])]
    else:
     values=[c for tab in tables(blocks,e) for row in tab for c in row]
     values.extend(b.get('text','') for b in blocks if b.get('type')!='Table')
    actual=collections.Counter(norm(v) for v in values if norm(v));matched=sum((expected&actual).values())
    results.append({'file':d['file'],'name':Path(d['sources'][0]).name,'engine':e,'format':'xlsx','text_cells':sum(expected.values()),'recalled_text_cells':matched,'missing_examples':list((expected-actual).items())[:5]})
# PDF phrases transcribed from rendered first pages, not extracted text.
pdfgold={
'b4820565976175b8f7c620addff59d15e429de36bdd314252de911dee65dafc1':[
'极客时间《企业级 Agent 工程架构实战营》课程大纲','一、课程定位','而不是停留在某一种框架或技术栈的使用层面。','课程将围绕企业级 Agent 系统设计中的核心架构问题展开：'],
'dc764a7577a85ebd3e9eb124427730828d887477aab387a99802aba7011b4cd3':[
'演示表格','出生日期','dd.mm.yyyy','旧金山','圣保罗','维也纳','更新：文本框从页面重用 Userfont UnifontMedium','这是一个示例文本。','那是下一行。']}
(A/'pdf-gold.json').write_text(json.dumps(pdfgold,ensure_ascii=False,indent=2))
for sha,phrases in pdfgold.items():
 d=next(d for d in docs if d['sha256']==sha)
 for e in ['baseline','unstructured']:
  blocks=load(d,e)
  if blocks is None:
   results.append({'engine':e,'format':'pdf_spot','file':d['file'],'checks':len(phrases),'strict_pass':0,'normalized_pass':0,'parse_failed':True});continue
  text=norm(''.join(b.get('text','') for b in blocks))
  # Optional display-equivalence score; never silently repair main result.
  clean=unicodedata.normalize('NFKC',re.sub(r'[\x00-\x1f]','',text))
  results.append({'engine':e,'format':'pdf_spot','file':d['file'],'checks':len(phrases),'strict_pass':sum(norm(x) in text for x in phrases),'normalized_pass':sum(norm(unicodedata.normalize('NFKC',x)) in clean for x in phrases),'details':[{'expected':x,'strict_pass':norm(x) in text,'normalized_pass':norm(unicodedata.normalize('NFKC',x)) in clean} for x in phrases]})
(A/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
lines=['# 内容保真测试','', '基准来自原始 Office XML 与人工查看 PDF 渲染页面后的转录，未使用任一待测解析器作为标准答案。','', '## 真实 Office 文件（两引擎均解析成功的可比子集）','', '|指标|现有实现|Unstructured|','|---|---:|---:|']
for fmt,nkey,dkey,label in [('docx','recalled','units','正文段落/单元格文本召回'),('docx','ordered','units','按原文顺序匹配的文本单元召回'),('docx','correct_table_cells','table_cells','表格按表/行/列位置精确匹配'),('xlsx','recalled_text_cells','text_cells','Excel 文本单元格值召回（计重复次数）')]:
 cells=[]
 for e in ['baseline','unstructured']:
  rs=[r for r in results if r['format']==fmt and r['engine']==e];n=sum(r[nkey] for r in rs);den=sum(r[dkey] for r in rs)
  cells.append(f'{n/den:.2%} ({n}/{den}，{len(rs)} 文件)' if den else '无样本')
 lines.append('|'+label+'|'+'|'.join(cells)+'|')
lines+=['','## PDF 人工核验片段（2 个第一页，共 13 项）','','|引擎|直接文本匹配|NFKC + 去控制符后匹配|','|---|---:|---:|']
for e in ['baseline','unstructured']:
 rs=[r for r in results if r['format']=='pdf_spot' and r['engine']==e];den=sum(r['checks'] for r in rs)
 lines.append(f"|{e}|{sum(r['strict_pass'] for r in rs)}/{den}|{sum(r['normalized_pass'] for r in rs)}/{den}|")
lines += ['', '## 解释与边界', '', '- 仅忽略空白后匹配，Office 不做字符归一化；文本召回衡量是否丢失原文单元，不能惩罚所有多余文本或证明语义正确。', '- Word 按原 XML 顶层正文/表格读取；不覆盖页眉、图片、脚注、文本框等。位置匹配按表序号、行列序号；双方先按 XML gridSpan/vMerge、HTML colspan/rowspan 展开合并单元格，再按网格位置比较。', '- Excel 真实文件指标只覆盖字符串单元格，按值及重复次数匹配，不证明行列正确，也不包含数值、日期、公式。行列对应及 0/False/公式另用 fixtures/merged.xlsx 控制样例核验，见 functional-checks.json。', '- Word 顺序匹配采用单调向前定位，是顺序召回诊断，不是通用阅读顺序准确率。', '- PDF 样本特意选择已发现异常的文件，存在选择偏差；其中一个是依赖库表单测试文件。只做问题复核，不能外推整体 PDF 错误率。解析失败按端到端片段未获取计分。', '- PDF 页图可见的表单值也计入检查，普通文本层提取遗漏这些值就是本需求下的覆盖不足；不据此断言库不支持专用表单 API。', '- PDF 归一化分数仅表示额外清洗可能修复的部分，不是当前解析器已实现的能力。', '- 不将这些不同口径指标加权拼成一个“总体准确率”。详情、漏项和标准答案在 accuracy/results.json、accuracy/pdf-gold.json，页图在 accuracy/pages/。', '', '复跑：`.venv/bin/python accuracy_test.py`。所有解析沿用此前保存结果，本测试不修改业务解析器。']
(A/'REPORT.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:24]))
p=A/'REPORT.md'
p.write_text(p.read_text()+'\n## 未匹配项复核修正\n\n- Word 源 XML 的文本框包含 Choice/Fallback 两套兼容表示，初版评分把它们拼成一段，且违背了排除文本框的范围。现已剔除，正文分母从 9624 修正为 9623。\n- 现有实现的 3 个真实未匹配项是嵌套表格中的设备编号；Unstructured 的 2 项是正文存储的页码 -1-、-2-。\n- Unstructured 的 Excel 48 个未匹配单元格（22 种不同值）经复核，均为实际换行变成字面量反斜杠+n；仅统一此换行表示后 48 项全部匹配。故 99.01% 是严格文本表示匹配率，不能称为内容丢失率；该样本归一化后的值召回为 100%。复验脚本：newline_diagnosis.py。\n')
