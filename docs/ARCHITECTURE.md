# 统一应用结构

模块目录见 [项目 README](../README.md)。本文只说明模块之间的调用方式与运行约束；当前选型依据集中在 [DECISIONS.md](DECISIONS.md)。

## 调用链

```text
Agent → tools.search_knowledge → knowledge.retrieval.search
Web /api/search ───────────────→ knowledge.retrieval.search
Web 文档与草稿接口 ────────────→ knowledge.service
                                  ├─ chunking / drafts
                                  ├─ embeddings → llama.cpp
                                  └─ repository → PostgreSQL
```

Agent 到知识模块是普通 Python 调用，不需要 `KNOWLEDGE_API_URL` 或单独 RAG 应用。Web 接口仍保留 `/api/documents`、`/api/drafts`、`/api/search` 的原有请求、响应与状态码。`KnowledgeError` 由 Web 转为 HTTP 响应，由工具转为 `error` 状态，业务代码不依赖 FastAPI。

检索内部仍调用 Embedding 服务和数据库；移除内部 HTTP 跳转不代表取消所有基础设施。同步文档接口由 Web 执行；当前是本地单用户、单进程应用。大规模解析与并发对话需要后台任务，暂未实现。

## 本地辅助服务

根 `compose.yaml` 通过 `include` 汇总 `compose/` 下的 Embedding、promptfoo 和 Langfuse 配置；相对路径和 `.env` 均以项目根目录为基准。默认只启动 Embedding，`eval` profile 启用 promptfoo，`tracing` profile 启用 Langfuse 全套。所有容器名以 `fe_` 开头，仅将页面和对象存储端口绑定到本机。Langfuse 使用独立的 PostgreSQL、ClickHouse、Redis 和 MinIO；不会复用应用的 `DATABASE_URL`。数据使用 Docker 命名卷持久化。

部署参考 [promptfoo 自托管说明](https://www.promptfoo.dev/docs/usage/self-hosting/) 和 [Langfuse 官方 Compose](https://github.com/langfuse/langfuse/blob/main/docker-compose.yml)，只保留本地运行所需组件。当前仅提供服务部署，Agent tracing 与项目评测用例尚未接入，规划见 `TASKS.md`。

## 配置、资源与迁移

统一维护根目录 `pyproject.toml`、`uv.lock`、`.env` 和 `compose.yaml`。根目录 Python 环境同时安装 Agent 与知识能力依赖，代价是安装体积增加，但不必维护两个应用环境。

知识实现与资源集中在 `knowledge/`：`data/` 保存草稿和原文件，`models/` 保存 Embedding 权重与 tokenizer，两者均不纳入 Git。旧实现保存在 [历史备份](history/README.md) 中。

`KNOWLEDGE_DATA_DIR` 和 `KNOWLEDGE_MODEL_DIR` 支持绝对路径或相对项目根目录的路径，默认分别为 `knowledge/data/` 和 `knowledge/models/`。已有文档后再迁移目录时，须同步修改数据库和草稿中的 `file_uri`；仅修改环境变量不会迁移已有记录。Compose 挂载与应用须使用同一模型目录。

模型哈希在实际检索或发布时计算并缓存，不在导入模块时加载大模型文件。这样导入 Web、检查接口、继续写 Agent 都不要求模型已部署。

未完成能力与验收条件统一维护在 [TASKS.md](../TASKS.md)，不在这里重复列清单。
