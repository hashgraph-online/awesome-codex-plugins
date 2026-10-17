/**
 * Conversation lifecycle projector — handles conversation opened, message appended,
 * resolved, and todo materialized events.
 */

import type {
  ConversationMessage,
  ConversationResolution,
  ConversationThread,
  DerivedTodo,
  ResolutionTodo,
} from '../domain/conversation-types.mts';
import { EVENT_TYPES } from '../domain/event-types.mts';
import { clone, closeThread, ensureConversationSections, upsertThread } from './helpers.mts';
import type { ExecutionState, RuntimeEvent } from './types.mts';

export function projectConversationLifecycle(
  state: ExecutionState,
  event: RuntimeEvent,
): ExecutionState | null {
  switch (event.type) {
    case EVENT_TYPES.CONVERSATION_OPENED: {
      ensureConversationSections(state);
      const thread = clone(event.data.thread as ConversationThread);
      state.conversations.threads = upsertThread(state.conversations.threads, thread);
      state.conversationMetrics.opened += 1;
      if (thread.kind === 'huddle') {
        state.conversationMetrics.huddles += 1;
      }
      return state;
    }

    case EVENT_TYPES.CONVERSATION_MESSAGE_APPENDED: {
      ensureConversationSections(state);
      const baseMessage = clone(
        event.data.message as Partial<ConversationMessage> & { id: string; threadId: string },
      );
      const message: ConversationMessage = {
        id: baseMessage.id,
        threadId: baseMessage.threadId,
        from: typeof baseMessage.from === 'string' ? baseMessage.from : '',
        to: Array.isArray(baseMessage.to)
          ? baseMessage.to.filter((value): value is string => typeof value === 'string')
          : [],
        intent: (baseMessage.intent as ConversationMessage['intent']) ?? 'question',
        content: typeof baseMessage.content === 'string' ? baseMessage.content : '',
        evidence: Array.isArray(baseMessage.evidence) ? clone(baseMessage.evidence) : undefined,
        createdAt:
          typeof baseMessage.createdAt === 'string' ? baseMessage.createdAt : event.timestamp,
      };
      state.conversations.messages = state.conversations.messages.concat(message);
      return state;
    }

    case EVENT_TYPES.CONVERSATION_RESOLVED: {
      ensureConversationSections(state);
      const baseResolution = clone(
        event.data.resolution as Partial<ConversationResolution> & { threadId: string },
      );
      const todos = Array.isArray(baseResolution.todos)
        ? baseResolution.todos.map((todo) => ({
            id: String(todo.id),
            owner: String(todo.owner),
            title: String(todo.title),
            status: (todo.status ?? 'pending') as ResolutionTodo['status'],
          }))
        : [];
      const resolution: ConversationResolution = {
        threadId: baseResolution.threadId,
        summary: typeof baseResolution.summary === 'string' ? baseResolution.summary : '',
        decision: typeof baseResolution.decision === 'string' ? baseResolution.decision : '',
        todos,
        createdAt:
          typeof baseResolution.createdAt === 'string' ? baseResolution.createdAt : event.timestamp,
      };
      state.conversations.resolutions = state.conversations.resolutions.concat(resolution);
      state.conversations.threads = closeThread(state.conversations.threads, resolution.threadId);
      state.conversationMetrics.resolved += 1;
      return state;
    }

    case EVENT_TYPES.TODO_MATERIALIZED: {
      ensureConversationSections(state);
      const baseTodo = clone(
        event.data.todo as Partial<DerivedTodo> & { id: string; owner: string; title: string },
      );
      const derivedTodo: DerivedTodo = {
        id: baseTodo.id,
        sourceThreadId: typeof baseTodo.sourceThreadId === 'string' ? baseTodo.sourceThreadId : '',
        title: baseTodo.title,
        owner: baseTodo.owner,
        type: (baseTodo.type as DerivedTodo['type']) ?? 'change',
        status: (baseTodo.status as DerivedTodo['status']) ?? 'pending',
        successCriteria: Array.isArray(baseTodo.successCriteria)
          ? baseTodo.successCriteria.filter((value): value is string => typeof value === 'string')
          : [],
        impact: {
          artifacts: Array.isArray(baseTodo.impact?.artifacts)
            ? baseTodo.impact.artifacts.filter(
                (value): value is string => typeof value === 'string',
              )
            : [],
          scope: Array.isArray(baseTodo.impact?.scope)
            ? baseTodo.impact.scope.filter((value): value is string => typeof value === 'string')
            : [],
        },
        dispatchHint: {
          stage:
            typeof baseTodo.dispatchHint?.stage === 'number' &&
            Number.isFinite(baseTodo.dispatchHint.stage)
              ? baseTodo.dispatchHint.stage
              : 0,
          agent:
            typeof baseTodo.dispatchHint?.agent === 'string' ? baseTodo.dispatchHint.agent : '',
        },
        createdAt: typeof baseTodo.createdAt === 'string' ? baseTodo.createdAt : event.timestamp,
      };
      state.derivedTodos = state.derivedTodos.concat(derivedTodo);
      state.conversationMetrics.todos += 1;
      return state;
    }

    default:
      return null;
  }
}
