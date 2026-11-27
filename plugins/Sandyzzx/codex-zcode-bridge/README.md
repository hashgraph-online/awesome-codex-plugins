# ZCode Bridge

**Codex 规划与验收，ZCode 执行，Bridge 让任务持续推进。**

本地异步 Agent 协作插件。Codex 明确派发有边界的任务，独立 Executor 管理执行，官方 ZCode AppServer 完成模型调用与工具操作，Codex 独立验收。

本文描述 Stable 2.0.0 插件功能。

## 安装与使用

环境：Windows x64、Node.js 24.16.0（已验证）、Git、支持插件的 Codex，以及已安装并登录的官方 ZCode Desktop。

安装 Stable 2.0.0：

```sh
codex plugin marketplace add https://github.com/Sandyzzx/codex-zcode-bridge.git --ref codex-zcode-bridge-v2.0.0
codex plugin add codex-zcode-bridge@codex-zcode-bridge
```

同一 Codex 安装只启用一份 Bridge。安装后开启新会话、审查 SessionStart Hook；配置失败时请让 Codex 运行 `zcode_doctor`。

示例：使用 ZCode Bridge，通过 Coding Plan 的当前可用模型修复指定测试，仅修改相关代码，由 Codex 审查结果，不提交或推送。

## 任务生命周期

- `zcode_task` 提交任务；回执可提供本地任务工作台链接。
- `zcode_status`、`zcode_feedback`、`zcode_events`、`zcode_result` 查看状态与证据。
- `zcode_continue` 用于验收返工、受控恢复或必要决定；不等同于必然恢复旧 ZCode Session。
- `zcode_cancel` 与 `zcode_interaction_reply` 处理受支持的取消与交互。
- `zcode_model_catalog` 实时读取官方运行时目录；`zcode_default_model`、`zcode_set_default_model`、`zcode_clear_default_model` 管理默认选择。

Worker `completed` 不等于 Codex 验收通过。必须独立核对实际改动、测试与 Result。

## 套餐、模型与费用

Coding Plan 使用授权的官方账户路径；稳定版发布准备期间已完成 GLM-5.4 / low 真实执行。Start Plan 技术适配及 `-StartPlan` 别名保留，当前账户真实执行尚未验证，且须遵守官方访问限制。

显式套餐选择优先；仅指定模型时，两种套餐均提供同一型号才优先 Start Plan，仅一方提供时选择该方。不可用时明确失败，不静默降级。Bridge 不维护模型名单，不保证任何额外折扣或使用量。

## 本地 Executor 与工作台

任务执行由独立 Executor 管理，工作台通过同一控制通道访问 SQLite；不会建立第二份 Authority。任务回执提供实际可用的控制台链接（若不可用会报告原因）。浏览器关闭不取消已经受理的任务。

在插件安装目录可使用：

```powershell
node dist/task-cli.mjs executor start
node dist/task-cli.mjs executor status
node dist/task-cli.mjs task list --limit 20
node dist/task-cli.mjs task status <task_id>
node dist/task-cli.mjs task console-url <task_id>
node dist/task-cli.mjs executor stop
```

`executor stop` 只允许空闲安全关闭。已有 Executor 将被复用；异常任务的用户授权清理仅释放该任务逻辑占用，不证明操作系统进程已停止，也不会自动重派。请确认风险后再授权。

安装并启用 2.x 插件即默认开启 Auto Wake，可能产生额外 Codex 用量；可在 Diagnostics 中关闭。Queue ACK 不等于实际新 Turn。工作台仅绑定本地回环地址，打开页面本身不调用模型；授权 Runtime 探针和成本检查需显式触发。

## 数据与安全

当前任务权威存储仅支持 SQLite v14；旧 Schema 非破坏性拒绝。升级前备份数据，勿手工修改数据库或删除锁。详见 [运行环境和升级指南](../../docs/ZCODE_RUNTIME.md)。

Bridge 以当前用户权限运行，Worktree 及 `allowed_paths` / `forbidden_paths` 不是安全沙箱。Push、Merge、Tag、Release、范围外删除、凭据修改等仍需明确授权。不在提示词中放入凭据或私钥，不绕过官方访问限制。

[中文主 README](../../README.zh-CN.md) · [English](../../README.md) · [安全说明](SECURITY.md) · [任务工作台](../../docs/WEB_CONSOLE.md)

## 维护状态

本项目仍保持开源，但不再保证及时维护或版本适配。详见[作者寄语](../../README.zh-CN.md#写在最后)。
