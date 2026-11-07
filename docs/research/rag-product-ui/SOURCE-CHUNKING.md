# RAG 产品的文档解析与切块：源码核查

核查日期：2026-11-03。对应 index.html 中的六个产品。克隆了 Dify、FastGPT、MaxKB、RAGFlow 的官方仓库默认分支，depth=1；位于 repos/。完整提交号及分支见 source-snapshots.json。只做源码阅读，没有安装或启动这些产品，也没有用客户文档评测。

千帆、百炼是此次调研的云产品，未取得其托管知识库对应的完整实现源码，本报告不猜测其内部切块库。厂商发布的其他开源项目不自动等同于云产品实现。当前默认分支也不等于此前截图使用的版本。

## 核心结论

这些产品没有统一采用某一种“解析+切块”库。文件解析通常调用已有库或外部服务，切块则大量使用产品仓库内的策略代码。它们也不都先生成相同的 Block 树；有的先统一成文本或 Markdown。

| 产品 | 本轮确认的解析路径 | 本轮确认的切块实现 |
|---|---|---|
| FastGPT | PDF：@llamaindex/liteparse-wasm，特定加载故障回退 PDF.js；DOCX：mammoth 转 HTML 再转 Markdown；XLSX：xlsx/SheetJS，papaparse 用于 CSV 表达 | 自写 TypeScript splitText2Chunks；标题、分隔符、标点递归拆分，合并短段，overlap；表格有专用逻辑 |
| MaxKB | PDF：pypdf；DOCX：python-docx；XLSX：openpyxl | 自写 SplitModel：标题/正则层级+长度限制；之后可用 MarkChunkHandle 把段落再拆成检索小块 |
| Dify | PDF：pypdfium2；DOCX：python-docx；Excel：openpyxl/pandas；部分其他格式走 Unstructured | 仓库内部 RecursiveCharacterTextSplitter 及增强/固定分隔符版本；普通块、父子块等处理器 |
| RAGFlow | 当前默认分支为 Go 路径：DeepDOC；另有 MinerU、Docling 外部解析适配；DOCX 使用 office_oxide，XLSX 使用 excelize | 自写 GeneralChunker、TokenChunker、TitleChunker 等；按格式、标题、token 和分隔符处理，保留定位/表格等信息 |

注意：表格只列已读的内置及相关适配路径，不代表插件市场或商业版所有能力。Unstructured 名字出现在 Dify 配置中，也不代表所有文件都经过它。

## FastGPT：标题与表格策略最值得看

源码入口：
- [预览 API](repos/FastGPT/projects/app/src/pages/api/core/dataset/file/getPreviewChunks.ts)：读取源内容 → rawText2Chunks → 返回预览；本路径预览截取前 10 块。
- [rawText2Chunks](repos/FastGPT/packages/service/core/dataset/read.ts)：先判断是否触发切块；普通模式交给 worker；智能模式可委托外部 Sangfor 服务，不能和本地算法混为一谈。
- [切块核心 textSplitter.ts](repos/FastGPT/packages/service/common/string/textSplitter.ts)：splitText2Chunks、commonSplit、markdownTableSplit。
- [PDF 路由](repos/FastGPT/packages/service/worker/readFile/extension/pdf.ts)；[LiteParse 适配](repos/FastGPT/packages/service/worker/readFile/utils/LiteParse/index.ts)；[DOCX](repos/FastGPT/packages/service/worker/readFile/extension/docx.ts)；[XLSX](repos/FastGPT/packages/service/worker/readFile/extension/xlsx.ts)。

处理特点：
1. 自定义边界、Markdown 标题、代码块/表格、空行、换行、句子标点逐级处理。
2. 小片段合并；超长内容继续细分；部分边界禁止 overlap，不能理解为所有块机械重复固定长度。
3. Markdown 表格按行拆分，每块重新携带表头及分隔行；不是随意按字符截断整张表。
4. XLSX 根据实际合并区域回填值，再清理空行空列并转表格；不同 sheet 用内部标记分隔。
5. 切块器支持 char/token 两种计量，默认是字符路径；不能只看到参数 chunkSize 就断言单位为 token。
6. 默认 PDF LiteParse 路径关闭 OCR；PDF.js 只在 WASM 加载/初始化类故障时回退，不是所有解析错误都回退。

## MaxKB：段落与检索小块是两层

源码入口：
- [文档导入/切分调度](repos/MaxKB/apps/knowledge/serializers/document.py)。
- [SplitModel](repos/MaxKB/apps/common/utils/split_model.py)：parse_to_tree、parse、smart_split_paragraph。
- [PDF](repos/MaxKB/apps/common/handle/impl/text/pdf_split_handle.py)、[DOCX](repos/MaxKB/apps/common/handle/impl/text/doc_split_handle.py)、[XLSX](repos/MaxKB/apps/common/handle/impl/text/xlsx_split_handle.py)。
- [工作流文档切分节点](repos/MaxKB/apps/application/flow/step_node/document_split_node/impl/base_document_split_node.py)：_process_split_result 中设置 paragraph['chunks']。
- [text_to_chunk](repos/MaxKB/apps/common/chunk/__init__.py)、[MarkChunkHandle](repos/MaxKB/apps/common/chunk/impl/mark_chunk_handle.py)。

