# SS 注册与回退

## 命名

| 层 | 名称 |
| --- | --- |
| 用户入口 | `/SS` |
| Skill ID | `software-stack` |
| MCP server ID | `software-stack` |
| 工具前缀 | `ss_` |

注册 Skill、命令与 MCP 是不同动作。不要仅写一个同名配置就宣称已经连通。

## 本机注册范围

为已安装客户端新增独立入口，不覆盖 AS：

1. 将 `skills/software-stack` 安装到用户 Skill 目录，仅安装一个副本。
2. Claude Code 的 `~/.claude/commands/SS.md` 使用本包命令。
3. Claude 用户配置 `mcpServers.software-stack`，Codex 配置 `[mcp_servers.software-stack]`，均指向本包虚拟环境 Python 与 `server.py`。
4. 环境变量 `SS_WORKSPACE_ROOTS` 显式列出获准工作区；没有配置则拒绝项目读取。环境变量不含 API 密钥。

Codex TOML 示例（替换为真实的绝对路径）：

```toml
[mcp_servers.software-stack]
command = 'F:\your-workspace\software-stack\.venv\Scripts\python.exe'
args = ['-B', 'F:\your-workspace\software-stack\server.py']

[mcp_servers.software-stack.env]
PYTHONIOENCODING = 'utf-8'
SS_WORKSPACE_ROOTS = '["F:/your-workspace"]'
```

Claude 使用相同的 `command`、`args`、`env`，另外设置 `type: stdio`。

本包提供只新增、不覆盖冲突项的注册器。先 dry-run，再显式执行：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\register_local.py --workspace-root 'F:\your-workspace'
.\.venv\Scripts\python.exe -X utf8 scripts\register_local.py --workspace-root 'F:\your-workspace' --apply
```

可多次传 `--workspace-root`。已有 SS 项与请求不一致时会停止，而不是悄悄扩大读取范围；后续更新应先审阅差异。注册器不创建 Git 提交或远端仓库。

## 验证分层

- 包测试：真实 stdio 握手、工具发现/调用、资源读取、作用域拒绝、双状态路径冲突、无写入。
- 注册读回：JSON/TOML 可解析，只有新增 SS 项，原 AS、其他 MCP 和模型/provider 配置语义不变。
- 客户端验收：重连或新开会话，确认 MCP 列表能看到 SS 的三个工具，再试一个真实软件任务。仅配置读回不等于当前会话已热加载。
- 长期效果：使用反馈再验证是否少返工；不能以测试数量证明技能更好。

## 停用与回退

- Claude：移除 `mcpServers` 中本次新增的 `software-stack` 项；Codex：移除对应 MCP 表或设 `enabled = false`。
- 删除前核对路径，仅移除 `software-stack` 安装副本与 `SS.md`；不要删除 AS 或项目 `.as-state`。
- 配置备份放在各自用户配置旁，含潜在凭据，不进源码包或 Git。仅在期间没有其他配置变化时才整份恢复，否则只移除 SS 项。
- 不自动停止其他客户端进程；重连后验证 AS 仍然可用。

参考：[Codex MCP](https://developers.openai.com/codex/mcp)、[Codex Skills](https://developers.openai.com/codex/skills)、[Claude Commands/Skills](https://code.claude.com/docs/en/slash-commands)、[官方 Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)。实现使用已固定的 SDK 1.30.0，不混用主分支 v2 API。
