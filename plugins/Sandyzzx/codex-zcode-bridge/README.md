# Zcode Bridge

把有明确边界的开发任务从 Codex 交给本机官方 ZCode Agent Runtime，在 Codex 中跟进进度，并独立审查实际改动后再决定是否接受。

当前稳定版本为 `1.7.0`，包含 SQLite-only 编排以及 Start Plan 与 Coding Plan 集成。

## 支持范围

| 套餐 | 当前支持 |
| --- | --- |
| Z.ai Start Plan | 只读发现官方账户凭据，执行实时模型权益检查，并通过单任务私有凭据 Lease 向官方 Runtime 交付认证。 |
| Z.ai Coding Plan | 使用既有的官方 Coding Plan 账户/API Key 路径。 |

两条路径都通过官方 ZCode AppServer 执行。Start Plan 的真实证据目前仅覆盖 Windows、官方 AppServer `0.17.1` 和 `GLM-5.3-Flash`；其他模型与平台仍取决于官方 Registry、账户权益和实际环境，不能从单一模型的成功推广为全部 Start Plan 模型已验证。

## 使用前

Stable `1.7.0` 需要 Node.js `>=24.16.0 <25`、Git、已安装并登录的 ZCode，以及支持插件 Marketplace 的 Codex。

添加 Stable Marketplace 并安装 **Zcode Bridge**。桌面应用中可先在 CLI 注册 Marketplace，再到 **Plugins Directory** 安装；之后开启新对话并检查、信任插件的 `SessionStart` Hook。

```sh
codex plugin marketplace add https://github.com/Sandyzzx/codex-zcode-bridge.git --ref codex-zcode-bridge-v1.7.0
codex plugin add codex-zcode-bridge@codex-zcode-bridge
```

更新 Stable Marketplace：

```sh
codex plugin marketplace upgrade codex-zcode-bridge
```

固定到当前 Stable 快照：

```sh
codex plugin marketplace add https://github.com/Sandyzzx/codex-zcode-bridge.git --ref codex-zcode-bridge-v1.7.0
```

Marketplace 安装不需要克隆源码或运行 `npm install`；Node.js 和 ZCode 需另行安装。

## 派发和验收

只有当用户明确要求使用 ZCode/Bridge，或既有明确授权覆盖当前目标时，Codex 才应派发任务。普通开发请求不会自动转交 ZCode。

Codex 作为 Master 定义目标、约束、允许范围和验收条件，并选择整任务或分阶段交付。ZCode 在给定 Workspace 中执行工作；如果调用方创建了 Git Worktree，Bridge 使用该现有目录，但不会自行创建、选择或删除 Worktree。

可用 MCP 工具：

- `zcode_task`、`zcode_status`、`zcode_feedback`、`zcode_events`、`zcode_result`
- `zcode_continue`、`zcode_cancel`、`zcode_interaction_reply`
- `zcode_doctor`、`zcode_model_catalog`、`zcode_default_model`、`zcode_set_default_model`、`zcode_clear_default_model`

`completed` 只表示 Worker 执行结束并规范化了报告，不表示 Codex 已接受代码。必须检查实际 Diff、测试和 Result。`zcode_continue` 仅用于验收返工、必要决定、受控恢复或报告修复，不用于普通的分步调度。

遇到安装或启动问题时，可调用只读诊断工具 `zcode_doctor`；它不会启动 ZCode Session。模型目录可通过 `zcode_model_catalog` 查询；Start Plan 条目使用 `<ModelId>-StartPlan` 别名，并在任务执行时进行实时权益检查。

## 安全边界

Bridge 以当前 Windows 用户权限运行。固定 `yolo` 执行档案允许普通读取、编辑、构建、测试和任务范围内清理，但这不是提权或恶意进程隔离机制。

Push、Merge、Tag、Release、生产 Authority 切换、任务范围外删除、凭据修改和真实生产任务数据访问仍需用户明确授权。任务 Prompt、Skill、路径列表和 Worktree 选择不会自行产生这些授权。

Git Worktree 只是工作目录布局，不是 OS 沙箱。`allowed_paths` 和 `forbidden_paths` 是任务指令，不是强制访问控制。派发前应检查 ZCode 可见的工作区内容，不要在 Prompt 中放入凭据、JWT、私钥或敏感账户数据。

Start Plan 不支持绕过 CAPTCHA 或 unusual activity；需要用户交互的官方账户流程应由用户在官方 ZCode 客户端中处理，Bridge 在无法确认权益时 fail-closed。

## SQLite Authority

Bridge 的任务权威存储是 SQLite。首次启动会创建并验证：

```text
${LOCALAPPDATA}\CodexZCodeBridge\state\bridge.sqlite
```

启动时发现有效的 Schema v13 Authority 后，Bridge 会在既有跨进程 bootstrap 锁内执行受控副本升级到 v14，并保留原库作为同目录 v13 备份。损坏或非 v13 数据库继续 fail-closed；不要通过清除 Hold 强制启动。完整说明见仓库的 [Runtime 指南](../../docs/ZCODE_RUNTIME.md) 和 [中文主 README](../../README.zh-CN.md)。

## 可选后台等待器

支持后台命令完成通知的 Host 可运行插件包内的只读 `dist/wait-task.mjs`。它观察同一 SQLite Attention Core，不批准、取消或修改任务状态；通知仍取决于 Host 的生命周期。
