# 历史备份（按需恢复）

`legacy-20261107.tar.gz` 保存整理前的整个 `archive/`：两份旧知识库实现、统一应用前的代码和依赖文件、旧任务规划及历史数据快照。压缩后约 680 KiB；移除展开目录前，已逐文件校验 SHA-256，共 57 个普通文件。

它不参与运行，也不是当前开发任务来源。平时从项目 README 和 TASKS 开始即可。

需要追溯时，先解压到一个单独目录，不要覆盖当前应用：

```sh
mkdir -p /private/tmp/privacy-history
tar -xzf docs/history/legacy-20261107.tar.gz -C /private/tmp/privacy-history
```

解压后保留原 `archive/` 层级。历史包包含旧本地配置和数据，仅作为本机备份，已加入 `.gitignore`，不随源码提交。当前运行资产位于 `rag/data/` 和 `rag/models/`，与本备份不同。
