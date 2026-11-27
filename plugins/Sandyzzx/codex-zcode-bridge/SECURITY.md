# 安全策略 / Security Policy

## 支持范围

Stable 2.0.0 是当前正式版本。项目已进入冻结维护阶段，安全修复以当前 `master` 为基线，不承诺固定响应时限或长期版本适配。

## 报告漏洞

请优先通过 GitHub 私密漏洞报告功能向仓库维护者提交问题；不要在公开 Issue、讨论区或日志中发布凭据、可利用样例或个人数据。如果私密报告功能不可用，请先开一个不含漏洞细节的 Issue，请求安全联系渠道。

请提供受影响版本、复现条件、影响范围和建议修复方式。维护者会确认收到并协商披露时间；当前没有承诺具体响应时限。

## 数据与信任边界

- MCP、独立 Executor、Worker、任务证据和工作台均在本机运行。任务 prompt、可见模型输出、工具摘要、状态、Usage、Result、Cleanup、Release 与 Wake 事实写入本地 SQLite v14 Authority；生产路径不读取或写入旧 JSON Task Authority。
- 生产路径把任务 prompt 交给本机官方 ZCode AppServer，并直接使用宿主指定的项目或 worktree；可能按用户配置连接模型服务及 MCP 工具。数据处理取决于 ZCode、所选 Provider 和启用的工具。
- Git worktree、路径清单、prompt 和 `yolo` 都不是沙箱。Bridge 以当前操作系统用户身份运行，不提供操作系统级文件、命令或网络隔离。`yolo` 不会授权 Push、Merge、Tag、Release、生产 Authority 切换、范围外删除、凭据修改或真实生产任务数据操作。
- Bridge 不写入或镜像官方 ZCode Desktop 私有的 `tasks-index.sqlite`。Bridge Task 不会因此出现在 Desktop 独立任务列表；官方 Session/AppServer 执行不受影响。
- SQLite 文件和 sidecar 的实际访问限制由父目录 ACL 和当前 Windows 用户权限决定。
- 环境变量通过白名单传递给 Worker 和 ZCode 子进程；未列入白名单的自定义代理或 Provider 环境变量不会传递。请使用受支持的 Provider 配置文件方式。
- 公开事件和摘要不转发完整 RPC payload、params、headers、未知 metadata、隐藏 reasoning 或凭据；失败 Result 的诊断有界且脱敏。

## English summary

Security fixes target the current `master` branch. Stable 2.0.0 is the formal release; this frozen project does not promise a fixed response time or long-term support.

Please report vulnerabilities through GitHub's private vulnerability reporting feature when available. Do not publish credentials, exploit details, or personal data in public issues, discussions, or logs. If private reporting is unavailable, open an issue without vulnerability details and request a secure contact channel.

Bridge runs with the current operating-system account. Task paths, Git worktrees, and `yolo` are not security sandboxes. The production Authority is local SQLite v14; Bridge does not mirror the private ZCode Desktop task index.
