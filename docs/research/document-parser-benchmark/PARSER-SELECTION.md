# 文档解析库综合对比与选型

记录日期：2026-11-03。本文整理本项目已有实测与调研，不代表已经完成解析器迁移。

## 当前结论

**推荐采用 Docling 作为统一解析入口和文档模型。**

本项目目前更看重统一模型、API 综合性和后续管理，性能不是主要矛盾。选型目的在于减少自行维护的格式适配分支，而不是追求最短解析耗时或最高 Star 数。

初期只处理 Word、Excel，不需要 PDF 视觉模型。后续增加普通电子 PDF 时先使用 Native 模式，遇到复杂版面、表格或扫描件，再单独评估模型辅助解析。

## 综合对比

| 对比项 | 独立库组合：pypdf / python-docx / openpyxl | Unstructured | Docling |
|---|---|---|---|
| 统一调用入口 | 需要自己封装 | `partition()` | `DocumentConverter` |
| 统一返回模型 | 需要自己设计 | `Element` 列表 | `DoclingDocument` |
| API 简洁性 | 各库简单，组合后适配分支较多 | 基础调用最直接 | 初始化稍多，整份文档的操作较统一 |
| 文档层级表达 | 需要自己组织 | 元素及关联元数据 | 统一文档结构和层级引用 |
| 表格处理接口 | 各格式不同 | 表格元素，通常读取 HTML | 表格对象、单元格结构及导出接口 |
| 导出能力 | 分别适配或自己拼接 | 元素序列化及格式转换工具 | Markdown、JSON、HTML 等统一导出 |
| Word / Excel 模型需求 | 不需要视觉模型 | 常规解析不需要视觉模型 | 不需要 PDF 视觉模型 |
| 无模型 PDF | pypdf | `fast` 模式 | `Native` 模式 |
| 复杂 PDF 扩展 | 另接 OCR、版面工具 | 可选 `hi_res`、OCR | 可选标准模型流水线、OCR |
| 依赖和部署 | 可按格式精简 | 依赖较多 | 标准安装依赖较多 |
| 自己维护的适配代码 | 较多 | 较少 | 较少，适合围绕统一文档对象开发 |
| 文件分类、版本、权限、入库管理 | 自己实现 | 自己实现 | 自己实现 |
| 对当前项目的适合程度 | 能用，但不符合统一优先的偏好 | 适合围绕元素列表处理 | 更符合统一模型和后续管理的取舍 |

“统一模型更便于管理”是工程判断，不是已经测得的故障率结论。统一框架可以减少自己的适配分支，但不能保证解析器没有 bug。

## 实测汇总

环境：Apple M1、16 GiB RAM；Unstructured 0.27.36、Docling 2.146.0。各测试 73 份相同原文件，另有控制样例。

| 指标 | 独立库组合 | Unstructured | Docling |
|---|---:|---:|---:|
| 成功且非空 | 48/73 | 56/73 | 50/73 |
| 失败或超时率 | 31.51% | 17.81% | 28.77% |
| Word 文本单元召回率 | 99.969% | 99.979% | 100% |
| Word 表格原位结构匹配率 | 99.969% | 100% | 99.875% |
| Excel 文本值严格匹配率 | 100% | 99.007% | 100% |
| Excel 文本召回率：统一换行后 | 100% | 100% | 100% |

将现有实现按底层库展开，性能如下：

| 格式 | 三方共同成功文件数 | pypdf | python-docx | openpyxl | Unstructured | Docling |
|---|---:|---:|---:|---:|---:|---:|
| PDF | 15 | 0.441 秒 | — | — | 2.184 秒 | 1.249 秒 |
| Word DOCX | 16 | — | 0.040 秒 | — | 0.266 秒 | 0.407 秒 |
| Excel XLSX | 17 | — | — | 0.021 秒 | 0.390 秒 | 0.015 秒 |

以上为解析耗时中位数，包含本项目适配逻辑，不是独立库内核性能排名。PDF 主对比不启用 OCR，Docling 使用 Native。前两者沿用之前实测，后台负载不同，不能据微小耗时差断言稳定性能优势。

### 内容指标的边界

