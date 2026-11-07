# 本地文档解析测试

选型结论与综合对比见 [文档解析库综合对比与选型](PARSER-SELECTION.md)。

范围：/Users/mac 下 PDF / DOC / DOCX / XLS / XLSX，含隐藏目录、依赖包、代码仓库样例；不跟随符号链接，不递归收集本测试目录。

所有解析均在本机进行，不向云解析 API 上传文档。安装依赖、下载公开模型可能访问网络。

- inventory.json：完整扫描结果及无权限目录记录。
- corpus/：按后缀分类、SHA256 命名的文件副本，不改动原文件。
- manifest.json：副本到所有原路径的对应关系，同内容同后缀只保存一份。
- fixtures/：自己生成的可控功能样例，独立于业务文件统计。
- results/：每文件的指标与结构输出。
- REPORT.md / results.csv：汇总。
- requirements.lock.txt：本次实际 Python 依赖版本。

复现：

```sh
python3 scan.py
python3 collect.py
.venv/bin/python fixtures.py
python3 select_samples.py
UNSTRUCTURED_DISABLE_NOTICE=1 .venv/bin/python run.py
.venv/bin/python check_features.py
python3 make_index.py
.venv/bin/python summarize.py
```

测试限制：原实现有大小/页数/网格限制且不支持 DOC/XLS；Unstructured 的 PDF 主对照采用 fast 模式，不代表 hi_res 上限。串行长驻进程，每文件 90 秒超时；进程首次请求与按格式懒加载影响单独记录。内存为进程累计峰值。真实文件无人工标准答案，成功、非空、字符数和表格数都不等于内容准确。

本轮默认按 benchmark-selection.json 测试（个人文档 + 每格式最多 6 份大小分位样例），并非全部收集文件。全量测试可运行 `.venv/bin/python run.py manifest.json`，可能需要较长时间；现有结果会跳过。浏览副本可打开 index.html；全部原路径映射见 FILES.csv。

本轮扫描例外：OrbStack 虚拟挂载读取超时，停止遍历并保留已发现文件；重新完成其余主目录扫描。macOS 无权限目录也未覆盖。清单只代表可读取的实际收集范围，不是完整备份。

内容保真测试：`.venv/bin/python accuracy_test.py`。结果见 accuracy/REPORT.md；标准来自源 Office XML 和 PDF 渲染页人工转录，不以解析器输出当标准。

## Docling 补测

独立环境 `.venv-docling`，版本见 `requirements-docling.lock.txt`。主比较为无模型模式：Office 正常转换；PDF 使用 NativePdfFormatOption。`docling-selection.json` 固定为原来实际测试的同一批 73 份文件。

```sh
BENCH_EXTENSIONS=.docx,.xlsx,.doc,.xls .venv-docling/bin/python run.py docling-selection.json docling
BENCH_EXTENSIONS=.pdf .venv-docling/bin/python run.py docling-selection.json docling_native
.venv/bin/python accuracy_three.py
.venv/bin/python pdf_accuracy_three.py
.venv/bin/python check_docling_features.py
.venv/bin/python summarize_three.py
```

三方汇总：COMPARISON-THREE.md；逐文件指标：comparison-three.csv。模型辅助 PDF 只补测 docling-full-selection.json 的 2 份异常文件与 PDF 控制样例，不混入主表，关闭 OCR、CPU 4 线程。首次模型准备日志与后续解析结果分别保存。原始 `.native` 数据在 parsed.json 的 native 字段，便于核查适配后的结构。
