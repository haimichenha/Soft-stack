---
description: SS 软件开发与学习入口，独立于 AS
argument-hint: <软件规划、代码问题、开发任务或学习目标>
---

使用 SS 完成本轮任务：$ARGUMENTS

1. 先读取 `~/.agents/skills/software-stack/SKILL.md`；如本机未安装，调用本会话实际暴露的 `ss_read_guide(topic="entry")`。缺少工具时只做一次定向发现，不猜服务器名、不遍历 resources/list。
2. 项目续接时，在确认的项目根目录调用一次 `ss_project_brief(repo_path)`。失败则读取项目已有 `.as-state/state.json` 与 `handoff.md`；若同时存在 `tools/search-stack/local/as-state`，遵从项目声明，不合并、不新建账本。
3. 只读本轮需要的参考；把目标落实到真实代码、具体行为和证据。任务未定时给有差异的小样，不把讨论自动升级为上线。
4. MCP 当前仅提供指南与只读状态，不能搜索、写代码、写学习记录、提交或部署；这些由宿主在本轮授权范围内执行。不要把调用 SS 等同于任务完成。
5. `/SS` 不改 `/AS`，不同时启动两个状态写入者。带着学习时讲清一个真实函数或状态，但不以答题作为继续工作的门禁。
