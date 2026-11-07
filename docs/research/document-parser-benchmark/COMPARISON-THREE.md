# 三方文档解析对比

主对比：现有实现 / Unstructured 0.27.36（PDF fast）/ Docling 2.146.0（PDF Native；Office 原生转换）。Apple M1、16 GiB RAM。

## 执行覆盖

|指标|现有实现|Unstructured|Docling|
|---|---:|---:|---:|
|成功且非空|48/73 (65.75%)|56/73 (76.71%)|50/73 (68.49%)|
|空结果|2/73 (2.74%)|4/73 (5.48%)|2/73 (2.74%)|
|部分结果|0/73 (0.00%)|0/73 (0.00%)|0/73 (0.00%)|
|失败/超时|23/73 (31.51%)|13/73 (17.81%)|21/73 (28.77%)|
|实际完成|73|73|73|

## 内容保真（三方均成功的同一批文件）

|指标|现有实现|Unstructured|Docling|
|---|---:|---:|---:|
|Word 文本单元召回|99.969% (9620/9623; 16文件)|99.979% (9621/9623; 16文件)|100.000% (9623/9623; 16文件)|
|Word 按原文顺序匹配召回|99.969% (9620/9623; 16文件)|99.979% (9621/9623; 16文件)|99.751% (9599/9623; 16文件)|
|Word 表格位置与内容匹配|99.969% (9599/9602; 16文件)|100.000% (9602/9602; 16文件)|99.875% (9590/9602; 16文件)|
|Excel 文本值严格召回|100.000% (4835/4835; 17文件)|99.007% (4787/4835; 17文件)|100.000% (4835/4835; 17文件)|
|Excel 换行表示统一后召回|100.000% (4835/4835; 17文件)|100.000% (4835/4835; 17文件)|100.000% (4835/4835; 17文件)|

## 主性能：三方均成功的相同文件，解析耗时中位数

|格式|文件数|现有实现(s)|Unstructured(s)|Docling(s)|
|---|---:|---:|---:|---:|
|.docx|16|0.040|0.266|0.407|
|.pdf|15|0.441|2.184|1.249|
|.xlsx|17|0.021|0.390|0.015|

## Docling 各格式执行结果

|格式|成功|空|部分|失败/超时|
|---|---:|---:|---:|---:|
|.doc|0|0|0|6|
|.docx|16|0|0|2|
|.pdf|17|1|0|5|
|.xls|0|0|0|6|
|.xlsx|17|1|0|2|

## 配置、冷启动与限制

- 同一批 73 份原文件，另有 4 份控制样例；每文件外部硬超时 90 秒。部分结果单列，不冒充完整成功。
- 主测试 Docling PDF 使用 NativePdfPipeline，无版面/OCR/表格模型；Office 使用原生转换。模型辅助标准模式仅对 2 份异常 PDF 和 2 份 PDF 控制样例另做补测，不混入主表。
- Docling 独立虚拟环境安装，依赖版本见 requirements-docling.lock.txt；未改变前两者的依赖。
- 主测试不需要模型；标准模式补测先单独下载模型，首次进程使用仍包含模型加载。parse_s 含转换和评分适配，convert_s/adapter_s 可分开查看；主测试的一部分与模型下载重叠，存在背景负载。
- 旧格式、损坏文件、缺少依赖和超时分别记录，执行失败率不等于内容错误率。
- Word/Excel 标准来自源 XML，正文不含浮动文本框；合并格统一展开。Excel 只评估字符串值，不覆盖数字/公式或所有行列错误；严格召回与换行归一化后召回分开。
- 召回不惩罚全部多余输出；按单元汇总，大文件权重大。PDF 没有全量人工标注，不能给出总体准确率。
- 主测试及标准模式补测都关闭 OCR；空扫描页属于配置覆盖不足，不是 Docling OCR 能力失败。
- 前两者沿用前次实测；测试时间和后台负载不同，性能用于选型初筛。

## Docling 冷启动预热记录

PDF 控制页预热：状态 ok；导入 4.100s，解析/首次模型准备 12.359s。不是稳定单页耗时。

## Docling 错误分类

