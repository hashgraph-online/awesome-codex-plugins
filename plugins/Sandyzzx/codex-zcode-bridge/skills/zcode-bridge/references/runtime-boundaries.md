# Bridge 运行时事实与边界

> Status: AUTHORITATIVE
> Last updated: 2026-11-11
> Last verified: 2026-11-12，核对 Stable 1.7.0 SQLite-only 架构、当前接口/项目状态、固定本机 profile 与模型路由幂等；跨平台真实运行 NOT RUN。
> Verified against: 372e90622772b070357a278f1da3dea58fa42dee（基线；本候选离线证据见 docs/research/master-skill-simplification-20261111.md）

- 生产只有 SQLite v14 Task Authority、一个 Lifecycle Manager 和 Worker→官方 app-server 链。旧 JSON TaskStore/Manager/Worker、CLI Adapter、GitWorktreeProvider 和恢复 roster 已退役；旧 `.tasks`/JSON 锁不是恢复源，不扫描、导入或手工删除。
- Capacity、永久 Claim 和路径互斥以 SQLite 为准；Result、进程退出、树 Cleanup 和 Release 是独立事实。无 Result 的 running 在重启后仍占用；缺 Receipt、句柄、超时或回调异常都不授权重派。
- 启动 Recovery 只读核对，不因 alive/exited/unknown 写持久 Hold。未知 Hold 不按时间或 PID 消失清除；当前没有 release-intent 回收合同，也不引入新状态机。
- 单次执行预算为 Task override > Host 持久配置/环境 > 60 分钟，范围 60 秒至 4 小时；清理另有独立预算。超时后保留 Attempt 证据，清理未确认不宣称资源已释放。
- 受信任单用户本机生产 profile 当前映射 app-server `yolo`：普通读取、编辑、构建、测试和任务范围内清理可用当前 OS 账户自动执行。这不是提权，也不是 OS 沙箱；具体权限审批仍以用户明确许可为准。
- `workspace` 是项目身份，`worktree_path` 是 Host 已准备的实际执行目录。`allowed_paths`/`forbidden_paths` 是 Worker 指令，不是强制隔离；ZCode Hooks、Desktop 索引、自动化、并行 worker 或 Companion 能力未启用时不得当作事实。
- Push、Merge、Tag、Release、生产 Authority 切换、任务外用户数据删除、凭据读取/修改和真实生产数据操作仍须用户明确授权。Skill/TaskPackage/worktree 不是可信凭证；MCP 和运行时仍按实际机制校验身份、权限和冲突。
- Provider 的 retryable/statusCode 不证明请求未被接受；429、5xx 和网络错误不自动重发。明确 `zcode_usage_exhausted` 通知 Master 停止。不要为绕过问题修改 provider 配置或把凭据写入任务、日志、事件或仓库。
- 诊断先查同一 task/attempt 的 status、result、events。需要实现细节时读仓库 `docs/INTERFACES.md` 对应章节，再按 `docs/decisions/README.md` 选择当前有效 ADR；普通委派不预读 ADR/archive/bundle。
