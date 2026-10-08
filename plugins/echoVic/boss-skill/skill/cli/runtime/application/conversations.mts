import { randomUUID } from 'node:crypto';
import type {
  ConversationAnchor,
  ConversationEvidence,
  ConversationMessage,
  ConversationResolution,
  ConversationThread,
  DerivedTodo,
  ResolutionTodo,
} from '../domain/conversation-types.mts';
import { EVENT_TYPES } from '../domain/event-types.mts';
import { type ExecutionState, materializeState } from '../projectors/materialize-state.mts';
import { isFormalSourceOfTruthArtifact, recordFeedback } from './pipeline.mts';
import { appendRuntimeEvent, ensureFeatureName, refreshMemory } from './state.mts';

type ConversationKind = ConversationThread['kind'];
type ConversationPriority = ConversationThread['priority'];
type ConversationStatus = ConversationThread['status'];
type MessageIntent = ConversationMessage['intent'];
type TodoType = DerivedTodo['type'];

const THREAD_KINDS: ConversationKind[] = [
  'ask',
  'challenge',
  'propose',
  'request_change',
  'escalate',
  'huddle',
];
const THREAD_PRIORITIES: ConversationPriority[] = ['low', 'medium', 'high', 'critical'];
const MESSAGE_INTENTS: MessageIntent[] = [
  'question',
  'objection',
  'proposal',
  'evidence',
  'decision',
];
const TODO_TYPES: TodoType[] = ['change', 'clarify', 'verify', 'doc_update', 'followup'];

const HINT_STAGES: Record<TodoType, number> = {
  change: 3,
  clarify: 2,
  verify: 3,
  doc_update: 2,
  followup: 3,
};

export interface OpenConversationInput {
  kind: ConversationKind;
  anchor: ConversationAnchor;
  initiator: string;
  participants: string[];
  priority?: ConversationPriority;
}

export interface AppendConversationMessageInput {
  threadId: string;
  from: string;
  to: string[];
  intent: MessageIntent;
  content: string;
  evidence?: ConversationEvidence[];
}

export interface ResolveConversationTodoInput {
  title: string;
  owner: string;
  type: TodoType;
  successCriteria?: string[];
  impact?: {
    artifacts?: string[];
    scope?: string[];
  };
}

export interface ResolveConversationEscalationInput {
  artifact: string;
  from: string;
  to: string;
  reason: string;
  priority?: string;
}

export interface ResolveConversationInput {
  threadId: string;
  summary: string;
  decision: string;
  todos?: ResolveConversationTodoInput[];
  escalation?: ResolveConversationEscalationInput;
}

export interface MaterializeConversationTodoInput {
  threadId: string;
  title: string;
  owner: string;
  type: TodoType;
  successCriteria?: string[];
  status?: DerivedTodo['status'];
  artifacts?: string[];
  scope?: string[];
  stage?: number;
  agent?: string;
}

export interface OpenConversationResult {
  feature: string;
  threadId: string;
  status: ConversationStatus;
}

export interface AppendConversationMessageResult {
  feature: string;
  threadId: string;
  messageId: string;
  messageCount: number;
}

export interface ResolveConversationResult {
  feature: string;
  threadId: string;
  policy: 'direct_todo' | 'huddle_recommended' | 'revision_escalated';
  resolution: ConversationResolution;
  todos: DerivedTodo[];
  escalation?: ResolveConversationEscalationInput;
}

export interface MaterializeConversationTodoResult {
  feature: string;
  threadId: string;
  todo: DerivedTodo;
}

export interface ConversationListItem extends ConversationThread {
  latestResolution?: ConversationResolution;
}

function ensureNonEmptyString(value: string, fieldName: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error(`${fieldName} 必须是非空字符串`);
  }
  return trimmed;
}

function ensureStringArray(values: string[], fieldName: string): string[] {
  if (!Array.isArray(values) || values.length === 0) {
    throw new Error(`${fieldName} 必须是非空数组`);
  }
  const normalized = values
    .map((value) => ensureNonEmptyString(String(value), fieldName))
    .filter((value, index, items) => items.indexOf(value) === index);
  if (normalized.length === 0) {
    throw new Error(`${fieldName} 必须包含至少一个非空字符串`);
  }
  return normalized;
}