- 失败率包含不支持旧格式、缺少 LibreOffice、损坏文件、大小限制及超时，不是内容错误率。
- 内容对比仅统计三方均成功的 16 份 Word、17 份 Excel；标准来自原始 Office XML。
- Word 文本召回检查原文单元是否完整出现，不惩罚所有额外输出，也不证明阅读顺序完全正确。
- Excel 真实文件指标只覆盖文本值，不证明数值、公式和行列对应关系全部正确。Unstructured 的 48 项严格匹配差异来自换行表示，不能当成丢失 48 个单元格。
- Docling 的 12 个表格原位结构差异包括：9 个单格代码表转为代码内容，3 个嵌套表格编号移至单独子表；不能解释成丢失了 12 段文字。
- 控制样例中，Docling 保留了 `00123`、`0`、`False` 和合并表头，但没有保留未缓存公式的原式。需要保留公式的业务应单独验证或补充适配。
- 两页定向异常 PDF 的检查不代表整体 PDF 准确率。Docling Native 仍出现过“页面”变成“顸面”的错误。

详细数据见 [三方测试报告](COMPARISON-THREE.md)、[内容保真测试](accuracy/REPORT.md) 和 [字符检查报告](CHARACTER-AUDIT.md)。

## 社区与生态参考

2026-11-03 GitHub API 查询快照：

| 指标 | Unstructured | Docling |
|---|---:|---:|
| GitHub Star | 15,675 | 70,052 |
| 本次核对的 7 个知名项目中，确认官方集成或主仓库接入的数量 | 5 | 6 |

这是本次核验范围，不是全网引用总数，也不代表默认使用或生产部署数量。未确认不代表没有；社区插件不计入上面的官方集成数。

| 项目 | Unstructured | Docling |
|---|---|---|
| LangChain | 官方集成目录支持 | 官方集成目录支持 |
| LlamaIndex | Reader 集成 | Reader 集成 |
| Haystack | Converter 集成 | Converter 集成 |
| Open WebUI | 主仓库有调用 | 主仓库有接入 |
| Dify | 主仓库有调用 | 本次确认的是社区插件 |
| RAGFlow | 未确认 | 官方解析器选项 |
| Langflow | 未确认 | 官方组件集成 |

核验来源：

- [Unstructured 仓库](https://github.com/Unstructured-IO/unstructured)、[Docling 仓库](https://github.com/docling-project/docling)。
- [LangChain Loader 目录](https://github.com/langchain-ai/docs/blob/main/src/oss/python/integrations/document_loaders/index.mdx)。
- [LlamaIndex Unstructured Reader](https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-file/llama_index/readers/file/unstructured/README.md)、[Docling Reader](https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-docling/README.md)。
- [Haystack Converters](https://docs.haystack.deepset.ai/docs/3.3/converters)。
- [Open WebUI Loader 源码](https://github.com/open-webui/open-webui/blob/main/backend/open_webui/retrieval/loaders/main.py)。
- [Dify Unstructured 源码](https://github.com/langgenius/dify/blob/main/api/core/rag/extractor/unstructured/unstructured_doc_extractor.py)、[Docling 社区插件](https://marketplace.dify.ai/plugin/s20ss/docling)。
- [RAGFlow Parser 配置](https://github.com/infiniflow/ragflow/blob/main/docs/guides/agent/ingestion_pipeline/configure_parser_component.md)。
- [Langflow Docling 组件](https://docs.langflow.org/1.12.0/bundles-docling)。

## 落地边界

建议采用：**Docling 负责解析与文档结构，业务模块负责管理与入库生命周期。**

| 层次 | 职责 |
|---|---|
| 解析层 | 统一调用 Docling，保留原始 `DoclingDocument` JSON；记录解析器版本、配置和错误 |
| 管理层 | 文件 ID、业务分类、文档版本、权限、上传和解析状态 |
| 切块层 | 切块配置、预览结果、块 ID、来源引用；通过文件 ID 和解析版本关联原文 |
| 入库层 | Embedding 与 pgvector 写入、入库状态，以及更新或删除时的索引同步 |

不再另造一套同等复杂的文档模型；可保留薄的业务接口，避免业务页面直接依赖解析器内部细节。原文件、解析结果和管理数据分别保存并建立关联。

保留嵌套表格、公式、特殊字符、换行和空扫描页等样例作为升级回归集。如果以后必须严格保留 Excel 公式、复杂表头或某类格式，而 Docling 无法满足，再按具体需求补充适配；不因预想问题提前接入多个解析框架。

接口参考：[Unstructured Partitioning](https://docs.unstructured.io/open-source/core-functionality/partitioning)、[Docling Pipeline Options](https://docling-project.github.io/docling/reference/pipeline_options/)。
