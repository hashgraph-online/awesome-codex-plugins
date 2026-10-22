/**
 * Agent lifecycle projector — handles agent started, completed, failed, and retry scheduled events.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { AGENT_STATUS } from '../domain/state-constants.mts';
import {
  ensureAgent,
  ensureStage,
  refreshWorkflowSchedule,
  updateWorkflowAgentNodes,
} from './helpers.mts';
import type { AgentState, ExecutionState, RuntimeEvent } from './types.mts';

export function projectAgentLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.AGENT_STARTED: {
      const stage = ensureStage(state, event.data.stage);
      const agent = ensureAgent(stage, String(event.data.agent));
      agent.status = AGENT_STATUS.RUNNING;
      if (!agent.startTime) agent.startTime = event.timestamp;
      if (typeof event.data.promptFingerprint === 'string') {
        agent.promptFingerprint = event.data.promptFingerprint;
      }
      if (typeof event.data.inputDigest === 'string') {
        agent.inputDigest = event.data.inputDigest;
      }
      updateWorkflowAgentNodes(
        state,
        event.data.stage,
        String(event.data.agent),
        { status: 'running', reason: 'agent-started' },
        event.timestamp,
        typeof event.data.artifact === 'string' ? event.data.artifact : undefined,
      );
      return state;
    }

    case EVENT_TYPES.AGENT_COMPLETED: {
      const stage = ensureStage(state, event.data.stage);
      const agent = ensureAgent(stage, String(event.data.agent));
      agent.status = AGENT_STATUS.COMPLETED;
      agent.endTime = event.timestamp;
      if (typeof event.data.promptFingerprint === 'string') {
        agent.promptFingerprint = event.data.promptFingerprint;
      }
      if (typeof event.data.inputDigest === 'string') {
        agent.inputDigest = event.data.inputDigest;
      }
      updateWorkflowAgentNodes(
        state,
        event.data.stage,
        String(event.data.agent),
        { status: 'completed', reason: 'agent-completed' },
        event.timestamp,
        typeof event.data.artifact === 'string' ? event.data.artifact : undefined,
      );
      refreshWorkflowSchedule(state, event.timestamp);
      return state;
    }

    case EVENT_TYPES.AGENT_FAILED: {
      const stageId = event.data.stage;
      if (stageId != null) {
        const stage = ensureStage(state, stageId);
        const agent = ensureAgent(stage, String(event.data.agent));
        agent.status = AGENT_STATUS.FAILED;
        agent.endTime = event.timestamp;
        agent.failureReason = (event.data.reason as string | null | undefined) || null;
        updateWorkflowAgentNodes(
          state,
          event.data.stage,
          String(event.data.agent),
          { status: 'failed', reason: (event.data.reason as string | undefined) ?? 'agent-failed' },
          event.timestamp,
          typeof event.data.artifact === 'string' ? event.data.artifact : undefined,
        );
      }
      return state;
    }

    case EVENT_TYPES.AGENT_RETRY_SCHEDULED: {
      const stage = ensureStage(state, event.data.stage);
      const agent = ensureAgent(stage, String(event.data.agent));
      agent.retryCount += 1;
      agent.status = 'retrying' as AgentState['status'];
      agent.failureReason = (event.data.reason as string | null | undefined) || null;
      return state;
    }

    default:
      return null;
  }
}