function normalizeKind(kind: string): ConversationKind {
  if (!THREAD_KINDS.includes(kind as ConversationKind)) {
    throw new Error(`无效 conversation kind: ${kind}`);
  }
  return kind as ConversationKind;
}

function normalizePriority(priority: string | undefined): ConversationPriority {
  if (priority == null) return 'medium';
  if (!THREAD_PRIORITIES.includes(priority as ConversationPriority)) {
    throw new Error(`无效 conversation priority: ${priority}`);
  }
  return priority as ConversationPriority;
}

function normalizeIntent(intent: string): MessageIntent {
  if (!MESSAGE_INTENTS.includes(intent as MessageIntent)) {
    throw new Error(`无效 message intent: ${intent}`);
  }
  return intent as MessageIntent;
}

function normalizeTodoType(type: string): TodoType {
  if (!TODO_TYPES.includes(type as TodoType)) {
    throw new Error(`无效 todo type: ${type}`);
  }
  return type as TodoType;
}

function normalizeAnchor(anchor: ConversationAnchor): ConversationAnchor {
  const normalized: ConversationAnchor = {};
  if (anchor.artifact)
    normalized.artifact = ensureNonEmptyString(anchor.artifact, 'anchor.artifact');
  if (anchor.task) normalized.task = ensureNonEmptyString(anchor.task, 'anchor.task');
  if (anchor.scope) normalized.scope = ensureNonEmptyString(anchor.scope, 'anchor.scope');
  if (anchor.decision)
    normalized.decision = ensureNonEmptyString(anchor.decision, 'anchor.decision');
  if (Object.keys(normalized).length === 0) {
    throw new Error('conversation anchor 必须至少包含 artifact、task、scope、decision 之一');
  }
  return normalized;
}

function buildThread(input: OpenConversationInput, now: string): ConversationThread {
  return {
    id: `conv-${randomUUID()}`,
    kind: normalizeKind(input.kind),
    anchor: normalizeAnchor(input.anchor),
    initiator: ensureNonEmptyString(input.initiator, 'initiator'),
    participants: ensureStringArray(input.participants, 'participants'),
    status: 'open',
    priority: normalizePriority(input.priority),
    createdAt: now,
    updatedAt: now,
  };
}

function buildMessage(input: AppendConversationMessageInput, now: string): ConversationMessage {
  return {
    id: `msg-${randomUUID()}`,
    threadId: ensureNonEmptyString(input.threadId, 'threadId'),
    from: ensureNonEmptyString(input.from, 'from'),
    to: ensureStringArray(input.to, 'to'),
    intent: normalizeIntent(input.intent),
    content: ensureNonEmptyString(input.content, 'content'),
    evidence:
      Array.isArray(input.evidence) && input.evidence.length > 0
        ? input.evidence.map((item) => ({
            type: item.type,
            ref: ensureNonEmptyString(item.ref, 'evidence.ref'),
          }))
        : undefined,
    createdAt: now,
  };
}

function findThread(state: ExecutionState, threadId: string): ConversationThread {
  const thread = state.conversations.threads.find((candidate) => candidate.id === threadId);
  if (!thread) {
    throw new Error(`未找到 conversation thread: ${threadId}`);
  }
  return thread;
}

function normalizeResolutionTodos(
  input: ResolveConversationInput,
  thread: ConversationThread,
): ResolveConversationTodoInput[] {
  const todos = Array.isArray(input.todos) ? input.todos : [];
  if (todos.length === 0) return [];
  return todos.map((todo) => ({
    title: ensureNonEmptyString(todo.title, 'todo.title'),
    owner: ensureNonEmptyString(todo.owner, 'todo.owner'),
    type: normalizeTodoType(todo.type),
    successCriteria: Array.isArray(todo.successCriteria)
      ? todo.successCriteria.map((item) => ensureNonEmptyString(item, 'todo.successCriteria'))
      : [],
    impact: {
      artifacts: [
        ...(thread.anchor.artifact ? [thread.anchor.artifact] : []),
        ...(todo.impact?.artifacts ?? []).map((item) =>
          ensureNonEmptyString(item, 'todo.impact.artifacts'),
        ),
      ].filter((item, index, items) => items.indexOf(item) === index),
      scope: [
        ...(thread.anchor.scope ? [thread.anchor.scope] : []),
        ...(todo.impact?.scope ?? []).map((item) =>
          ensureNonEmptyString(item, 'todo.impact.scope'),
        ),
      ].filter((item, index, items) => items.indexOf(item) === index),
    },
  }));
}

