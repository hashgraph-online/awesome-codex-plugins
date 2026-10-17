/**
 * 子代理状态上报的结构化契约。
 *
 * 取代 `[BOSS_STATUS]` 散文块 + 正则解析：状态是控制流输入，
 * 必须在工具层校验，而不是从自然语言里猜。非法值直接报错让调用方重试，
 * 而不是静默降级成 failed。
 */

export const AGENT_REPORT_STATUS = Object.freeze({
  DONE: 'DONE',
  DONE_WITH_CONCERNS: 'DONE_WITH_CONCERNS',
  NEEDS_CONTEXT: 'NEEDS_CONTEXT',
  BLOCKED: 'BLOCKED',
  REVISION_NEEDED: 'REVISION_NEEDED',
} as const);

export type AgentReportStatus = (typeof AGENT_REPORT_STATUS)[keyof typeof AGENT_REPORT_STATUS];

export const AGENT_REPORT_STATUS_VALUES: readonly AgentReportStatus[] = Object.freeze(
  Object.values(AGENT_REPORT_STATUS),
);

/** 视为「推进成功」的状态；其余一律映射为 failed。 */
const SUCCESS_STATUSES: ReadonlySet<string> = new Set<string>([
  AGENT_REPORT_STATUS.DONE,
  AGENT_REPORT_STATUS.DONE_WITH_CONCERNS,
]);

export function isAgentReportStatus(value: unknown): value is AgentReportStatus {
  return (
    typeof value === 'string' && (AGENT_REPORT_STATUS_VALUES as readonly string[]).includes(value)
  );
}

/**
 * 把上报状态映射为流水线 agent 状态。
 * 注意：仅 DONE / DONE_WITH_CONCERNS 算完成——子代理自报完成不等于验收通过，
 * 门禁仍需独立评估（SKILL.md 不变量）。
 */
export function toPipelineAgentStatus(status: AgentReportStatus): 'completed' | 'failed' {
  return SUCCESS_STATUSES.has(status) ? 'completed' : 'failed';
}
