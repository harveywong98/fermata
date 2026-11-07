<p align="center">
  <img src="docs/assets/fermata-banner.svg" alt="Fermata — 五线谱与延长记号" width="100%" />
</p>

**Fermata，一个通用 Agent 项目。** 名字取自音乐中的延长记号（𝄐）。

围绕 Agent、工具、知识与 Skills 组织，业务场景通过工具和操作规范接入。

## 启动

在项目根目录配置 `.env`（参考 [.env.example](.env.example)），准备 PostgreSQL/pgvector 和本地 BGE 模型：

```sh
uv sync --locked
docker compose up -d
uv run python main.py
```

访问 http://127.0.0.1:8018 ，接口文档位于 http://127.0.0.1:8018/docs 。

Compose 默认只启动 Embedding，promptfoo 和 Langfuse 按需启用，容器名统一以 `fe_` 开头。知识库数据库仍通过 `DATABASE_URL` 单独配置。应用按单进程运行。模型和数据配置见 [知识模块说明](rag/README.md)。

辅助服务（Docker Compose 2.20+）：

promptfoo 直接定义在根 `compose.yaml`，可用 `docker compose up -d promptfoo` 单独启动。统一从根 `compose.yaml` 启动；`compose/` 下的文件由它引入，不单独启动。在 IDEA 的 Docker Compose 运行配置中选择根文件，项目名使用 `fermata`，启用需要的 profile（`eval` 或 `tracing`）。单独运行子文件会使用不同的项目名，与已有 `fe_` 容器发生命名冲突。

```sh
docker compose --profile eval up -d       # Embedding + promptfoo
docker compose --profile tracing up -d    # Embedding + Langfuse 全套
docker compose --profile '*' up -d        # 全部启动
docker compose --profile '*' stop         # 全部停止，保留数据
```

| 本地服务 | 地址 |
| --- | --- |
| promptfoo | http://localhost:15500 |
| Langfuse | http://localhost:13000 |

Langfuse 首次访问时注册本地账号。数据保存在 Docker 命名卷中，`docker compose --profile '*' down` 移除全部容器但保留数据，加 `-v` 会删除这些卷。配置中的默认凭据仅用于本地开发，覆盖项见 `.env.example`。只启动知识检索依赖可用 `docker compose up -d embedding`。

## 结构

```text
main.py       应用入口
agent/        Agent、提示词与会话
tools/        工具实现与注册
rag/    文档处理、入库与检索
web/          接口与页面
skills/       业务操作规范
tests/        learning 学习示例、regression 回归测试
evals/        promptfoo 评测配置、数据集和运行入口
docs/         设计与参考资料
compose/      Embedding 与 Langfuse 子配置
```

## 开发

```sh
uv run pytest -q
# 学习切分 API（本地 tokenizer），-s 展示输入输出：
uv run pytest tests/learning/test_chunking_api.py -q -s
# 学习 Embedding API（需先启动 embedding）：
uv run pytest tests/learning/test_embedding_api.py -q -s
# 应用、数据库与 Embedding 服务启动后：
uv run python scripts/smoke.py
```

默认只运行 `tests/regression/`。学习示例的依赖与调用方式见 [测试说明](tests/README.md)。

RAG 效果评测见 [评测目录](evals/rag/README.md)：准备演示知识库后运行 `uv run python -m evals.rag.scripts.run`，用本机 `promptfoo view --port 15501` 查看历史；本机 CLI 与 Compose 的 promptfoo 数据独立。

[任务清单](TASKS.md) · [系统结构](docs/ARCHITECTURE.md) · [选型说明](docs/DECISIONS.md) · [评测方法](docs/EVALUATION.md)
