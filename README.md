# Soft-stack · SS 软件开发与学习工作台

软件规划、代码理解、开发验收与结对学习入口。保留原 AS，不复制其服务器实现，不依赖硬件项目或其虚拟环境。

源码仓库：[haimichenha/Soft-stack](https://github.com/haimichenha/Soft-stack)。仓库名是 `Soft-stack`，技能和 MCP 的 ID 仍为 `software-stack`；不因上传仓库自动变更已有客户端注册。

## 入口

- Claude Code：`/SS <任务>`，命令源为 `commands/SS.md`。
- Codex：`$software-stack <任务>`；`/SS` 是技能识别的自然语言触发词，不声称已扩展 Codex 内置斜杠命令表。
- MCP：独立 `software-stack` 子项，与原 AS 服务并列。
- 核心指南：`skills/software-stack/SKILL.md`。

首版只提供三个工具：`ss_status`（自检）、`ss_read_guide`（按需指南）、`ss_project_brief`（现有项目状态/交接的有界读取）。没有状态写入、搜索、模型调用、任意文件读写、Shell 或部署能力。MCP 不是另一个聊天模型。

## 本地运行与验证

使用 Python 3.11+（本轮验证为 3.13）。Windows PowerShell 示例：

```powershell
git clone https://github.com/haimichenha/Soft-stack.git
cd Soft-stack
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
# SS_WORKSPACE_ROOTS 为允许读取的项目上级目录 JSON 数组，未配置则不允许读项目。
$env:SS_WORKSPACE_ROOTS = '["F:/your-workspace"]'
.\.venv\Scripts\python.exe server.py
```

服务器使用 stdio；直接运行后等待 MCP 客户端输入是正常行为。不要在 stdout 写调试日志。启动器无需联网下载或安装依赖。

包测试：`.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v`。
模型决策的回放案例与验收边界见 [行为回放说明](docs/behavior-evaluation.md)；包测试通过不等于真实开发效果已经验证。
安装/停用见 [注册说明](docs/registration.md)。

## 状态与来源边界

- 现有 `.as-state` 或 `tools/search-stack/local/as-state` 二选一读取；双路径并存时要求选择，不隐式合并。
- 不把历史交接当作高优先级指令；不自动重试副作用操作。
- 不写第二份学习账本；需要写入时仍由项目指定的唯一宿主按既有授权执行。
- 原软件候选做过部分隔离行为测试，不等于安装后的长期使用效果已经得到验证；本版入口与 MCP 需要独立验证。
- `provenance/local-candidate.json` 保留早期本地候选来源，`provenance/publication-20261022.json` 记录本轮发布清单与来源检查；早期记录中的未发布状态不代表当前远端状态。
- 本轮只发布本地编写的 SS 源码、指南、脱敏测试和注册说明，未复制 AS 服务器或 AE-tool 执行器实现，未上传个人运行状态/备份/配置。AS 方法参考提交保留在来源记录中。
- 本仓库目前未指定 LICENSE，不擅自为依赖、原 AS 或 AE-tool 赋予许可证；第三方依赖通过包管理器安装，不随包复制。上传、客户端安装和真实任务验收是三个不同步骤。

## 与 Grok 执行器配合

SS 负责需求、学习和产品验收，不内置付费模型调用。需要用户已授权的 Grok 委派时，可选用 [AE-tool 的 Grok skills](https://github.com/haimichenha/AE-tool/tree/improve/grok-ss-boundary-20261022/grok-skills)；该修订目前在独立分支，不把默认 `main` 当成同一版本。没有 Grok 或 AS 也能使用 SS。