处理特点：
1. PDF 优先尝试目录、内部链接等线索；无目录路径读取文本，并以字号相对正文的差异生成标题标记。这是启发式，不是模型保证正确的语义识别。
2. DOCX 读取段落/表格并转为适合分段的文本；SplitModel 按标题正则构造层级，最终输出 title/content 等段落数据。
3. 超长段落在长度范围内找句末标点，找不到再按长度拆。这里主要按字符长度。
4. XLSX 用表头加若干数据行拼 Markdown，达到 limit 时另开一段并补表头；单行过长不应假定总能满足硬上限。
5. 工作流路径在段落基础上调用 text_to_chunk，MarkChunkHandle 使用标点/换行正则与长度限制再切一层。展示段落和向量检索的小块不必相同。

## Dify：递归切分和父子块

源码入口：
- [格式选择](repos/dify/api/core/rag/extractor/extract_processor.py)。
- [PDF](repos/dify/api/core/rag/extractor/pdf_extractor.py)、[Word](repos/dify/api/core/rag/extractor/word_extractor.py)、[Excel](repos/dify/api/core/rag/extractor/excel_extractor.py)。
- [选择切块器 _get_splitter](repos/dify/api/core/rag/index_processor/index_processor_base.py)。
- [增强及固定分隔符切块器](repos/dify/api/core/rag/splitter/fixed_text_splitter.py)、[内部递归切块实现](repos/dify/api/core/rag/splitter/text_splitter.py)。
- [普通段落处理器](repos/dify/api/core/rag/index_processor/processor/paragraph_index_processor.py)、[父子块处理器](repos/dify/api/core/rag/index_processor/processor/parent_child_index_processor.py)。

处理特点：
1. 提取 → CleanProcessor 清洗 → splitter.split_documents → 索引，不是直接把每页当最终 chunk。
2. 自定义模式先按指定分隔符分段，过长才继续递归；候选边界包含空行、中文句号、英文句号空格、空格等。
3. 支持长度和 overlap。当前 from_encoder 实际返回 len(text)，即字符计量；参数仍叫 max_tokens，不能据变量名判断实际单位。
4. 父子模式先形成父块，再拆子块；load 中对子块建立向量索引。
5. RecursiveCharacterTextSplitter 在本仓库内实现，不是当前直接 import langchain_text_splitters 的调用；没有进一步考证其历史代码来源。
6. 本轮跟踪的是 core/rag 内置路径；新知识流水线可以有插件化节点，不能据此枚举全部插件的解析方案。

## RAGFlow：解析与切块显式分工

当前快照已以 Go 为主，不能只拿旧版 Python 的 rag/app/naive.py 当当前主链路。

源码入口：
- [Parser 组件](repos/ragflow/internal/ingestion/component/parser.go)。
- [PDF 方法和配置](repos/ragflow/internal/parser/parser/pdf_parser_common.go)、[MinerU 适配](repos/ragflow/internal/parser/parser/pdf_parser_mineru.go)、[Docling 适配](repos/ragflow/internal/parser/parser/pdf_parser_docling.go)。
- [DOCX](repos/ragflow/internal/parser/parser/docx_parser.go)、[XLSX](repos/ragflow/internal/parser/parser/xlsx_parser.go)。
- [GeneralChunker](repos/ragflow/internal/ingestion/component/chunker/general.go)：按 PDF、DOCX、Markdown、电子表格分别调策略。
- [TokenChunker](repos/ragflow/internal/ingestion/component/chunker/token.go)：分隔符模式、token 合并模式、overlap 等。
- [TitleChunker](repos/ragflow/internal/ingestion/component/chunker/title.go)：按标题分组/层级策略。
- [Tokenizer/向量生成](repos/ragflow/internal/ingestion/component/tokenizer.go)。

处理特点：解析器输出带类型/位置/媒体信息的内容，chunker 再决定如何组合成检索单元。支持 MinerU 或 Docling，并不意味着把它们返回的原始块直接拿来当最终检索块。不同策略存在结构完整性与严格长度上限的取舍，不能将某个模式的限制推广至所有模式。

## 对你这个项目的建议

先复用成熟解析器，同时只保留少量明确的切块规则：标题路径随块保留、短段合并、超长段再拆、表格分行后补表头、保存来源引用。复杂布局识别交给解析器，业务特有的表头/版本/材料用途由自己的应用处理。

