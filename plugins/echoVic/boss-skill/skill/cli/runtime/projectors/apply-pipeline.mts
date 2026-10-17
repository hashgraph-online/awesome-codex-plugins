/**
 * Pipeline lifecycle projector — handles pipeline init, pause, resume, and pack applied events.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { PIPELINE_STATUS } from '../domain/state-constants.mts';
import {
  clone,
  defaultExecutionState,
  isNonEmptyString,
  isObject,
  mergeDeep,
  refreshWorkflowSchedule,
  updateWorkflowNode,
} from './helpers.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';

function applyPipelineResumedWorkflow(state: ExecutionState, event: RuntimeEvent): void {
  if (!state.workflow) return;
  const decisions = Array.isArray(event.data.nodes) ? event.data.nodes : [];
  state.workflow.resumedFromRunId =
    typeof event.data.fromRunId === 'string'
      ? event.data.fromRunId
      : state.workflow.resumedFromRunId;

  for (const decision of decisions) {
    if (!isObject(decision) || !isNonEmptyString(decision.id)) continue;
    const status =
      decision.decision === 'reuse'
        ? 'reused'
        : decision.decision === 'skip'
          ? 'skipped'
          : 'pending';
    updateWorkflowNode(
      state,
      decision.id,
      {
        status,
        decision: typeof decision.decision === 'string' ? decision.decision : undefined,
        reason: typeof decision.reason === 'string' ? decision.reason : undefined,
      },
      event.timestamp,
    );
  }
}

export function projectPipelineLifecycle(
  currentState: ExecutionState,
  event: RuntimeEvent,
  feature: string,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.PIPELINE_INITIALIZED: {
      const initial = mergeDeep(
        defaultExecutionState(feature),
        event.data.initialState ?? {},
      ) as ExecutionState;
      initial.updatedAt = event.timestamp || initial.updatedAt;
      if (!initial.createdAt) initial.createdAt = event.timestamp || '';
      if (!initial.feature) initial.feature = feature;
      return initial;
    }

    case EVENT_TYPES.PIPELINE_PAUSED: {
      currentState.status = PIPELINE_STATUS.PAUSED;
      currentState.pause = {
        paused: true,
        reason: typeof event.data.reason === 'string' ? event.data.reason : '',
        requestedBy: typeof event.data.requestedBy === 'string' ? event.data.requestedBy : 'user',
        pausedAt: event.timestamp,
      };
      return currentState;
    }

    case EVENT_TYPES.PIPELINE_RESUMED: {
      currentState.status = PIPELINE_STATUS.RUNNING;
      currentState.pause = null;
      applyPipelineResumedWorkflow(currentState, event);
      refreshWorkflowSchedule(currentState, event.timestamp);
      return currentState;
    }

    case EVENT_TYPES.PACK_APPLIED: {
      const eventData = isObject(event.data) ? event.data : {};
      const config = isObject(eventData.config) ? eventData.config : {};
      const parameters = isObject(eventData.parameters) ? eventData.parameters : {};
      const derived = {
        pipelinePack: eventData.pack ?? 'default',
        pipelinePackVersion: eventData.version ?? '',
        enabledGates: Array.isArray(config.gates) ? clone(config.gates) : [],
        activeAgents: Array.isArray(config.agents) ? clone(config.agents) : [],
        packConfig: clone(config),
      };
      currentState.parameters = mergeDeep(
        currentState.parameters ?? {},
        mergeDeep(derived, parameters),
      ) as Record<string, unknown>;
      return currentState;
    }

    default:
      return null;
  }
}
