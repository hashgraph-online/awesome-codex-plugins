# 独立验收、接收与受控返工

> Status: AUTHORITATIVE
> Last updated: 2026-10-24
> Last verified: 2026-10-29，仅静态核对独立功能候选的引用、授权与JSON主线边界；历史离线记录不代表本候选运行时验收。真实Worker、Host按需加载强制与token收益 NOT RUN。
> Verified against: master 73af9d60ff9bbcbbc1ae1d7b1f9b9fb9fca48bb0 + 本独立功能候选；来源74d4764和经审查的JSON文案。

## 审查与接收改动

**完整交付门**：`whole_task` 的 Worker 在授权范围内自主调查、实现、测试、修复并重测；`staged` 的 Worker 则自主完成本阶段完整成果并停止，不得顺带执行未批准的下一阶段。Master 按本任务实际验收边界独立检查，Worker 自报、工具成功或 `completed` 均不等于验收通过。只有明确新证据支持时才重新规划或返工；不要靠加长提示词原样循环重派。


1. 在事件报告的实际执行目录检查 Git 状态、完整 diff、实际文件和测试。对照用户目标、允许/禁止路径和验收标准逐项核实。`whole_task` 验收整个授权任务，不能凭局部测试宣布整体完成；`staged` 验收当前阶段交付和交接条件，明确列出尚未完成的后续目标。
2. 不能仅相信 AgentReport.files_changed、ZCode 报告的测试状态或模型输出；独立运行适用的验收命令。
   - 日常改动独立运行适用的验收命令时优先使用 `npm run test:affected`，核对它输出的 changed files、domains、selected/not selected 理由和压力测试结论。
   - 只有变更真实命中影响映射中的压力边界才接受/要求压力测试；`STRESS_TESTS_NOT_APPLICABLE` 必须有可核对影响域，不能作为跳过受影响压力测试的理由。
   - R4、发布候选、关键生产架构切换或测试基础设施变更要求 `npm run test:full` 或等价完整串行回归；不得接受减少测试、新增 SKIP或改动断言后的“完整回归”。
3. 若执行目录是 worktree，在审查通过后由 Codex 按用户授权把所需改动接收到项目工作区；先保留项目中已有的用户改动、检查冲突，再复查并运行验收。若直接在项目根目录执行，则在同一目录审查。
4. Bridge 不会自动应用、合并或删除 worktree。不要在审查及接收改动前删除 Codex 准备的 worktree，也不要自动提交、推送或创建 PR。
5. 如果结果未达标，先集中整理全部验收失败点和证据，再调用 zcode_continue 做一次完整返工，复用同一 ZCode session 和原执行目录。保持当前策略与授权范围，只收紧实际失败的维度（如遗漏约束、缺少测试或错误决定边界），不无差别追加整段规则；不要把返工拆成连续的微任务，也不要用续作推进正常实现的下一步。不得自动原样重派、切换模型或无限重试。任务运行期间若用户取消，调用 zcode_cancel 并确认终态。
6. 如果结果为 `invalid_agent_report` 且执行工作已完成，先检查 `report_candidate`、原始 `zcode_output` 和实际 diff；续作提示只要求修复 JSON 报告，不要再次编辑或重跑测试。缺少的决定字段必须基于证据补齐，无法确认时设 `needs_master_decision=true`。
7. 任务为 failed 时用 `zcode_result.error_code` 确认原因，不仅凭 `zcode_feedback` 的失败标签判断代码失败。`cleanup_failed` 是当时清理未能确认；后续 `zcode_status.observation.cleanup=verified` 表示已取得退出证据，原失败仍保留。分别报告两个事实，再独立验收代码。新鲜查询为 unknown 或 unverified 时不自行删除锁、改历史状态或另起同目录任务；旧不可读取锁需要独立诊断，不能按时间删锁。
   - 对已知 SQLite `failed + cleanup_unverified` Task，按入口的 **HOLD RECOVERY POLICY** 报告已能确认的 workspace、Task、Attempt 和原因，并先取得用户对可能终止仍存活 Worker 的明确授权。MCP 无 Task 枚举工具；`zcode_status` 不返回 workspace，因此信息缺失时须明确标为未知。当前 `zcode_cancel` 仅接受 `{ task_id }`，成功返回 Task status record；它可能执行原身份绑定的进程树终止，不提供单独的 dry-run/authorize 参数。未授权不得调用。
   - 获准后调用 `zcode_cancel`，再读取 `zcode_status`。成功才代表该次恢复完成，不代表历史 cleanup failure 未发生；不确定或失败时保留占用，检查其他独立 workspace 是否仍可工作。成功后先检查 workspace Git diff/WIP，再决定是否发起新 Attempt。
8. 若 `zcode_result.error_code` 或失败事件为 `zcode_usage_exhausted`，这表示本次 ZCode 执行已中断：立即停止当前任务，不要继续编辑、派发、调用 `zcode_continue` 或自动重试；马上明确告知用户额度已耗尽、当前任务已中断，并等待用户确认额度恢复后再继续。
