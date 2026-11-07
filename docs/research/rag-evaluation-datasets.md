# RAG 评测数据集调研

调研日期：2026-11-07。本文记录选型依据，不表示数据集已下载、接入或完成验证。当前实现范围以 `TASKS.md` 和 [评测说明](../../evals/rag/README.md) 为准。

## 要解决的问题

比较文档切分大小与重叠、Embedding 模型与输入长度、标题和正文的拼接方式时，需要固定测试问题与证据，才能判断改动是否有效。当前优先考虑中文资料和中文问题，英文数据集作为后续参考。

评测链路：原始文件 → 解析正文 → 切块 → Embedding／检索 → 拼接上下文 → 生成回答。

资料来自真实世界，不代表问题来自真实用户；人工审核过，不代表问题完全由人工编写。按页标注证据，也不等于预先固定了系统的检索块。

## 数据来源、粒度和评测阶段

以下是本轮讨论的候选集合，不是所有公开 RAG 数据集的完整目录。链接指向数据卡或官方项目；同名数据集的不同版本、子集不能直接混用分数。

| 数据集 | 语言 | 原始资料来源 | 问题、答案与标注来源 | 提供粒度／是否切好 | 主要评测阶段 |
| --- | --- | --- | --- | --- | --- |
| [Double-Bench](https://huggingface.co/datasets/Episoode/Double-Bench) | 中英等多语言 | 学术资料、CommonCrawl、Wikipedia 等，包含 PDF、扫描件、幻灯片、网页 | 迭代生成与知识图谱引导构造单跳／多跳问题；证据经人工核验 | 文档包、OCR 数据、问答、文档路径与证据页码；未固定项目的 Chunk | 文档／页面检索、多跳证据检索、最终问答 |
| [DuRetrieval（MTEB 版本）](https://huggingface.co/datasets/mteb/DuRetrieval) | 中文 | 商业搜索引擎的查询与网页段落 | 开发／测试集汇集多个检索器结果，再人工标注相关性 | 固定段落、查询、相关段落 ID；基本已切好 | Embedding、召回、排序 |
| [LongBench v1](https://huggingface.co/datasets/zai-org/LongBench) | 中英 | 汇集已有数据集并补充构建任务，涉及论文、新闻、会议等长文本及代码 | 因子任务而异，包含沿用的人工问答、新标注与合成任务 | 已整理的长 context、问题、答案；不是统一的原始文件库或检索块集 | 长上下文理解、最终回答；可改造成 RAG 实验 |
| [CRUD-RAG](https://github.com/IAAR-Shanghai/CRUD_RAG) | 中文 | 新闻文章；官方提供 8 万余篇新闻用于检索库 | 按续写、问答、纠错、摘要构建任务；问答部分使用 GPT-4 生成单／多文档问题与答案 | 新闻正文和任务样本，可自行切分；不是原始 PDF 评测集 | 检索、上下文长度、知识库构建等对最终任务效果的影响 |
| [QASPER](https://huggingface.co/datasets/allenai/qasper) | 英文 | NLP 论文，全文从 S2ORC 获取 | NLP 从业者阅读标题和摘要后提问；回答者阅读全文，给出答案并标注证据 | 章节／段落化全文、问答、证据段落；已解析，可重新切块 | 证据选择、检索、论文问答 |
| [Open RAG Bench](https://huggingface.co/datasets/vectara/open_ragbench) | 主要英文 | arXiv 论文 PDF | OCR 解析并按章节整理，用 gpt-4o-mini 生成问答和过滤；另有干扰文档 | PDF 下载链接、解析章节、问答、文档／章节相关性标注 | 文档与章节检索、端到端 RAG；可比较切分方案 |
| [FinanceBench](https://huggingface.co/datasets/PatronusAI/financebench) | 英文 | 上市公司公开财务文件 | 金融领域人员参与构建问题、答案与证据；包含指标提取与数值推理，不能把所有题型视为同一种构造过程 | 原文链接、问答、证据文本与页码；公开子集 150 题，未固定 Chunk | 财报证据检索、表格／数值问答 |
| [ViDoRe V3](https://huggingface.co/collections/vidore/vidore-benchmark-v3) | 多语言；文档语言和查询翻译语言须分别核对 | 财报、工业、科研、医药等领域文档 | 人工与模型混合出题；模型预筛，人工标相关页、答案与证据框，再质检及合并答案 | PDF、页面图像、OCR Markdown、页面相关性与证据框，以页为主要单元；具体内容以子集为准 | 视觉／文本页面检索、证据定位、最终回答 |
| [OmniDocBench](https://huggingface.co/datasets/opendatalab/OmniDocBench) | 含中英等 | 论文、报告、教材、报纸等文档页面 | 人工筛选，结合辅助标注、人工标注、专家质检和模型质检 | 页面、PDF 切片及文本／表格／公式／阅读顺序标注；不是问答集 | 文档解析、OCR、表格与版式识别 |

构建过程补充来源：[Double-Bench 项目](https://double-bench.github.io/)、[DuReader-Retrieval 原论文](https://aclanthology.org/2022.emnlp-main.357/)、[CRUD-RAG 论文](https://arxiv.org/abs/2401.17043)、[FinanceBench 发布说明](https://www.patronus.ai/research/financebench)、[ViDoRe V3 混合标注流程](https://huggingface.co/blog/QuentinJG/introducing-vidore-v3)。

## 如何据此做决策

| 要决定什么 | 应固定什么 | 所需数据与候选 | 观察指标与边界 |
| --- | --- | --- | --- |
| 哪个解析器更好 | 原文件与评测规则 | 原文件及正文／表格／顺序标注；OmniDocBench | 文本识别、表格结构、阅读顺序等；不混入检索与生成 |
| 块大小、重叠多少合适 | 解析正文、模型、问题、检索预算 | 完整正文及独立于 Chunk ID 的证据；Double-Bench、QASPER、Open RAG Bench、FinanceBench | 证据覆盖、排名、耗时；页级命中不能代表证据完整 |
| Embedding 模型哪个好 | 文本块、问题、检索参数 | 固定语料与相关性标注；DuRetrieval | Recall@K、MRR、nDCG；结果不能代表 PDF 解析质量 |
| 标题和正文怎样拼接 | 切块边界、模型、问题 | 同一批块与证据标注 | 证据召回和排名，同时检查输入截断 |
| 最终回答是否改善 | 问题、参考答案，明确上下文来源 | LongBench、CRUD-RAG 或带答案的文档集 | 正确性、忠实性和引用；最终分数无法独立定位解析、检索或生成故障 |

切分没有通用的“正确块边界”。本项目应通过下游证据检索效果评估切分，而不是仅比较切出的块长得是否相同。不同大小的块在同一 Top K 下可能返回不同文本量，应同时记录返回 token 数或补充固定上下文预算的比较。

## 当前建议与待确认事项

- 中文文件评测优先考察 Double-Bench：先筛中文、单跳、纯文本证据题，试跑约 30～50 题。需要验证原文件形态、问题与文档语言、页码基准及切块到证据页的映射，尚未完成样本核验。
- 若先比较 Embedding，DuRetrieval 接入成本更低，但固定段落不能替代长文档切分评测。MTEB 子集与原始 DuReader-Retrieval 的规模不同，应记录具体版本。
- 英文切分实验可从 QASPER 的结构化全文开始，减少解析干扰；需要从 PDF 开始时，再考虑 Open RAG Bench 或 FinanceBench。
- LongBench v1 是长上下文基准。改造成跨文档检索实验后，应明确语料范围和改造方法，不能直接把结果与原基准分数比较。
- Double-Bench 的 OCR 内容不是自动可信的人工解析标准。可用检索／问答分数观察解析影响，但不能直接据此声称测得解析准确率。
- 每次比较固定问题、标注、语料范围和数据版本。保留干扰资料；不能只把正确答案所在段落放入库。缩小语料后的分数只代表这个子集。
- 当前评分器使用文件名和证据原文包含关系。页级／章节级／段落 ID 标注需要对应的评分适配，不能原样套用，也不应把多个替代证据误当作必须全部命中的证据。
- 当前模型是中文 BGE。英文实验需明确模型语言适用范围，不能直接用英文结果推断中文业务效果。

数据尚未下载。调研时 Double-Bench 文档包约 23.4 GB，另提供 OCR 包。Double-Bench、Open RAG Bench、FinanceBench 数据卡标为 CC BY-NC 4.0；正式引入企业使用前需要核对所选版本与原始资料条款，不能把代码许可等同于数据许可。

本轮仅形成候选清单；不引入新的评测框架，不承诺接入全部数据集。明确首批数据范围后，再在 `TASKS.md` 排定实现。