function buildResolutionTodo(todo: ResolveConversationTodoInput): ResolutionTodo {
  return {
    id: `todo-${randomUUID()}`,
    owner: todo.owner,
    title: todo.title,
    status: 'pending',
  };
}

function buildResolution(
  input: ResolveConversationInput,
  thread: ConversationThread,
  now: string,
): ConversationResolution {
  const todos = normalizeResolutionTodos(input, thread).map(buildResolutionTodo);
  return {
    threadId: ensureNonEmptyString(input.threadId, 'threadId'),
    summary: ensureNonEmptyString(input.summary, 'summary'),
    decision: ensureNonEmptyString(input.decision, 'decision'),
    todos,
    createdAt: now,
  };
}

function buildDerivedTodo(
  thread: ConversationThread,
  resolutionTodo: ResolutionTodo,
  todoInput: ResolveConversationTodoInput,
  createdAt: string,
): DerivedTodo {
  const type = normalizeTodoType(todoInput.type);
  return {
    id: resolutionTodo.id,
    sourceThreadId: thread.id,
    title: resolutionTodo.title,
    owner: resolutionTodo.owner,
    type,
    status: resolutionTodo.status,
    successCriteria: todoInput.successCriteria ?? [],
    impact: {
      artifacts: todoInput.impact?.artifacts ?? [],
      scope: todoInput.impact?.scope ?? [],
    },
    dispatchHint: {
      stage: HINT_STAGES[type],
      agent: resolutionTodo.owner,
    },
    createdAt,
  };
}

function buildStandaloneTodo(
  input: MaterializeConversationTodoInput,
  thread: ConversationThread,
  now: string,
): DerivedTodo {
  const type = normalizeTodoType(input.type);
  const title = ensureNonEmptyString(input.title, 'title');
  const owner = ensureNonEmptyString(input.owner, 'owner');
  return {
    id: `todo-${randomUUID()}`,
    sourceThreadId: thread.id,
    title,
    owner,
    type,
    status: input.status ?? 'pending',
    successCriteria: Array.isArray(input.successCriteria)
      ? input.successCriteria.map((item) => ensureNonEmptyString(item, 'successCriteria'))
      : [],
    impact: {
      artifacts: Array.isArray(input.artifacts)
        ? input.artifacts.map((item) => ensureNonEmptyString(item, 'artifacts'))
        : [],
      scope: Array.isArray(input.scope)
        ? input.scope.map((item) => ensureNonEmptyString(item, 'scope'))
        : [],
    },
    dispatchHint: {
      stage:
        typeof input.stage === 'number' && Number.isFinite(input.stage)
          ? input.stage
          : HINT_STAGES[type],
      agent: ensureNonEmptyString(input.agent ?? owner, 'agent'),
    },
    createdAt: now,
  };
}

function resolvePolicy(
  thread: ConversationThread,
  input: ResolveConversationInput,
  todos: ResolveConversationTodoInput[],
): 'direct_todo' | 'huddle_recommended' | 'revision_escalated' {
  if (input.escalation) {
    return 'revision_escalated';
  }
  if (thread.kind !== 'huddle' && new Set(todos.map((todo) => todo.owner)).size > 1) {
    return 'huddle_recommended';
  }
  return 'direct_todo';
}

function normalizeEscalation(
  escalation: ResolveConversationEscalationInput | undefined,
  thread: ConversationThread,
): ResolveConversationEscalationInput | undefined {
  if (!escalation) return undefined;
  const artifact = ensureNonEmptyString(escalation.artifact, 'escalation.artifact');
  if (!isFormalSourceOfTruthArtifact(artifact)) {
    throw new Error(`会话升级只能针对正式 source-of-truth artifact: ${artifact}`);
  }
  if (thread.anchor.artifact && thread.anchor.artifact !== artifact) {
    throw new Error(`升级 artifact ${artifact} 与线程锚点 ${thread.anchor.artifact} 不一致`);
  }
  return {
    artifact,
    from: ensureNonEmptyString(escalation.from, 'escalation.from'),
    to: ensureNonEmptyString(escalation.to, 'escalation.to'),
    reason: ensureNonEmptyString(escalation.reason, 'escalation.reason'),
    priority: escalation.priority?.trim() || 'recommended',
  };
}

