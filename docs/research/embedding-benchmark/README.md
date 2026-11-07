# 电力数据类型向量检索测试

比较 BGE-small-zh-v1.5 / BGE-base-zh-v1.5 / Qwen3-Embedding-0.6B 在100项电力类型目录中的检索能力。见 [报告](REPORT.md) 和 [描述核验](description-review.md)。

输入来源：`/Users/mac/Downloads/电力数据类型.txt`。原文件不修改。

## 本次结果（2026-11-03）

100项候选目录；61个合成识别用例；6个多目标召回用例。待识别输入均带业务说明时：

|模型|目录仅名称 Top1|目录补定义 Top1|补定义 Top5|查询 P50|查询 P95|
|---|---:|---:|---:|---:|---:|
|BGE-small-zh-v1.5|63.9%|80.3%（49/61）|98.4%（60/61）|15.7 ms|36.9 ms|
|BGE-base-zh-v1.5|78.7%|83.6%（51/61）|100%（61/61）|64.8 ms|189.4 ms|
|Qwen3-Embedding-0.6B|82.0%|86.9%（53/61）|100%（61/61）|163.7 ms|508.4 ms|

初步建议base用于候选召回。Qwen本次Top1多判对2题，但消耗更大；小样本不能证明显著优势。所有模型补定义后，多目标Top10均只有5/6题完全找齐，Top20为6/6。描述不是越多越好：Qwen仅名称目录的多目标Top10原本为6/6，补定义后反而漏掉一项。

测量条件：Apple M1，Docker ARM64，4CPU/4线程，F16，统一llama.cpp b8576；精确余弦检索，不含生成模型、reranker或ANN。查询耗时为67次业务查询的单轮HTTP编码时间，不是生产压测结果。

## 归档文件

|文件|内容|
|---|---|
|[REPORT.md](REPORT.md)|指标定义、四组对照、完整召回、性能和逐题错误|
|[description-review.md](description-review.md)|100个类型的描述、公开依据和客户待确认项|
|[dataset.json](dataset.json)|评测前固定的候选定义、问题和目标标注|
|[failures.csv](failures.csv)|四组对照的Top1错误，可用Excel筛选|
|[snapshot-20261103.json](snapshot-20261103.json)|三个模型的指标、耗时、模型和数据集哈希归档|
|[source-types.txt](source-types.txt)|原始类型列表副本，与原文件SHA256一致|
|results/|本机完整向量、排名、计时及服务日志；大文件不纳入Git|

这次直接使用TXT类型列表，没有经过Docling；因此结果验证的是类型语义检索，不是PDF/Word解析或长文档切块效果。

## 复现

Python仅用标准库。三个GGUF固定revision见models.json；下载到models/，实际SHA256见results/*/summary.json。本地镜像不上传注册表。

```sh
cd /Users/mac/Developer/src/python/privacy-react-demo/docs/research/embedding-benchmark
python3 build_dataset.py
docker build -t privacy-embedding-benchmark:b8576 .
python3 -u run.py
python3 report.py
```

现有dataset.json已经固定，重跑原实验可以跳过build_dataset.py；该脚本当前读取上面的Downloads原路径。source-types.txt是独立归档副本。重新生成测试集或修改描述后，应另存一轮结果，不能和本次结果混合。

Dockerfile使用现有Go项目llamacpp镜像配置中的同一个ARM64上游版本server-b8576，独立包装embedding启动参数。未修改原有生成服务的Dockerfile/模型/入口。

三个模型统一使用 `--no-mmap`。初次mmap试跑因Docker宿主文件挂载下Qwen速度异常而中止，该轮保存在results-mmap，不参与最终比较。

### base转换

社区base GGUF存在重复且冲突的BOS/EOS元数据，不能加载。实际改从BAAI官方固定revision下载config/tokenizer/vocab、pytorch_model.bin和1_Pooling/config.json，用同版本转换器输出F16。原始失败文件保留，未直接修改权重或手工猜测特殊token。

```sh
# llama.cpp固定tag b8576；依赖环境需有torch/transformers/numpy等转换器依赖
python llama.cpp/convert_hf_to_gguf.py hf-base \
  --outfile models/bge-base-zh-v1.5-official-f16.gguf --outtype f16
```

官方来源revision见base-official-source.json，实际源权重SHA256和转换器commit见models.json；日志convert-base.log。现有转换环境为document-parser-benchmark/.venv-docling，未更改业务依赖。

运行器逐模型启动本地端口18087，4CPU，F16，不使用GPU；结束后停止自己创建的容器。已有同名容器会导致启动失败，不会主动删除其他进程。完整模型结果存在则跳过；要重新测试请先移走对应results子目录。不得把不同dataset.json的结果混合比较。

## 两侧描述对照

- 候选目录：仅名称 / 名称＋业务定义。
- 待识别输入：缺少上下文的字段 / 补业务说明后的字段。
- 61个单目标问题，共4种组合；6个多目标问题，用明确描述分别检索两种目录。
- 原文件不是完整客户数据字典，描述以名称语义为基础，明确保留不确定性。基于公开材料核对电价/电费、电力/电量和许可证等概念，不擅自认证客户字段。
- 查询instruction：BGE中文检索前缀，Qwen英文任务instruction；所有文本在本地处理，网络仅下载公开模型及查阅通用定义。

## 模型来源

- https://huggingface.co/CompendiumLabs/bge-small-zh-v1.5-gguf
- https://huggingface.co/CompendiumLabs/bge-base-zh-v1.5-gguf
- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF
- BGE原模型/CLS说明：https://huggingface.co/BAAI/bge-base-zh-v1.5

不比较不同模型的原始相似度阈值；同一阈值没有跨模型可比性。不将TopK候选命中当最终业务分类准确率。
