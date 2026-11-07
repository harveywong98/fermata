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

Compose 默认只启动 Embedding，promptfoo 和 Langfuse 按需启用，容器名统一以 `fe_` 开头。知识库数据库仍通过 `DATABASE_URL` 单独配置。应用按单进程运行。模型和数据配置见 [知识模块说明](knowledge/README.md)。

辅助服务（Docker Compose 2.20+）：

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
knowledge/    文档处理、入库与检索
web/          接口与页面
skills/       业务操作规范
tests/        测试
docs/         设计与参考资料
compose/      按服务拆分的容器配置
```

## 开发

```sh
uv run pytest -q
# 应用、数据库与 Embedding 服务启动后：
uv run python scripts/smoke.py
```

[任务清单](TASKS.md) · [系统结构](docs/ARCHITECTURE.md) · [选型说明](docs/DECISIONS.md) · [评测方法](docs/EVALUATION.md)
