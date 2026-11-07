# 知识能力模块

本模块是统一应用内部的知识能力，供 `tools/knowledge.py` 和 `web/routes.py` 共用。代码不依赖 FastAPI；HTTP 适配在 `web/`。统一启动见[项目 README](../README.md)，Agent 主流程仍有 [TODO](../TASKS.md)。

Docling解析 → 父子块预览 → BGE-base向量化 → PostgreSQL/pgvector检索。

页面：http://127.0.0.1:8018 ，API：http://127.0.0.1:8018/docs 。

## 启动

以下命令在项目根目录运行：

```sh
uv sync --locked
# 本机.env已配置，不要覆盖；新环境参考.env.example。
docker compose up -d embedding
uv run python main.py
```

PG复用 `127.0.0.1:5432/privacy_knowledge_demo`，账号在未提交的.env中。上述命令只启动llama.cpp服务（18087），CPU4线程、CLS池化、768维、关闭mmap。首次启动在独立knowledge schema建表，不自动删除旧结构。

默认模型为 `knowledge/models/bge-base-zh-v1.5-f16.gguf`，tokenizer位于 `knowledge/models/tokenizer/`，来自已验证的 [Embedding实验](../docs/research/embedding-benchmark/README.md)：BAAI官方权重经b8576转换。模型文件不进入Git。

## 使用

1. 选择业务知识库，上传PDF、DOCX、XLSX、TXT或MD，最大20MiB。
2. 查看解析内容，设置完整输入预算（默认400 tokens）和正文重叠（默认40）。上传和预览仅保存到配置的数据目录下drafts/临时文件，不写PG。
3. 预览子块及父单元ID；支持“删除此块”，也可调整大小重新生成；确认后才向量化和发布。
4. 搜索指定同一知识库，先命中子块，再读取父单元并去重。
5. 页面分为“已入库文档”和“未确认草稿”。打开已入库文档会生成编辑草稿；放弃草稿不影响已发布版本，删除已入库文档才会删除PG记录与原文件。

## 代码

`data/` 保存草稿与原文件，`models/` 保存模型与 tokenizer；均为本地资源，不纳入 Git。

|文件|职责|
|---|---|
|application/service.py|上传、预览、发布、编辑和删除的业务逻辑|
|application/retrieval.py|Agent 和 Web 共用的检索入口|
|storage/repository.py|PG连接及schema初始化|
|embedding/client.py|BGE向量服务调用、输入校验与模型版本标识|
|embedding/tokenizer.py|模型tokenizer与token计数，供切分和向量输入校验共用|
|contracts.py|共享输入模型与业务错误|
|documents/parsing.py|TXT和Docling解析，将文档组织为带来源信息的父单元|
|documents/chunking.py|按token预算切分父单元，保留标题、表头和字符范围|
|application/drafts.py|临时草稿文件及分块预览，不访问PG|
|../web/templates/knowledge.html|单页导入与搜索界面|
|../web/routes.py|HTTP接口适配|
|storage/sql/schema.sql|document与document_chunk两张表；父子块自关联|
|../compose/embedding.yaml|使用llama.cpp上游镜像运行Embedding服务，由根compose.yaml引入|

标题下连续正文形成父块，表格单独形成父块；TXT按段落或行划分。父、子块均保存在document_chunk，用chunk_role区分，子块parent_id指向同表父块。父块只保存完整正文，不向量化；子块保存向量。通过文档与批次复合外键约束关联范围。父块正文有意冗余，避免回读时拼接重叠的子块。

**最终确认前，不向PG写入文档、父块或子块。** 草稿默认写在knowledge/data/drafts/，可以恢复预览或放弃；尚无自动过期清理，临时文件会保留至手动放弃。确认时先生成全部向量，随后单事务写入两张表并切换生效批次。失败不留下半份数据；旧预览返回409。编辑已入库文档时，确认前旧版保持不变；确认成功后替换旧批次。单进程运行，勿增加workers。

删除块会按来源字符范围从草稿父正文移除内容，再重新切分，防止父块和重叠邻居带回已删除文字。调整大小不会恢复删除内容，原始文件保留。全部删空也可确认，清空该文档可检索内容。当前无撤销按钮。

## 边界

- 本地单用户演示，无登录、任务队列和自动重试；同步等待，失败可重新确认。
- PDF使用Docling Native文本解析，无OCR或额外版面模型；空扫描件报错，不会假装入库成功。
- 不实现自动规则语义推断、跨章节引用解析、模型补写描述。完整设计方向见 [CHUNKING.md](CHUNKING.md)。
- 搜索是TopK候选，不是最终分类或无答案判断。按父单元去重后不保证返回K条。
- 父单元响应最多前6000字符，返回parent_truncated，同时保留真正命中片段。详情可查看全文；尚无Agent token预算分配。
- 原文件和解析结果默认在knowledge/data/，备份需包含PG及该目录。hash由应用计算；Chunk正文hash不全局唯一。
- profile固定权重哈希、CLS池化和文本处理版本。Embedding服务应加载compose指定权重，不能偷偷换同维度模型。
- 知识库暂用业务名称作标识，没有单独配置表。模型、上传文件、.env不提交。

## 验证

API 学习示例在 `tests/learning/`，行为回归测试在 `tests/regression/`。切分与 Embedding 的输入输出示例及运行依赖见 [测试说明](../tests/README.md)。

```sh
uv run pytest -q
# API、PG、Embedding需已启动；只清理测试自身创建的文档
uv run python scripts/smoke.py
```

smoke覆盖TXT、DOCX、XLSX、PDF真实解析，并直接比较两张PG表的数据快照，验证确认前零写入、模拟向量服务失败不落库、过期预览、重复确认、父子回读、删除重叠内容及空版本发布。历史版本曾通过完整验证；本次重构验证范围以交付说明为准。

旧多库解析实现保存在 [历史备份](../docs/history/README.md) 中；当前选型及原始报告入口见 [选型说明](../docs/DECISIONS.md)。
