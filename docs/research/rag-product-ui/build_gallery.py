from pathlib import Path
import json,html,zipfile
r=Path(__file__).parent;m=json.loads((r/'manifest.json').read_text());by={x.get('file'):x for x in m if 'file' in x}
groups=[
('dify','Dify','文档管理与片段维护','官方文档截图，未标注精确应用版本。','把资料列表与片段详情分开；启停和归档是维护入口，不能据此认定有自动质量评分。',[
('dify-04.png','文档列表与批量操作'),('dify-05.png','片段内容与文档信息')]),
('ragflow','RAGFlow','解析结果对照与修订','官方文档 DEV 页面引用截图，图片可能来自较早版本。','最值得参考的是原文和解析片段并排显示；用户能发现表格错位、缺内容，并修订片段。',[
('ragflow-03.jpg','解析策略配置'),('ragflow-05.jpg','文件解析状态'),('ragflow-06.jpg','原文与解析片段对照'),('ragflow-07.jpg','修订片段、关键词与问题')]),
('fastgpt','FastGPT','导入前预览','官方快速上手教程截图，未标注精确应用版本。','上传→配置→预览→就绪，把检查分块内容纳入导入过程。预览不是系统自动证明资料正确。',[
('fastgpt-15.png','上传文件'),('fastgpt-16.png','解析与分块参数'),('fastgpt-17.png','入库前预览分块'),('fastgpt-18.png','资料处理完成与就绪状态')]),
('maxkb','MaxKB','分类维护、命中测试与入库工作流','官方 MaxKB-docs v2 分支截图；具体版本和商业功能以官方授权说明为准。','适合参考客户知识管理员的操作方式：标签维护、分段修订、试问，以及入库执行详情。',[
('maxkb-v2-document_action.png','文档列表与维护操作'),('maxkb-v2-Tag_Manage.png','标签管理'),('maxkb-v2-segmentation_management.png','分段管理'),('maxkb-v2-hittesting.png','问题命中测试'),('maxkb-v2-set_workflow_dataset.png','知识入库工作流'),('maxkb-v2-debug_workflow_dataset1.png','入库流程执行详情')]),
('qianfan','百度千帆','检索范围与命中测试','官方命中测试教程截图，未登录控制台实测。','测试问题、检索配置、结果和历史记录在一个页面内；能定位检索问题，但相似度不是内容正确率。',[
('qianfan-12.png','从知识库进入命中测试'),('qianfan-14.png','检索模式与重排配置'),('qianfan-16.png','命中结果与测试历史'),('qianfan-17.png','检索范围筛选入口')]),
('bailian','阿里云百炼','类目、标签与切片维护（文档核实）','仅取得官方问答示例界面；没有取得可确认的知识管理页面截图。','官方文档明确描述类目、标签、元数据和切片启停等页面操作。下图仅作问答显示参考，不能当作质量管理页面。',[
('bailian-08.png','问答结果展示示例；非知识管理截图')])]
intro='收集日期：2026-11-03。覆盖 6 款代表性产品，不是市场全部产品。图片来自官方文档或官方 GitHub 图片仓库，保留原始标注；没有现场登录实测，没有重绘或生成产品界面。点击图片可放大，点击原图可查看原始尺寸。'
css='''body{margin:0;background:#f5f7fa;color:#182337;font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1240px;margin:auto;padding:36px 24px}h1{font-size:34px;margin:8px 0}h2{font-size:26px;margin:0}p{max-width:1000px}.meta{color:#626d7f;font-size:14px}.nav{display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:#f5f7faf2;padding:15px 0;z-index:3}.nav button{padding:9px 17px;border:1px solid #ccd5e2;border-radius:20px;background:white;cursor:pointer}.nav button.active{background:#244fbe;color:white}section{margin:35px 0 55px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}figure{margin:0;padding:14px;background:white;border:1px solid #e0e6ed;border-radius:12px}figure img{width:100%;height:300px;object-fit:contain;cursor:zoom-in;background:#fafafa}figcaption{font-weight:600;margin-top:10px}a{color:#2459b4}figure .meta{display:flex;gap:18px}aside{background:#eaf0ff;padding:16px 22px;border-radius:12px}dialog{border:0;border-radius:12px;width:94vw;max-width:1700px;padding:14px}dialog::backdrop{background:#000b}dialog img{width:100%;max-height:85vh;object-fit:contain}dialog button{float:right;padding:8px 18px;cursor:pointer}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #dde3eb;padding:12px;text-align:left}@media(max-width:750px){.grid{grid-template-columns:1fr}main{padding:20px 14px}figure img{height:240px}}'''
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RAG 产品 UI 参考图册</title><style>'+css+'</style><main><p class="meta">隐私运营 Agent · 产品调研</p><h1>RAG 知识库界面参考图册</h1><p>'+intro+'</p><aside><b>先看这四处：</b>FastGPT 的入库预览、RAGFlow 的原文对照、MaxKB 的标签管理、千帆的命中测试。<br>已核实的是操作界面；不能据此声称这些产品都具备自动真实性判定、业务规则冲突检测或可靠的版本发布机制。</aside><nav class="nav"><button class="active" data-key="all">全部</button>']
for key,name,*_ in groups:parts.append(f'<button data-key="{key}">{name}</button>')
parts.append('</nav>')
md=['# RAG 产品 UI 调研与截图\n',intro+'\n','## 结论\n','成熟产品普遍提供知识维护界面。此次证据集中在分类/标签、解析/分块预览、片段修订、启停、检索测试；不应把这些等同于自动内容可信度评估。\n','推荐组合：FastGPT 导入流程 + RAGFlow 原文对照 + MaxKB 标签维护 + 千帆命中测试。你的业务另加材料用途、适用业务、生效版本，以及缺失字段/表头的待处理提示。\n']
count=0
for key,name,title,version,lesson,items in groups:
 parts.append(f'<section data-product="{key}"><h2>{name} · {title}</h2><p>{lesson}</p><p class="meta">{version}</p><div class="grid">')
 md.extend([f'## {name}：{title}\n',version+'\n',lesson+'\n'])
 for fn,cap in items:
  x=by['images/'+fn];x['gallery_caption']=cap;x['selected']=True;count+=1
  esc=html.escape;parts.append(f'<figure><img loading="lazy" src="{x["file"]}" alt="{esc(cap)}"><figcaption>{esc(cap)}</figcaption><div class="meta"><a href="{esc(x["page_url"])}" target="_blank" rel="noopener">官方来源</a><a href="{x["file"]}" target="_blank">本地原图</a></div></figure>')
  md.append(f'### {cap}\n\n![{cap}]({x["file"]})\n\n[官方来源]({x["page_url"]}) · [原图地址]({x["image_url"]})\n')
 parts.append('</div></section>')
