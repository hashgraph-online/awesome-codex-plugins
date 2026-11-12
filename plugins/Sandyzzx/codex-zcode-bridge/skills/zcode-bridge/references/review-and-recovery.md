# 独立验收、返工与恢复

> Status: AUTHORITATIVE
> Last updated: 2026-11-11
> Last verified: 2026-11-11，核对当前 Result/Continue/Cancel schema、SQLite Hold 合同与报告修复 Prompt；真实生产恢复 NOT RUN。
> Verified against: 372e90622772b070357a278f1da3dea58fa42dee（基线；本候选离线证据见 docs/research/master-skill-simplification-20261111.md）

## 验收与接收

1. 在事件报告的实际执行目录检查 Git 状态、完整 diff、实际文件和适用验证。`whole_task` 验收整个授权任务；`staged` 验收当前阶段及交接条件，明确后续目标未完成。验证命令和分层遵循当前项目自己的权威说明，不把 Worker 自报、工具成功或 `completed` 当作验收。
2. AgentReport 的 files_changed/tests/decisions 是规范化声明。Master 独立区分实际运行、Worker 自报、历史记录和 NOT RUN；没有独立验证时不写验收通过。
3. 审查通过后，按用户授权接收所需改动；保留既有用户改动、检查冲突并复验。Bridge 不自动应用、合并、删除 worktree，也不自动提交、推送或创建 PR。
4. 结果不达标时汇总全部失败证据，用 `zcode_continue` 做一次完整返工。保持原策略和授权，只收紧实际失败维度，不追加无关规则、不拆成微任务、不无限原样重派或自动换模型。
5. `invalid_agent_report` 且执行已完成时，检查 `report_candidate`、原始 `zcode_output` 和实际 diff；续作只修复 JSON 报告，不编辑文件或重跑测试。缺失决定只能基于证据补齐，无法确认则 `needs_master_decision=true`。

## 失败、取消与 Hold

- `failed` 用 `zcode_result.error_code` 判断原因，不用 feedback 标签替代。`cleanup_failed` 或 `cleanup_unverified` 是清理事实，与代码验收分开；后续 `observation.cleanup=verified` 只说明取得退出证据，不改写历史失败。
- 对已知 `failed + cleanup_unverified` Task，先报告可确认的 workspace、Task、Attempt 和原因。核心 MCP 没有 Bridge Task/Attempt 全局枚举工具；可选 Ledger 只能枚举其管理的 ProjectTask，不能发现所有 Bridge 任务。`zcode_status` 不返回 workspace；缺失写未知，不猜测。
- `zcode_cancel` 只接受 `{ task_id }`，可能按原 PID/start fingerprint 终止仍存活 Worker，没有 dry-run/authorize 参数。用户授权的是当前明确 Recovery 操作，不是无限期终止权限；必须先取得用户的明确授权。获准后同一 Operation 一次只发起一个 cancel，调用后读 `zcode_status`。
- Recovery 只有原身份、recorded-tree claimant、interaction 状态和 Operation CAS 全部验证成功才释放；失败、未知或响应丢失保持 Hold。停止失败后先重新核对原 Worker 身份和状态，原授权范围内可再次尝试；目标身份或操作范围变化时重新取得用户授权。不得并发重复发出终止信号，也不得拼接底层清理命令、重放 Prompt、创建 Attempt 或手工改 SQLite 绕过。
- Recovery 成功后先检查原 workspace Git diff/WIP，再讨论是否创建新 Attempt；不自动 reset、clean、覆盖 checkout 或删除用户源码。单路径 Hold 不阻塞其他独立 workspace。
- 用户取消时调用 `zcode_cancel` 并确认终态。`zcode_usage_exhausted` 表示本次执行中断：停止编辑、派发、续作和自动重试，告知用户并等待确认额度恢复。
