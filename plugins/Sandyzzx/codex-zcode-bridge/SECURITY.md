# 安全策略 / Security Policy

## 支持版本

安全修复面向当前 `master` 分支。该项目仍处于早期开发阶段，尚未承诺长期支持某个发布版本。

## 报告漏洞

请优先通过 GitHub 私密漏洞报告功能向仓库维护者提交问题；不要在公开 Issue、讨论区或日志中发布凭据、可利用样例或个人数据。如果私密报告功能不可用，请先开一个不含漏洞细节的 Issue，请求安全联系渠道。

请提供受影响版本、复现条件、影响范围和建议修复方式。维护者会确认收到并协商披露时间；当前没有承诺具体响应时限。

## 数据与信任边界

- MCP 服务、worker、任务证据和临时 worktree 均在本机运行。任务 prompt、可见模型输出、工具摘要、状态和结果写入本地 `.tasks/`。
- 生产路径将任务 prompt 交给本机 ZCode app-server，并直接使用宿主指定的项目或 worktree；可能按用户配置连接模型服务及 MCP 工具。具体数据处理取决于 ZCode、所选 provider 和所启用的工具。
- Git worktree 不是沙箱。ZCode session 默认使用 `yolo` 模式，也可配置为 `plan`、`build` 或 `edit`；所有模式都以当前操作系统用户身份运行。Bridge 不提供操作系统级文件、命令或网络沙箱。
- Bridge 会 best-effort 写入 ZCode Desktop 的 `tasks-index.sqlite`，其中包括 session ID、worktree 路径、模型/供应商标签和 Bridge task ID；不写入任务目标或 prompt。数据库 schema 不匹配、被锁定或不可写时只记录事件告警，不影响 ZCode。
- 仅 legacy GitWorktreeProvider 有 Git 快照及启发式凭据排除；当前生产路径不创建快照，也不承诺过滤执行目录中的凭据。legacy 路径的 Git clean filters 可能在排除步骤前运行。
- POSIX 下 `.tasks/` 使用 `0700` 目录和 `0600` 文件权限。Windows 的实际访问限制由父目录 ACL 决定。
- 环境变量通过白名单传递给 worker 和 ZCode 子进程；未列入白名单的自定义代理或 provider 环境变量不会传递。请使用受支持的 provider 配置文件方式。

## Security policy

Security fixes target the current `master` branch. The project is in early development and does not yet promise long-term support for a particular release.

Please report vulnerabilities through GitHub's private vulnerability reporting feature when available. Do not publish credentials, exploit details, or personal data in public issues, discussions, or logs. If private reporting is unavailable, open an issue without vulnerability details and request a secure contact channel.

Include the affected version, reproduction conditions, impact, and a suggested fix. The maintainers will acknowledge the report and coordinate disclosure; no response-time commitment is currently made.
