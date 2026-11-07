# 本地文档解析对照测试

运行环境：macOS-27.0.1-arm64-arm-64bit。Apple M1 / 16 GiB RAM；现有代码 vs Unstructured 0.27.36。

扫描命中 8293 条已复制来源；按 SHA256+后缀去重 1426 份。扫描错误 1314，复制错误 0。

## 范围和口径

- 原文件未修改；corpus 为副本，manifest.json 保存每份副本与所有原路径。
- PDF 对照使用 Unstructured fast 模式，不代表 hi_res 表格识别能力。扫描页能否 OCR 以实际结果为准。
- 现有实现保留其 20 MiB、200 页和 20 万单元格限制；限制失败与库能力失败需分开看。旧 DOC/XLS 原实现不支持。
- 单引擎串行、长驻进程，首次请求含冷启动。parse_s 可能含第一次按格式加载依赖；不是纯内核性能。
- 单文件 90 秒超时。peak_rss_mb 是当前进程累计峰值，不是单文件独占内存。
- business 仅按路径粗分（MyDocuments/Documents/Downloads），不是人工判断业务有效性。
- 真实文件未提供人工标注，字符数/表格数不能当准确率；输出需人工核验。

累计实际测试：baseline 73 份，Unstructured 73 份（含扫描期间的早期抽样）；另有 4 份控制样例。表中耗时只统计成功非空文件，失败与超时另列。 副本哈希校验 1426 份，不一致 0 份。

## 真实文件结果

|引擎|格式|已测|成功非空|空内容|失败/超时|解析耗时中位数(s)|P95(s)|
|---|---|---:|---:|---:|---:|---:|---:|
|baseline|.doc|6|0|0|6|—|—|
|baseline|.docx|18|16|0|2|0.040|1.420|
|baseline|.pdf|23|15|1|7|0.441|4.572|
|baseline|.xls|6|0|0|6|—|—|
|baseline|.xlsx|20|17|1|2|0.021|0.163|
|unstructured|.doc|6|0|0|6|—|—|
|unstructured|.docx|18|16|0|2|0.266|55.261|
|unstructured|.pdf|23|18|3|2|2.042|27.351|
|unstructured|.xls|6|5|0|1|0.129|4.623|
|unstructured|.xlsx|20|17|1|2|0.390|11.671|

## 控制样例功能检查

|样例|引擎|状态|关键词覆盖|表格/行/HTML|标题数|
|---|---|---|---|---|---|
|structured.docx|baseline|ok|4/4|1/0/0|1|
|structured.docx|unstructured|ok|4/4|1/0/1|1|
|merged.xlsx|baseline|ok|4/4|0/5/0|0|
|merged.xlsx|unstructured|ok|4/4|1/0/1|0|
|text-table.pdf|baseline|ok|4/4|0/0/0|0|
|text-table.pdf|unstructured|ok|4/4|0/0/0|5|
|scan.pdf|baseline|empty|0/2|0/0/0|0|
|scan.pdf|unstructured|empty|0/2|0/0/0|0|

## 同一文件双引擎成功的可比子集

- .docx：16 份；baseline 解析中位数 0.040s；Unstructured 0.266s。
- .pdf：15 份；baseline 解析中位数 0.441s；Unstructured 2.184s。
- .xlsx：17 份；baseline 解析中位数 0.021s；Unstructured 0.390s。

## 控制样例的边界检查

- baseline：公式原式 `=1+1` 保留。合并表头和 0/False 的行列对应需查看结构 JSON，不以词命中代替。
- unstructured：公式原式 `=1+1` 未保留。合并表头和 0/False 的行列对应需查看结构 JSON，不以词命中代替。
- Unstructured 单独 OCR 测试：ok，字符数 56，解析耗时 146.918s；不混入 fast 性能表。

## 错误分类

