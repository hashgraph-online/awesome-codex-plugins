/**
 * Stage/artifact/gate projector — handles stage transitions, artifact recording, and gate evaluation.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { PIPELINE_STATUS, STAGE_STATUS } from '../domain/state-constants.mts';
import {
  clone,
  ensureGate,
  ensureStage,
  refreshWorkflowSchedule,
  uniqueArtifacts,
  updateWorkflowArtifactNode,
  updateWorkflowNode,
} from './helpers.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';

export function projectStageLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.STAGE_STARTED: {
      const stage = ensureStage(state, event.data.stage);
      stage.status = STAGE_STATUS.RUNNING;
      if (!stage.startTime) stage.startTime = event.timestamp;
      state.status = PIPELINE_STATUS.RUNNING;
      state.pause = null;
      return state;
    }

    case EVENT_TYPES.STAGE_COMPLETED: {
      const stage = ensureStage(state, event.data.stage);
      stage.status = STAGE_STATUS.COMPLETED;
      stage.endTime = event.timestamp;
      return state;
    }

    case EVENT_TYPES.STAGE_FAILED: {
      const stage = ensureStage(state, event.data.stage);
      stage.status = STAGE_STATUS.FAILED;
      stage.endTime = event.timestamp;
      stage.failureReason = (event.data.reason as string | null | undefined) || null;
      state.status = PIPELINE_STATUS.FAILED;
      return state;
    }

    case EVENT_TYPES.STAGE_RETRYING: {
      const stage = ensureStage(state, event.data.stage);
      stage.status = STAGE_STATUS.RETRYING;
      stage.retryCount += 1;
      // 阶段重试是「agent 重试耗尽」之后的升级手段，必须给这一阶段的 agent 重新发预算。
      // 否则升级之后 retry-agent 仍报「已达最大重试次数」，恢复阶梯最上面一级是空的。
      for (const agent of Object.values(stage.agents ?? {})) {
        if (agent) agent.retryCount = 0;
      }
      state.metrics.retryTotal += 1;
      state.status = PIPELINE_STATUS.RUNNING;
      state.pause = null;
      return state;
    }

    case EVENT_TYPES.STAGE_SKIPPED: {
      const stage = ensureStage(state, event.data.stage);
      stage.status = STAGE_STATUS.SKIPPED;
      stage.endTime = event.timestamp;
      return state;
    }

    case EVENT_TYPES.ARTIFACT_RECORDED: {
      const stage = ensureStage(state, event.data.stage);
      stage.artifacts = uniqueArtifacts(stage.artifacts.concat(String(event.data.artifact)));
      updateWorkflowArtifactNode(
        state,
        String(event.data.artifact),
        { status: 'completed', decision: undefined, reason: 'artifact-recorded' },
        event.timestamp,
      );
      refreshWorkflowSchedule(state, event.timestamp);
      return state;
    }

    case EVENT_TYPES.GATE_EVALUATED: {
      const stage = ensureStage(state, event.data.stage);
      const gateName = String(event.data.gate);
      const checks = Array.isArray(event.data.checks) ? clone(event.data.checks) : [];
      stage.gateResults[gateName] = {
        passed: Boolean(event.data.passed),
        executedAt: event.timestamp,
        checks,
      };
      const gate = ensureGate(state, gateName);
      gate.status = STAGE_STATUS.COMPLETED;
      gate.passed = Boolean(event.data.passed);
      gate.executedAt = event.timestamp;
      gate.checks = checks;
      updateWorkflowNode(
        state,
        `gate:${gateName}`,
        {
          status: event.data.passed ? 'completed' : 'failed',
          reason: event.data.passed ? 'gate-passed' : 'gate-failed',
        },
        event.timestamp,
      );
      refreshWorkflowSchedule(state, event.timestamp);
      return state;
    }

    default:
      return null;
  }
}
