# 用户反馈与执行证据表达

> Status: AUTHORITATIVE
> Last updated: 2026-11-01
> Last verified: 2026-11-01，仅核对 Codex Rollout Master token 的既有报告字段映射；真实Worker、Host按需加载强制与token收益 NOT RUN。
> Verified against: bfab3386937f552d4c60761f32df9ea097fcb6f1 + Codex Rollout token候选；来源74d4764和经审查的JSON文案。

## 结果反馈格式（适合人来判读）

向用户汇报任务结果时使用固定结构：**一句话结论 → 任务总览 → 验收证据 → 待处理事项**。让用户能从固定位置回答四个问题：完成了什么、验证到哪一步、花了多少时间/token、还需要决定什么。

1. 任务总览是纵向两列表（项目 / 内容），固定包含：目标与交付、执行标识（task_id、attempt）、执行状态（Bridge 原始状态，注明"不等同验收通过"）、独立验收（通过/未通过/未验证/部分验证，注明责任方与范围）、接收与发布（已接收/未接收、已提交/未提交、已推送/未推送、已发布/未发布，各附证据；没有执行过的操作写"未提交/未推送/未发布"，不适用写"不适用"）、本次耗时（排队/执行/独立验证分开列，未知项写"未知"，不拼成虚假总数）、Codex 主会话 token、ZCode 执行 token、模型与推理档位、后续动作。
2. 验收证据表固定三列"检查项 / 结果 / 证据"。结果必须区分：独立实测（你真实运行过的）、worker自报（tests 等报告值）、历史记录、NOT RUN。没有独立验证时，绝不能因为 worker 报告 tests=passed 就把验收标成通过。
3. token 与模型判读规则：准备最终报告时再次运行 `node "$SKILL_DIR/scripts/codex-master-token-usage.mjs" --baseline-total <本次派发前保存的 query.total.totalTokens>`，将 `feedback_codex_tokens.note` 原样用于现有"Codex 主会话 token"行。`state: reported` 时该行只显示一个本次报告窗口消耗数字，不附加统计口径、明细、来源或时间；该数字是同一显式 Thread 的 Rollout `total` 绝对快照差，不累加 `last`，不包含报告生成后尚未发生的回复。缺少起点、Thread ID、Rollout、身份、TokenCount 或文件稳定读取时只显示"未取得"；`last`、Thread 总计、账户额度、会话总量和文本长度都不能替代本次调用统计。ZCode token 仍只显示 `zcode_result.usage` 的输入/输出/总量及完整性，缺失写"未报告"，不填 0；运行中写"截至当前未取得最终 token"，绝不能引用上一次任务的用量。模型只显示 runtime 确认值（`session_ready`/`model_selected` 的 provider_id/model_id 与 reasoning_level）；请求值标"请求"，runtime 未报告写"未报告"；请求与实际不一致时明确标出差异。
4. 运行中的反馈只报有意义的变化：当前阶段（`zcode_status.observation.activity`）、已执行时长、最后业务进展时间、阻塞项；不反复输出整份完成报告。
5. 格式：时间用分/秒，超过 1 小时用时/分/秒；token 用千位分隔整数；表格单元格内的竖线、换行、链接要转义；大批同类测试可分组，详细日志放链接不进表格；session ID、PID、OS 指纹、内部 seq 放诊断详情，不占完成反馈。任务成功但清理未确认时，两个事实分开写，不只给一个笼统 PASS/FAIL。
6. `zcode_status.observation` 是统一观测（worker/runtime 存活、activity、result、cleanup、stalled 提示）。`stalled` 只是观测提示，不代表失败，也不要因此自动重试或取消；`unknown` 不判死。