function listResolutionMap(state: ExecutionState): Map<string, ConversationResolution> {
  return new Map(
    state.conversations.resolutions.map((resolution) => [resolution.threadId, resolution]),
  );
}

export function openConversation(
  feature: string,
  input: OpenConversationInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
): OpenConversationResult {
  ensureFeatureName(feature);
  const now = new Date().toISOString();
  const thread = buildThread(input, now);
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.CONVERSATION_OPENED, { thread });
  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  const persisted = findThread(state, thread.id);
  return {
    feature,
    threadId: persisted.id,
    status: persisted.status,
  };
}

export function appendConversationMessage(
  feature: string,
  input: AppendConversationMessageInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
): AppendConversationMessageResult {
  ensureFeatureName(feature);
  const currentState = materializeState(feature, cwd).state;
  findThread(currentState, ensureNonEmptyString(input.threadId, 'threadId'));
  const now = new Date().toISOString();
  const message = buildMessage(input, now);
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.CONVERSATION_MESSAGE_APPENDED, { message });
  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return {
    feature,
    threadId: message.threadId,
    messageId: message.id,
    messageCount: state.conversations.messages.filter((item) => item.threadId === message.threadId)
      .length,
  };
}

export function resolveConversation(
  feature: string,
  input: ResolveConversationInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
): ResolveConversationResult {
  ensureFeatureName(feature);
  const currentState = materializeState(feature, cwd).state;
  const thread = findThread(currentState, ensureNonEmptyString(input.threadId, 'threadId'));
  const now = new Date().toISOString();
  const escalation = normalizeEscalation(input.escalation, thread);
  const normalizedTodos = normalizeResolutionTodos(input, thread);
  if (!escalation && normalizedTodos.length === 0) {
    throw new Error('resolveConversation 必须生成至少一个 todo，或升级到 formal revision loop');
  }

  const resolution = buildResolution(input, thread, now);
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.CONVERSATION_RESOLVED, { resolution });

  if (escalation) {
    recordFeedback(feature, {
      ...escalation,
      cwd,
    });
  } else {
    resolution.todos.forEach((resolutionTodo, index) => {
      const todo = buildDerivedTodo(thread, resolutionTodo, normalizedTodos[index]!, now);
      appendRuntimeEvent(cwd, feature, EVENT_TYPES.TODO_MATERIALIZED, { todo });
    });
  }

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);

  return {
    feature,
    threadId: thread.id,
    policy: resolvePolicy(thread, input, normalizedTodos),
    resolution:
      state.conversations.resolutions.find((item) => item.threadId === thread.id) ?? resolution,
    todos: state.derivedTodos.filter((todo) => todo.sourceThreadId === thread.id),
    escalation,
  };
}

export function materializeTodo(
  feature: string,
  input: MaterializeConversationTodoInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
): MaterializeConversationTodoResult {
  ensureFeatureName(feature);
  const currentState = materializeState(feature, cwd).state;
  const thread = findThread(currentState, ensureNonEmptyString(input.threadId, 'threadId'));
  const now = new Date().toISOString();
  const todo = buildStandaloneTodo(input, thread, now);
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.TODO_MATERIALIZED, { todo });
  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return {
    feature,
    threadId: thread.id,
    todo: state.derivedTodos.find((item) => item.id === todo.id) ?? todo,
  };
}

export function listConversations(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): ConversationListItem[] {
  ensureFeatureName(feature);
  const { state } = materializeState(feature, cwd);
  const resolutionMap = listResolutionMap(state);
  return state.conversations.threads.map((thread) => ({
    ...thread,
    latestResolution: resolutionMap.get(thread.id),
  }));
}

export function listTodos(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): DerivedTodo[] {
  ensureFeatureName(feature);
  const { state } = materializeState(feature, cwd);
  return state.derivedTodos;
}
