import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).parent
OUT=ROOT/'results'
LABELS={'small':'BGE-small-zh-v1.5','base':'BGE-base-zh-v1.5','qwen':'Qwen3-Embedding-0.6B'}
def pct(v):return f'{v*100:.1f}%'

def main():
 summaries={k:json.loads((OUT/k/'summary.json').read_text()) for k in LABELS}
 rankings={k:json.loads((OUT/k/'rankings.json').read_text()) for k in LABELS}
 expected=hashlib.sha256((ROOT/'dataset.json').read_bytes()).hexdigest()
 assert all(s['dataset_sha256']==expected for s in summaries.values()),'Dataset changed since evaluation'
 assert len({s['image'] for s in summaries.values()})==1,'Mixed runtime images'
 lines=['# 电力数据类型 Embedding 实测','',
 '日期：2026-11-03。100 个候选类型；61 个单目标/可接受同义目标用例；6 个多目标完整召回用例。全部为基于类型名称构造的合成测试，不是客户真实标注集。',
 '', '## 判断','',
 '- 当前优先把base作为候选召回器：双侧描述Top5找回61/61，Top1为51/61。Qwen Top1为53/61，只多2题，CPU延迟与内存更高；小样本不足以证明统计显著优势。',
 '- small适合资源紧张部署，但本次双侧描述仍有一个目标排到第13，不能宣称Top5全覆盖。',
 '- 描述改善了单目标整体表现，却不是逐题单调改善：Qwen多目标在仅名称目录时Top10六题全覆盖，扩充定义后“价格字段”一题漏掉启停调峰电价。',
 '- 当前目录只有100项。要求完整枚举某类字段时，明确分组/结构化过滤更可控；提高K只是本次实验补救，不保证扩大目录后仍完整。',
 '- 原文件不足以验证客户内部口径。待核对字段不会被包装成已验证事实；如果补充真实表注释、单位与客户问题，应重新评测再决定生产模型。',
 '', '## 结果怎么看','',
 '- 单目标 Hit@K：前 K 条含任一可接受目标的用例比例；这里不能用“找齐所有相关项”解释。',
 '- 多目标 Recall@K：每题已找回目标数 / 全部目标数，再取题目均值。Complete@K：每题的全部目标都找齐的比例。',
 '- 短查询组故意缺上下文，例如多个类型都只问“编号”；其命中是预设意图可恢复程度，不是无歧义分类准确率。',
 '- 只比较检索候选，不包含大模型最终分类、规则执行或自动拒答；没有用生成模型裁判。',
 '', '## 1. 单目标：目录与输入同时补描述','',
 '|模型|Top1 命中|Top3 命中|Top5 命中|Top10 命中|MRR@10|', '|---|---:|---:|---:|---:|---:|']
 for k,s in summaries.items():
  m=s['metrics']['descriptions/context/single']
  lines.append('|'+LABELS[k]+'|'+'|'.join(pct(m[f'hit@{n}']) for n in [1,3,5,10])+f"|{m['mrr@10']:.3f}|")
 lines+=['','## 2. 描述加在哪一侧：四组对照（Top1 / Top5）','','|目录|待识别输入|small|base|qwen|','|---|---|---:|---:|---:|']
 for catalog,clabel in [('names','仅类型名'),('descriptions','类型名＋定义')]:
  for qm,qlabel in [('short','模糊短字段'),('context','字段业务描述')]:
   cells=[]
   for s in summaries.values():
    m=s['metrics'][f'{catalog}/{qm}/single'];cells.append(f"{pct(m['hit@1'])} / {pct(m['hit@5'])}")
   lines.append(f'|{clabel}|{qlabel}|'+'|'.join(cells)+'|')
 lines+=['','## 3. 多目标：能否全部找齐（输入含业务描述）','','|模型|目录|Recall@5|Complete@5|Recall@10|Complete@10|Recall@20|Complete@20|','|---|---|---:|---:|---:|---:|---:|---:|']
 for k,s in summaries.items():
  for mode in ['names','descriptions']:
   m=s['metrics'][f'{mode}/context/multi']
   lines.append(f'|{LABELS[k]}|{mode}|'+'|'.join(pct(m[f'{x}@{n}']) for n in [5,10,20] for x in ['recall','complete'])+'|')
 lines+=['','有一题包含 8 个正确类型，因此固定 Top5 在数学上不可能将该题全部找齐。不能据此认定是模型能力不足。目录枚举任务可用显式类型分组/关键词条件并集；向量 TopK 不提供完整性保证。',
 '', '## 4. 性能（Docker ARM64 CPU）','',
 '|模型|向量维度|目录＋定义 编码项/秒|业务查询 P50 ms|业务查询 P95 ms|容器峰值 MiB|启动秒|最大输入tokens|',
 '|---|---:|---:|---:|---:|---:|---:|---:|']
 for k,s in summaries.items():
  p=s['performance'];q=p['context']
  lines.append(f"|{LABELS[k]}|{s['dimension']}|{p['descriptions']['items_per_s']:.1f}|{q['request_p50_ms']:.1f}|{q['request_p95_ms']:.1f}|{s['container_memory_peak_bytes']/1048576:.1f}|{s['startup_s']:.2f}|{s['max_tokens']}|")
 lines+=['','- Apple M1 / 主机16GiB；OrbStack Linux ARM64 VM 8CPU / 约8GiB；容器4CPU，llama.cpp线程4，GPU层0。',
 '- 三模型顺序运行；F16 GGUF；同一 llama.cpp b8576，统一 --no-mmap，避免Docker宿主挂载的按页读取干扰。BGE CLS pooling；Qwen last pooling；分别使用官方风格的查询指令。',
 '- 目录按8项/请求，查询1项/请求；预热后计时。P50/P95为67个业务查询HTTP往返编码时间，不含向量库或LLM生成。单轮小样本，不能代表稳定压测。',
 '- 峰值为容器cgroup memory.peak，包含文件缓存等，不是纯模型权重或独立RSS。启动耗时单列，下载不计入。',
 '- 精确余弦搜索，向量逐项L2归一化，未使用pgvector ANN、关键词融合、reranker或阈值筛选。',
 '- 每条输入先通过服务tokenizer核对长度；未截断；BGE上下文512，Qwen测试配置2048，不是其能力上限。',
 '- 每个模型额外检查同文本单条与批量编码余弦 >0.999；这只是部署一致性检查，不等同于对原始HF权重逐值校验。',
 '', '## 5. 双侧描述组 Top1 错误案例','',
 '|模型|问题|可接受类型|实际第一名|正确类型最优排名|','|---|---|---|---|---:|']
 for k,rows in rankings.items():
  for r in rows:
   if r['catalog']=='descriptions' and r['query_mode']=='context' and r['kind']=='single' and r['rank']>1:
    lines.append(f"|{LABELS[k]}|{r['query']}|{', '.join(r['targets'])}|{r['top10'][0]['name']}|{r['rank']}|")
 lines+=['','## 6. 多目标漏召回明细（双侧描述，Top10）','','|模型|问题|仍未召回的目标及排名|','|---|---|---|']
 for k,rows in rankings.items():
  for r in rows:
   if r['catalog']=='descriptions' and r['query_mode']=='context' and r['kind']=='multi':
    missing=[f'{n}（{rank}）' for n,rank in r['all_target_ranks'].items() if rank>10]
    lines.append(f"|{LABELS[k]}|{r['query']}|{', '.join(missing) or '无'}|")
 lines+=['','## 7. 适用边界与可复核材料','',
 '- [描述核验](description-review.md)：公开资料能核对通用概念，不能代替客户表字典；未知单位、枚举与字段映射没有强行确定。',
 '- [完整数据集](dataset.json)：全部描述、问题、可接受目标。评测前冻结；没有根据结果修改问题或标准答案。',
 '- 原始文件只有名称，不存在真实报文值、表名、客户字段描述。所有测试输入是合成业务说明，不证明仅凭真实数字值可以完成分类。',
 '- 同一助手编写定义和问题，有合成集偏差；61题不覆盖全部100类型，模糊字段作为候选干扰项保留。两种同义边界采用可接受目标集合，详见描述核验。',
 '- small采用社区F16转换（已核对CLS/SEP为101/102），Qwen采用官方F16。社区base文件BOS/EOS键重复且冲突，无法加载，最终采用BAAI官方权重经llama.cpp b8576重新转换的F16；转换后CLS/SEP为101/102。',
 '- 下载固定revision、文件SHA256、实际运行命令、镜像ID、数据集SHA256保存在各模型summary.json。旧mmap配置的试跑保存于results-mmap，不混入本报告。',
 '- 结果目录各模型保存 vectors.json、rankings.json、timings.json、token_lengths.json、server.log、summary.json；failures.csv可筛选全部未命中案例。',
 '- 本次不经过Docling：TXT中每行本来就是一个类型。未来PDF/Word由Docling解析后，仍需显式构建类型定义，不能把解析块直接当完整分类标准。','']
 (ROOT/'REPORT.md').write_text('\n'.join(lines))
 with (ROOT/'failures.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(['model','catalog','query_mode','query_id','query','targets','rank','top1','top5'])
  for k,rows in rankings.items():
   for r in rows:
    if r['kind']=='single' and r['rank']>1:w.writerow([k,r['catalog'],r['query_mode'],r['query_id'],r['query'],','.join(r['targets']),r['rank'],r['top10'][0]['name'],','.join(x['name'] for x in r['top10'][:5])])
 print('Wrote REPORT.md and failures.csv')

if __name__=='__main__':main()
