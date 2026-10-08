/**
 * Revision lifecycle projector — handles revision requested and user choice recorded events.
 */
import { EVENT_TYPES } from '../domain/event-types.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';

export function projectRevisionLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.REVISION_REQUESTED: {
      state.revisionRequests = (state.revisionRequests ?? []).concat({
        from: String(event.data.from),
        to: String(event.data.to),
        artifact: String(event.data.artifact),
        reason: String(event.data.reason),
        priority: typeof event.data.priority === 'string' ? event.data.priority : 'recommended',
        timestamp: event.timestamp,
        resolved: false,
      });
      state.feedbackLoops.currentRound = (state.feedbackLoops.currentRound || 0) + 1;
      // 上限限制的是同一产物的返工轮次；按产物分别计数，不同产物互不影响
      const artifact = String(event.data.artifact);
      if (!state.feedbackLoops.rounds) state.feedbackLoops.rounds = {};
      const rounds = state.feedbackLoops.rounds;
      rounds[artifact] = (rounds[artifact] ?? 0) + 1;
      return state;
    }

    case EVENT_TYPES.USER_CHOICE_RECORDED: {
      state.humanInterventions = (state.humanInterventions ?? []).concat({
        choiceType: String(event.data.choiceType),
        selected: String(event.data.selected),
        timestamp: event.timestamp,
        agent: typeof event.data.agent === 'string' ? event.data.agent : undefined,
        stage: event.data.stage != null ? Number(event.data.stage) : undefined,
      });
      return state;
    }

    default:
      return null;
  }
}