parts.append('''<section data-product="all"><h2>你的产品可直接借鉴的设计</h2><table><tr><th>页面</th><th>保留功能</th><th>业务补充</th></tr><tr><td>知识资料</td><td>导入、状态、标签、启停、批量操作</td><td>规范 / 系统说明 / 已核验案例 / 原始证据；适用业务与有效版本</td></tr><tr><td>资料详情</td><td>原文对照、分块预览、修订、重新解析</td><td>缺表头、缺单位、来源待确认等具体问题；保留修订记录</td></tr><tr><td>知识验证</td><td>输入问题、查看命中片段与来源、测试历史</td><td>标记依据错误、版本过时、缺少条件；形成待处理任务</td></tr></table><p>实施边界：不把检索分数当可信度；不把解析成功当业务正确；不把替换原文件当索引已更新。MaxKB v2 文档明确提醒“替换原文档”不改变已有分段与向量，百炼也区分片段修改和源文件修改。</p><p><a href="https://github.com/1Panel-dev/MaxKB-docs/blob/v2/docs/user_manual/dataset/doclist.md">MaxKB 文档维护说明</a> · <a href="https://help.aliyun.com/zh/model-studio/rag/documents">百炼文档管理说明</a> · <a href="https://help.aliyun.com/zh/model-studio/rag-optimization/">百炼优化说明</a></p><p class="meta">截图版权归各产品及文档作者所有，收集用于内部产品设计研究。main 分支与在线文档可能更新，manifest.json 留存此次来源地址。</p></section></main><dialog id="zoom"><button id="close">关闭 ✕</button><img id="large" alt="截图原图"></dialog><script>const modal=document.getElementById('zoom');document.querySelectorAll('figure img').forEach(i=>i.addEventListener('click',()=>{document.getElementById('large').src=i.src;modal.showModal()}));document.getElementById('close').onclick=()=>modal.close();document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('section[data-product]').forEach(s=>s.hidden=b.dataset.key!=='all'&&s.dataset.product!==b.dataset.key&&s.dataset.product!=='all')});</script></html>''')
(r/'index.html').write_text(''.join(parts));md.extend(['## 重要边界\n','- 相似度不是可信度；解析完成不是业务质量合格。\n- 修改原文件、修改片段、重建索引是不同操作。\n- MaxKB v2 的替换原文档不会更新既有分段与向量：[原文](https://github.com/1Panel-dev/MaxKB-docs/blob/v2/docs/user_manual/dataset/doclist.md)。\n- 百炼此次没有获得知识管理页实图，只收录问答示例：[文档管理说明](https://help.aliyun.com/zh/model-studio/rag/documents)。\n- 完整来源和下载情况见 manifest.json。\n'])
(r/'README.md').write_text('\n'.join(md));(r/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
with zipfile.ZipFile(r/'rag-ui-reference.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in ['index.html','README.md','manifest.json']:z.write(r/f,f)
 for x in m:
  if x.get('selected'):z.write(r/x['file'],x['file'])
print('selected screenshots:',count,'products:',len(groups));print('gallery:',r/'index.html')
