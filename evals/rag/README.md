# RAG 检索评测

用 promptfoo 执行和查看检索评测，Python 复用 `knowledge/`；不 fork promptfoo，不接入 Ragas 或 Langfuse。

当前是 BGE-base、现有切分和拼接规则的基线，演示语料由本项目编写，5 个问题只用于跑通流程，不代表真实业务效果。没有答案生成或模型裁判，默认不调用收费模型。

## 运行

在项目根目录执行，需要根 `.env` 的数据库配置、本地 BGE 模型与 tokenizer。CLI 运行在宿主机，使用当前 Python 环境；不需要启动 Web 应用。

```sh
uv sync --locked
npm install -g promptfoo@0.125.1
docker compose up -d embedding
uv run python -m evals.rag.prepare
uv run python -m evals.rag.run
# 查看本机 CLI 保存的实验历史
promptfoo view --port 15501
```

`prepare` 仅上传 `corpus/*.txt` 到专用知识库 `__eval_fermata_demo_v1`，使用 400 token / 40 overlap，重复执行跳过相同文件，不删除或替换已有文档。修改语料后，应先在知识管理页删除该评测库中旧文件再准备；不要在此库中手工编辑切块或混入其他资料。它与业务库按名称隔离，共用现有数据库，不是独立数据库。

`run` 检查文档哈希及模型版本后，只执行检索，关闭缓存和自动分享。每次保存到 `results/<UTC时间>/`：逐题结果、配置与评分脚本副本、语料哈希、模型版本、索引批次和处理参数、代码版本及源码哈希。执行失败会保留非零退出码，不能当作“检索无结果”。

结果同时写入本机 promptfoo 历史。Compose 的 `15500` 页面使用独立的容器数据卷，不会自动看到本机 CLI 历史；本版用 `15501` 的本机 viewer 查看，避免把两处存储混为一谈。不会自动上传到公共分享服务。

## 文件与测试集

| 文件 | 用途 |
| --- | --- |
| `corpus/` | 可公开提交的演示原文 |
| `cases.yaml` | 问题、参考答案、预期证据 |
| `promptfooconfig.yaml` | Provider、Top K 与评分配置 |
| `provider.py` | 调用现有检索，返回 hits、context 和运行信息 |
| `score.py` | 根据原文证据计算覆盖率和首次命中排名 |
| `prepare.py` / `run.py` | 准备演示索引 / 运行并保存实验 |

新增案例时填写 `query`、`reference` 与 `expected_evidence`。证据使用文件名和原文短句，不使用切分后会变化的 Chunk ID。当前 `reference` 仅作人工阅读参考，评分依据是 `expected_evidence`；两者须人工保持一致。

数据集和配置纳入 Git，`results/` 默认忽略。有价值的运行可精选后显式提交；真实业务资料需先去除敏感信息。不要把模型生成的答案直接作为人工标准答案。

## 指标与边界

- `evidence_coverage`：在返回的父上下文中找到的标注证据数 / 标注证据总数。要求文件名相同且含原文，忽略空白差异；全部找到才算此题通过。
- `first_evidence_rr`：第一条含有标注证据的返回结果排名的倒数，未命中为 0。多证据问题仍须看覆盖率。
- 每题保留检索分数、命中子块、父上下文、截断标记和耗时，便于查看漏掉了什么。

这里的 Top K 是去重前的候选子块数；评分检查实际返回的父上下文，因此条数可能少于 K。这些是确定性的原文匹配指标，不是 promptfoo 的模型裁判 `context-recall`，也不衡量生成答案正确性。原文改写或跨块才能拼出的证据可能无法匹配，需审阅失败案例。当前检索无拒答阈值，不用“返回空列表”代表无答案能力。

多切分方案、拼接策略、其他维度的 Embedding 模型及裁判评分尚未实现，见 [任务清单](../../TASKS.md)。先积累真实问题与证据，再扩展对比方案。

接口依据：[Python provider](https://www.promptfoo.dev/docs/providers/python/)、[Python 评分器](https://www.promptfoo.dev/docs/configuration/expected-outputs/python/)。
