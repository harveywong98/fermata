# 测试与学习示例

| 目录 | 用途 | 运行方式 |
| --- | --- | --- |
| `regression/` | 行为、边界、错误处理和接口兼容性 | `uv run pytest -q` |
| `learning/` | 看懂 API 的输入、参数和返回结构 | `uv run pytest tests/learning -q -s` |

在项目根目录运行。默认回归测试不调用外部服务，但切分相关测试需要本地 BGE tokenizer（默认 `knowledge/models/tokenizer/`）。

学习示例只打印关键结构、实际数据类型和少量样例值，不验证正确性；正确性断言由回归测试负责。学习示例使用真实调用：

- [文档切分](learning/test_chunking_api.py)：TXT → 父单元 → 子块，展示大小、重叠、正文、向量输入文本和来源范围。只需 tokenizer。
- [Embedding](learning/test_embedding_api.py)：展示 HTTP 请求和响应，以及 `embed()` 返回的归一化向量 JSON 字符串。需要 tokenizer 和本地模型，先运行 `docker compose up -d embedding`。
- [Search](learning/test_search_api.py)：展示查询参数、命中结构和评测 provider 的运行信息。需要数据库与 Embedding，并先运行 `uv run python -m evals.rag.prepare`。

切分和 Embedding 示例不需要 PostgreSQL，Search 示例需要。缺少资源或服务时会失败；文件开头列出了依赖和单独运行命令，`-s` 可查看精简的结果示例。

效果评测独立放在 [evals/rag/](../evals/rag/README.md)，不属于默认 pytest 测试集。

完整入库与检索验证仍使用 `uv run python scripts/smoke.py`，需要应用、数据库与 Embedding 服务；脚本会清理自身创建的测试数据。