- 4 次：timeout_or_crash：
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 48521e23cd620283813142cc5b2fc63f5cad9c6f1aecde92dbc40ec062163f68.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.PIPELINE: 'pipeline'> module_name='SimplePipeline' error_message="1 validation error for TableData\n  Value error, Table of 50001x23 cells exceeds the limit of 1000000 cells [type=value_error, input_value={'num_ro
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='MsWordDocumentBackend could not load document with hash 703544cab06c5ab0b8822626e60dfa79452ef988382d8e9029d01a1dd9579941' category=<FailureCategory.BACKEND_F
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='MsExcelDocumentBackend could not load document with hash ed2b9bb486e15d407515f8a6b2e5f255a108e5ea6132d6cc0c37bc473ee60052' category=<FailureCategory.BACKEND_
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 843819e8d2f3282aece5b64db4fa9e3f78385f7b292c0e8840ac1129ff90125c.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 4f26e919f0b1cc3d44efa88833988c07dbff5f5127b0deade4439a2ed1293de6.doc.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 69de7452c5fa453186361eaeac5c239b691130350d0c86e5d4765cc8de4eecda.doc.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 30cc728f3eec3dc23623d1aebd0064584cc16226f4db0c38a4f0361015318673.doc.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 504bc783df3574d50728d5859b008a36b9162634bbabe9fdab967863c071e0a6.doc.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 8dbd4b5c986638c0b4745c997085a2448cd74ecb252683a6599dd82880e36688.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 73ab13e7a2874023c2f3cde09eb9ec6f0e4e4c195c1c76156dc91f1633116a3e.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document b63801ee3272b0cc75820448ef00c7eb800842459450c53c57028ba67ee5218c.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document bdc9cb5f13e01cecf773c897aef564a2ffb46614f07116e711d0ab64f65bdd41.xls.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document 4489c2d43a2790efcfcf3eea569cc7792c50a63ecb9fc5ee8cc6ac3e89dc78a7.doc.' category=<FailureCategory.UNKN
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='docling-parse could not load document e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855: Failed to load document with key key=e3b0c44298fc1c14
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='MsWordDocumentBackend could not load document with hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' category=<FailureCategory.BACKEND_F
- 1 次：error：component_type=<DoclingComponentType.USER_INPUT: 'user_input'> module_name='' error_message='An unexpected error occurred while opening the document d548546329126695e2a76d0647fdfa77f9f3f9d0800cc0ce57fc689c06dcb861.doc.' category=<FailureCategory.UNKN

参考配置：[Docling 官方 Pipeline Options](https://docling-project.github.io/docling/reference/pipeline_options/)。
复跑：`BENCH_EXTENSIONS=.docx,.xlsx,.doc,.xls .venv-docling/bin/python run.py docling-selection.json docling`，PDF：`BENCH_EXTENSIONS=.pdf .venv-docling/bin/python run.py docling-selection.json docling_native`；评分：`.venv/bin/python accuracy_three.py`；报告：`.venv/bin/python summarize_three.py`。

## 主性能对比：Docling Native PDF（无版面/OCR/表格模型）

|指标|结果|
|---|---:|
|完成|23/23|
|成功/空/失败|17/1/5|

三方均成功的 15 份 PDF：现有实现 0.441s，Unstructured fast 2.184s，Docling Native 1.249s（中位数）。

## 控制样例与结构差异解释

- Docling 的 Word 文本全部召回不意味着原网格结构完全保留：9 个单格代码表变成代码内容，3 个嵌套表格编号移到单独的子表。表格原位匹配把这些算作结构差异，不能解释成丢了 12 段文字。
- Docling 控制 Excel 保留 00123、0、False 和合并表头；未缓存公式单元格为空，不保留公式原式。这与只读取缓存值的行为相符。详见 docling-functional-checks.json。
- Docling PDF 首次下载采用 Xet 时出现长时间停滞，终止后改普通 HTTP 下载；中断日志保留在 docling-warmup-xet.log，不能把后一次预热时长当作全部安装准备时间。

## PDF 定向异常页人工检查（不是随机准确率）

|引擎|完成文件数|直接片段匹配|NFKC/去控制符后|
|---|---:|---:|---:|
|baseline|2/2|0/13|4/13|
|unstructured|2/2|5/13|9/13|
|docling|2/2|12/13|12/13|
|docling_native|2/2|12/13|12/13|

仅沿用前次人工转录的两页、13 项（含表单可见值）；超时或失败按未获取计。不能外推整体 PDF 内容准确率。

标准模式补充真实 PDF 已完成 2/2（另有 2 份 PDF 控制样例），不包含在主表成功率中。

异常页复核：Docling Native 在课程大纲中未出现此前的 U+0001 控制符；但中文字体表单仍输出 `更新�文本框从顸面重用`，存在替换符和有效汉字误映射，不能把没有 `(cid:N)` 当成没有错误。

## 模型版样例耗时（单次，非总体性能）

|文件|页数|Native(s)|标准模型版(s)|
|---|---:|---:|---:|
|课程大纲|29|5.194|41.523|
|中文字体表单|2|0.185|3.704|
