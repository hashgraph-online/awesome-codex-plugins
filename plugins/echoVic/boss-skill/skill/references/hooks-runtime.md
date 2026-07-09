# Hooks Runtime

本文件保存 Boss hook 行为。只有调试 hooks、安装适配、或解释生命周期行为时才需要读取。

## Hook Dispatch

所有 hooks 脚本使用 Node.js 实现，通过 `boss hooks run` 中间件统一调度。

hooks 定义在：
- `skill/hooks/claude/hooks.json`
- `skill/hooks/codex/hooks.json`
- `.claude/settings.json`

## Hook Profile

| 环境变量 | 说明 | 值 |
|----------|------|-----|
| `BOSS_HOOK_PROFILE` | Hook 运行级别 | `minimal` / `standard`（默认）/ `strict` |
| `BOSS_DISABLED_HOOKS` | 禁用指定 hook | 逗号分隔 Hook ID，如 `post:bash:context,notification:log` |

## Hook 列表

| Hook ID | 事件 | Profile | 作用 |
|---------|------|---------|------|
| `session:start` | SessionStart (startup) | all | 检测活跃流水线 + 加载上次 session 状态 |
| `session:resume` | SessionStart (resume) | all | 恢复会话时提示未完成流水线 |
| `pre:write:artifact-guard` | PreToolUse (Write/Edit) | standard,strict | 阻止直接编辑 execution.json；写入产物时校验阶段状态 |
| `post:write:artifact-track` | PostToolUse (Write) | standard,strict | 文件写入 `.boss/` 后追加产物事件并物化 execution.json |
| `post:bash:context` | PostToolUse (Bash) | standard,strict | 捕获门禁/测试/harness 命令执行 |
| `subagent:start` | SubagentStart | all | 子 Agent 启动时注入当前流水线阶段上下文 |
| `subagent:stop` | SubagentStop | all | 子 Agent 结束后记录 agent-log.jsonl |
| `stop:pipeline-guard` | Stop | standard,strict | Agent 停止时检查 running 阶段，阻止过早退出 |
| `notification:log` | Notification (async) | all | 记录通知到 notifications.jsonl |
| `session:end` | SessionEnd | all | 保存 `.boss/.session-state.json` 并生成报告 |

## Session 记忆持久化

- SessionEnd 保存 feature、pipeline 状态、阶段摘要、cwd/worktree、时间戳。
- SessionStart 加载 `.boss/.session-state.json` 恢复上下文。

