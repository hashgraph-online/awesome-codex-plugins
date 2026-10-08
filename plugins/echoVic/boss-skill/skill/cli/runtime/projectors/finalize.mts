/**
 * Finalizes the materialized state — computes derived metrics, pipeline status,
 * and normalizes state after all events have been projected.
 */
import { PIPELINE_STATUS, STAGE_STATUS } from '../domain/state-constants.mts';
import {
  ensureConversationSections,
  normalizePlugins,
  refreshWorkflowSchedule,
} from './helpers.mts';
import type { ExecutionState } from './types.mts';

function computeDurationSeconds(start: string | null, end: string | null): number | null {
  if (!start || !end) return null;
  return Math.max(0, (new Date(end).getTime() - new Date(start).getTime()) / 1000);
}

export function finalizeState(state: ExecutionState): ExecutionState {
  if (!state.createdAt) state.createdAt = state.updatedAt || new Date().toISOString();

  // Aggregate metrics from stages
  const stageEntries = Object.entries(state.stages ?? {});
  const stages = stageEntries.map(([, stage]) => stage);
  const stageCount = stages.length;

  const stageTimings: Record<string, number> = {};
  let totalSeconds = 0;
  for (const [stageId, stage] of stageEntries) {
    const duration = computeDurationSeconds(stage.startTime, stage.endTime);
    if (duration != null) {
      stageTimings[stageId] = duration;
      totalSeconds += duration;
    }
  }
  state.metrics.stageTimings = stageTimings;
  state.metrics.totalDuration = stageCount > 0 && totalSeconds > 0 ? totalSeconds : null;

  if (stageCount > 0) {
    state.metrics.meanRetriesPerStage = Number((state.metrics.retryTotal / stageCount).toFixed(2));
  } else {
    state.metrics.meanRetriesPerStage = 0;
  }
  state.metrics.revisionLoopCount = Number(
    state.feedbackLoops && Number.isFinite(Number(state.feedbackLoops.currentRound))
      ? state.feedbackLoops.currentRound
      : 0,
  );

  let completedCount = 0;
  let failedCount = 0;
  for (const stage of stages) {
    if (!stage.agents) continue;
    for (const agent of Object.values(stage.agents)) {
      if (agent.status === 'completed') completedCount += 1;
      else if (agent.status === 'failed') failedCount += 1;
    }
  }
  state.metrics.agentSuccessCount = completedCount;
  state.metrics.agentFailureCount = failedCount;

  const gateStates = Object.values(state.qualityGates ?? {}).filter((gate) => gate.passed !== null);
  if (gateStates.length > 0) {
    const passedCount = gateStates.filter((gate) => gate.passed).length;
    state.metrics.gatePassRate = Number(((passedCount / gateStates.length) * 100).toFixed(2));
  } else {
    state.metrics.gatePassRate = null;
  }

  const stageStatuses = Object.values(state.stages ?? {}).map((stage) => stage.status);
  if (
    stageStatuses.length > 0 &&
    stageStatuses.every(
      (status) => status === STAGE_STATUS.COMPLETED || status === STAGE_STATUS.SKIPPED,
    )
  ) {
    state.status = PIPELINE_STATUS.COMPLETED;
  } else if (state.pause?.paused === true) {
    // 显式暂停压过「有阶段在跑」的推断。此前顺序相反，于是在唯一值得暂停的时刻
    // （某个阶段正在跑）status 仍被推导为 running，连带两个守卫一起失效：
    // 重复 pause 不再被拒、`update-stage running` 的自动恢复也不再触发。
    state.status = PIPELINE_STATUS.PAUSED;
  } else if (
    stageStatuses.some(
      (status) => status === STAGE_STATUS.RUNNING || status === STAGE_STATUS.RETRYING,
    )
  ) {
    state.status = PIPELINE_STATUS.RUNNING;
  }

  state.plugins = normalizePlugins(state.plugins);
  if (!state.pluginLifecycle || typeof state.pluginLifecycle !== 'object') {
    state.pluginLifecycle = { discovered: [], activated: [], executed: [], failed: [] };
  }
  state.pluginLifecycle.discovered = normalizePlugins(state.pluginLifecycle.discovered);
  state.pluginLifecycle.activated = normalizePlugins(state.pluginLifecycle.activated);
  state.pluginLifecycle.executed = Array.isArray(state.pluginLifecycle.executed)
    ? state.pluginLifecycle.executed
    : [];
  state.pluginLifecycle.failed = Array.isArray(state.pluginLifecycle.failed)
    ? state.pluginLifecycle.failed
    : [];
  state.metrics.pluginFailureCount = state.pluginLifecycle.failed.length;
  ensureConversationSections(state);
  refreshWorkflowSchedule(state, state.updatedAt);
  state.conversationMetrics.unresolved = state.conversations.threads.filter(
    (thread) => thread.status !== 'closed' && thread.status !== 'materialized',
  ).length;
  return state;
}