不要因为产品用了自写切块器就照搬整套代码。现成切块器可作为起点；只有客户样本证明需要时再补特殊处理。也不要因为引入 Docling，就认为所有清洗和检索块设计都已自动完成。

补充：本目录 index.html 只是截图图册，使用原生 HTML/CSS/JavaScript，无前端框架，无 RAG 解析或切块库。

## Git 历史补充：解析库并非单向升级

本轮将 Dify、MaxKB、RAGFlow 从浅克隆补全为可追溯历史（仍使用 blob 过滤，历史文件按需获取），未 checkout 或修改产品代码。

### MaxKB：pypdf → PyMuPDF → pypdf

- 2024-08-20，`17af6033978e34bb277770c4d461f07f9a6724de`：PDF 文本提取从 pypdf.PdfReader 改成 fitz/PyMuPDF；提交明确写“修复部分 pdf 中文乱码”。此时无文本页仍有 PyPDFLoader 图片提取分支，不应概括为完全删除所有 pypdf 使用。
- 2024-09-06，`70f44b990`：提交题为“格式规范的 pdf 通过目录来分段”。
- 2025-10-13，`cae568211`：增加 smart_split_paragraph。
- 2025-12-02，`9255089d8`：增加字号分析辅助提取 PDF 内容。
- 2026-04-27，`eaf508eb47c9e6719556bbaa9096d6becd5300fd`：PDF 主读取路径由 fitz 改回 pypdf.PdfReader，移除 pymupdf 依赖，保留自己的目录/链接/字号及 SplitModel 处理。提交未明确披露换库原因，不能自行归因为许可证或性能。
- 2026-08-03，`74335e9ad`：增加位置感知及目录处理；提交关联的问题是标题文本与正文重叠时段落内容丢失。
- 2026-10-19，`72456835f`：针对不同层级同名标题导致分段错误，保存正则匹配位置，替代按标题字符串重新搜索定位。

核查方法：git log --follow（跨目录移动）及 git show 对比实际 import、调用和处理逻辑。

### Dify：PDF 从可选 Unstructured 回到专用 PdfExtractor

- 2024-10-24，`5f11fe521dfc2e8d94990d5067cefd08fa1f51bc`：ETL_TYPE=Unstructured 分支的 PDF 处理从 UnstructuredPDFExtractor 改为 PdfExtractor；该提交版本的 PdfExtractor 使用 pypdfium2。不是全产品移除 Unstructured。
- PR #9794 的公开说明只有移除 PDF 路径，并未解释性能/质量动机。
- 2024-12-25，`9231fdbf4`：引入父子块支持。
- 2025-04-16，`95283b4dd3b34132050cb8b625daf2c463a4d1ff`：切块器 length_function 从 token encoder 改为字符 len(text)。
- 2026-09-23，`3113343c4`：进一步清理未使用的 splitter tokenization。

### RAGFlow：新增解析器选择，再演进为服务接入

- 2025-10-17，`387baf858`，PR #10621：增加 MinerU，初始接入使用 MINERU_EXECUTABLE 调用可执行程序。
- 2025-10-23，`0ff2042fc`，PR #10759：增加 Docling。与 DeepDOC 并存，不是证明新引擎全面替代旧引擎。
- 2025-12-17，`03f9be7cbbf88c1a02a48160b3dc72c946dde681`，PR #11977：MinerU 接入调整为 API 方式；同时删除部分自动安装/启动相关逻辑。这里 API 不等同于必须使用公网 SaaS。
- 2026-10 的后续提交：Docling 位置/页数回传修复 `acd6d887a`、MinerU 坐标缩放修复 `6d553f387`、取消时停止轮询 `350df0863`。这些说明接入解析器后，来源定位和任务生命周期仍需应用适配。

公开需求依据：#3945 要求可切换外部 PDF 解析器；#8092 用户提出 MinerU 结果切得细，可以再合并。这是用户的需求观点，不是准确率基准测试。

公开链接：
- https://github.com/1Panel-dev/MaxKB/commit/17af6033978e34bb277770c4d461f07f9a6724de
- https://github.com/1Panel-dev/MaxKB/commit/eaf508eb47c9e6719556bbaa9096d6becd5300fd
- https://github.com/langgenius/dify/pull/9794
- https://github.com/langgenius/dify/commit/95283b4dd3b34132050cb8b625daf2c463a4d1ff
- https://github.com/infiniflow/ragflow/pull/10621
- https://github.com/infiniflow/ragflow/pull/10759
- https://github.com/infiniflow/ragflow/pull/11977
- https://github.com/infiniflow/ragflow/issues/3945
- https://github.com/infiniflow/ragflow/issues/8092

判断：历史支持的是“基础库/统一解析器随需求调整，产品保留自己的切块与管理能力”，不支持“成熟产品最终都会全面换成 Docling/MinerU”，也不能仅从一次换库推断新库整体更好。
