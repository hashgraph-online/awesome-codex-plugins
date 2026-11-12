# 执行监控、互动与审批

> Status: AUTHORITATIVE
> Last updated: 2026-11-11
> Last verified: 2026-11-11，核对当前 events/attention/interaction schema、固定本机执行 profile 与 Codex token 只读脚本；真实 Worker/Host 行为 NOT RUN。
> Verified against: 372e90622772b070357a278f1da3dea58fa42dee（基线；本候选离线证据见 docs/research/master-skill-simplification-20261111.md）

## 跟进

0. 首次派发前把 `SKILL_DIR` 设为当前 `SKILL.md` 所在目录，运行 `node "$SKILL_DIR/scripts/codex-master-token-usage.mjs"`，保存 `query.total.totalTokens`。脚本只读取 `CODEX_THREAD_ID` 指向的本机 Codex Rollout，不扫描其他会话、不调用模型；`thread_id_missing`、`rollout_not_found`、`thread_identity_unverified`、`no_token_count` 或 `file_changed` 时保留状态，不猜测 Thread。
1. `zcode_task` 返回后立即调用 `zcode_events`（`after_seq: 0, view: "summary"`），报告 `workspace_ready` 的 project/execution path、worktree 与 queued/running。按 `next_seq` 继续，直到 `turn_started`、启动失败或终态；不忙轮询。
2. `turn_started` 后向用户报告项目根目录、实际执行目录、session ID、runtime 报告的 provider/model/reasoning 和执行模式。模型和档位只读 `session_ready` 或 `model_selected` 的 runtime details；只有请求值时标“请求”，缺失写“未报告”。生产受信任本机 profile 当前映射 `yolo`：普通工具可自动执行并使用当前 OS 账户，不是沙箱。
3. 运行期间用 `after_seq` 增量读取，默认 `view: "summary"`，需要完整请求时改 `raw`；`wait_ms` 可用 10000–25000。只等待 Pending、终态或 Attempt 变化时传 `wait_for: "attention"`，以返回的嵌套 `attention` 为决策事实；普通事件不会唤醒该模式。
4. 心跳、工具事件和文件变化分别证明不同事实；没有输出或结果时不推断测试通过、源码已还原或任务完成。`stalled` 只是观测提示；短静默先查业务事件、文件变化、交互、心跳和进程身份，不立即取消或重派。
5. `zcode_feedback` 是当前 Attempt 的简洁来源标注快照；`last_observed` 不是实时工具状态，`interaction: not_observed` 不代表没有交互。终态后先读 feedback，再按需读 result；两者都不替代独立验收。
6. 安装、运行时或 provider 配置异常先调用只读 `zcode_doctor`；`unknown` 不是通过。诊断不得读取或写入凭据。

## 互动

收到 `interaction_requested` 时读取持久请求的 method、工具、理由、输入、选项或问题；若因 `max_bytes`/`scan_incomplete` 不完整，先提高读取预算，内容不全不得放行。只有用户明确授权该具体操作才能 `zcode_interaction_reply` `allow`；worktree、`yolo`、TaskPackage 或历史授权都不构成许可。

用户输入只依据已知事实或用户明确回答。AskUserQuestion 从 `details.params.questions`（嵌套工具输入时为 `details.params.input.questions`）读取；`answers` 以每个问题完整原文为键，不用 header/选项标签替代。回复后继续观察，Bridge 校验请求与原 Worker 通道身份，失败时保持未决并报告。
