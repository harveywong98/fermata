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

Compose 启动 Embedding 服务，数据库通过 `DATABASE_URL` 配置。应用按单进程运行。模型和数据配置见 [知识模块说明](knowledge/README.md)。

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
```

## 开发

```sh
uv run pytest -q
# 应用、数据库与 Embedding 服务启动后：
uv run python scripts/smoke.py
```

[任务清单](TASKS.md) · [系统结构](docs/ARCHITECTURE.md) · [选型说明](docs/DECISIONS.md) · [评测方法](docs/EVALUATION.md)