### baseline
- 12 次：ParseError — 仅支持 PDF、DOCX、XLSX；旧 DOC/XLS 需先转换
- 4 次：ParseError — 文件超过 20 MiB，请拆分
- 3 次：ParseError — 文件解析失败（BadZipFile），请检查格式或损坏情况
- 1 次：ParseError — 工作簿网格超过 200000 个单元格，请拆分或清理多余格式
- 1 次：UnicodeEncodeError — 'utf-8' codec can't encode character '\ude1d' in position 295: surrogates not allowed
- 1 次：ParseError — 文件解析失败（EmptyFileError），请检查格式或损坏情况
- 1 次：ParseError — 文件解析失败（LimitReachedError），请检查格式或损坏情况
### unstructured
- 6 次：FileNotFoundError — soffice command was not found. Please install libreoffice
on your system and try again.

- Install instructions: https://www.libreoffice.org/get-help/install-ho
- 3 次：timeout_or_crash — 
- 1 次：ValueError — not a ZIP archive (so not a DOCX file): '/Users/mac/Developer/src/python/privacy-react-demo/docs/research/document-parser-benchmark/corpus/docx/703544cab06c5ab0b8822
- 1 次：UnprocessableEntityError — Not a valid XLSX file.
- 1 次：OleFileError — incomplete OLE sector
- 1 次：ValueError — not a ZIP archive (so not a DOCX file): '/Users/mac/Developer/src/python/privacy-react-demo/docs/research/document-parser-benchmark/corpus/docx/e3b0c44298fc1c149afbf

原始统计：results.csv；结构结果：results/<engine>/*.parsed.json；可重跑：.venv/bin/python run.py（已完成文件跳过）。

## 测试覆盖与具体判断

- 本轮选择 70 份去重原文件，另有 4 份自制控制样例；不是全量性能测试。选择清单见 benchmark-selection.json。
- baseline：本轮选定原文件完成 70/70。
- unstructured：本轮选定原文件完成 70/70。
- 扫描覆盖主目录但不完整遍历 OrbStack 虚拟挂载（多次超时后停止，保留已发现路径）；macOS 拒绝访问的目录见 inventory.json，不能声称这些目录已完整扫描。
- 部分测试与文件扫描/复制同时运行，本次耗时用于本机选型初筛，不是隔离资源后的严格性能排名。
- Word 控制样例两者均保留关键文字、标题和表格；真实文档仍须检查阅读顺序、跨页内容等。
- 原生 PDF 控制样例两者可提取关键文字，但均未还原为表格。本轮 Unstructured fast 不代表 hi_res 的表格识别效果，hi_res 未测。
- Excel 控制样例：现有实现保留字符串 00123、数值 0、布尔 False、公式原式和合并来源；Unstructured 0.27.36 在本例把 count=0 输出为 False，未保留公式原式与显式合并关系。具体见 functional-checks.json。
- Excel 公式：读取缓存计算值与保留公式原式是两种需求；样例公式没有缓存结果，空值不能直接推断所有公式都丢失。0/False 则是本例确实出现的值混淆，需要在目标版本与真实文件复验。
- 扫描 PDF：现有实现和 fast 均无文字；单独启用本机 Tesseract OCR 能识别测试页。这里是英文扫描页，尚不能说明中文扫描件准确率。
- DOC/XLS、格式损坏、体积/页数限制及超时要分别看待。运行环境缺少 LibreOffice 时的转换失败属于部署缺依赖，不代表安装齐全后仍不支持。

## OCR 缓存后复测

|次数|状态|导入(s)|解析(s)|字符数|
|---|---|---:|---:|---:|
|scan-0|ok|9.414|42.026|56|
|scan-1|ok|0.000|9.929|56|
|scan-2|ok|0.000|9.517|56|

首次 OCR 记录含依赖/字体缓存初始化，不能视为稳定性能；复测为同一进程连续三次，不同文件与中文复杂版面需另测。

## 选型建议

当前数据不足以证明统一解析库普遍更好。现有实现对 Office 原始字段和表格溯源更可控；Unstructured 提供统一元素接口及可选 OCR，但需要接受额外依赖，并对值保真和复杂版面补充回归。先保留现有实现，用实际中文扫描件、跨页表格和多级表头补齐标注集后再决定是否替换。

## 补充：内容保真测试

已对 16 份 Word、17 份 Excel 做源 XML 对照，并对 2 份 PDF 的第一页进行渲染核验。结果、评分口径与限制见 [内容保真测试](accuracy/REPORT.md)。复跑：`.venv/bin/python accuracy_test.py`。
