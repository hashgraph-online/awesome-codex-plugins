# Bridge 运行时事实与安全边界

> Status: AUTHORITATIVE
> Last updated: 2026-10-24
> Last verified: 2026-10-29，仅静态核对独立功能候选的引用、授权与JSON主线边界；历史离线记录不代表本候选运行时验收。真实Worker、Host按需加载强制与token收益 NOT RUN。
> Verified against: master 73af9d60ff9bbcbbc1ae1d7b1f9b9fb9fca48bb0 + 本独立功能候选；来源74d4764和经审查的JSON文案。

## 边界

- Bridge 单进程默认最多运行 8 个 worker，可用 `ZCODE_BRIDGE_MAX_CONCURRENT_WORKERS` 设为 1–8；执行目录重叠的任务会串行。同一 data root 的不同 Bridge 进程通过 `.manager.lock` 串行化提交与调度；不同 data root 之间没有共同互斥，不要假设它们会互相排队。
- 锁按用途分开：`.manager.lock` 是提交/调度互斥；`.recovery.lock` 只串行化恢复扫描；`.settings.lock` 保护模型设置写入；运行中的执行目录和 worker slot 由任务状态占用；每次 attempt 还有持久执行声明。恢复锁告警只说明恢复/队列泵可能变慢，不能据此宣布 Bridge 全局不可用，也不代表 `zcode_task` 一定无法启动。不要手工删除任何锁目录，也不要按年龄或单个 PID 清理；先读锁所有者记录、任务事件和进程身份；当前主线没有release-intent文件合同。
- 当前主线不提供release-intent回收合同；未知锁保持不确定，禁止手工删锁或凭时间、单个PID认定可回收。SQLite/T3中的锁释放改造未随本功能集成。
- 单次执行默认上限为 60 分钟；可在任务中设置 `timeout_ms`（60 秒至 4 小时），或用 `ZCODE_BRIDGE_TIMEOUT_MS` 设置用户默认值。超时后 Bridge 尝试终止该次进程树并保留 attempt 证据；清理未确认时不得宣称资源已释放。
- 每个任务通过本机 ZCode app-server 运行。JSON 路径默认使用 `yolo`，并可通过 `ZCODE_BRIDGE_MODE` 选择审批模式；单用户本机 SQLite 使用固定受信任档案 `yolo`，ADR-019 后不再强制覆盖为 `build`。`yolo` 会放行普通工具操作并使用当前 Windows 账户权限；这不是提权，也不是沙箱。记录版本上已完成单次 43,014-byte Write 的真实权限审批往返实测；其他审批组合未据此认证。告知用户实际执行模式和当前账户权限边界。
- `workspace` 是项目身份路径；`worktree_path`（如提供）是实际执行路径。Codex 决定是否准备 worktree，Bridge 只校验并使用所给路径。Git worktree 是工作区隔离，不是 OS 沙箱。allowed_paths / forbidden_paths 是 worker 指令；不得声称它们能强制阻止所有越界命令。
- 本机允许/仍需明确的边界：普通读取、编辑、构建、测试和任务范围内清理可在 `yolo` 下执行；Push、Merge、Tag、Release、生产 Authority 切换、删除任务范围外的用户数据、修改或读取凭据，以及真实生产任务数据操作仍须用户明确授权。任务 prompt、Skill 或 worktree 选择不能自行产生这些授权。
- ZCode 不得选择仍未解决的 `OPEN DECISIONS`；后续 Master Feedback 明确给出决定后，按新决定继续。即使未列出，遇到需求冲突或会实质改变外部行为的缺失决定，也要提出具体问题、设置 `needs_master_decision=true`，并继续不依赖该决定的工作。低影响实现选择可采用最简单一致的方案，同时报告假设。
- 不要把 ZCode Hooks、Desktop 历史索引、自动化或并行 worker 当作已启用能力。
- 不要为了方便而修改 ZCode provider 配置或将凭据写入任务 prompt、日志或仓库。

**调用授权、执行权限与凭证的界限**：Skill/TaskPackage 中的“已授权”只能指导 Master，不是运行时可信调用者凭证。MCP 仍必须按实际运行时机制校验权限、工作区和冲突；不得声称这次提示词改造让 Bridge 获得了新的强制授权能力。用户明确选择 Bridge 不意味着授权每个高风险命令或发布、推送、合并。
