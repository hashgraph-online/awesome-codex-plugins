/**
 * Wave lifecycle projector — handles wave verified events.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import { refreshWorkflowSchedule } from './helpers.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';

function upsertWorkflowWaveNode(state: ExecutionState, event: RuntimeEvent): void {
  if (!state.workflow) return;
  const waveId = typeof event.data.waveId === 'string' ? event.data.waveId : '';
  if (!waveId) return;
  const nodeId = `wave:${waveId}`;
  state.workflow.nodes[nodeId] = {
    id: nodeId,
    kind: 'wave',
    stage: 0,
    phase: 'wave-verification',
    inputs: [],
    optional: false,
    status: event.data.verified === true ? 'completed' : 'failed',
    reason: typeof event.data.phase === 'string' ? `wave-${event.data.phase}` : 'wave-verification',
    updatedAt: event.timestamp,
  };
}

export function projectWaveLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.WAVE_VERIFIED: {
      upsertWorkflowWaveNode(state, event);
      refreshWorkflowSchedule(state, event.timestamp);
      return state;
    }

    default:
      return null;
  }
}
