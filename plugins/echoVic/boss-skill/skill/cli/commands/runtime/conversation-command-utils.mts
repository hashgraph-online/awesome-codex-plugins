import {
  type CliContext,
  CliUserError,
  consumeCliContractOption,
  type JsonObject,
  outputList,
  readJsonInput,
} from '../../cli/contract.mts';
import {
  appendConversationMessage,
  listConversations,
  listTodos,
  openConversation,
  resolveConversation,
} from '../../runtime/application/conversations.mts';
import { appendRuntimeEvent } from '../../runtime/application/state.mts';
import type {
  ConversationAnchor,
  ConversationMessage,
  ConversationResolution,
  ConversationThread,
  DerivedTodo,
  ResolutionTodo,
} from '../../runtime/domain/conversation-types.mts';
import { EVENT_TYPES } from '../../runtime/domain/event-types.mts';
import {
  type ExecutionState,
  materializeState,
} from '../../runtime/projectors/materialize-state.mts';

type ConversationKind = ConversationThread['kind'];
type ConversationPriority = ConversationThread['priority'];
type ConversationIntent = ConversationMessage['intent'];
type TodoType = DerivedTodo['type'];
type TodoStatus = DerivedTodo['status'];

const CONVERSATION_KINDS = [
  'ask',
  'challenge',
  'propose',
  'request_change',
  'escalate',
  'huddle',
] as const;
const CONVERSATION_PRIORITIES = ['low', 'medium', 'high', 'critical'] as const;
const CONVERSATION_INTENTS = ['question', 'objection', 'proposal', 'evidence', 'decision'] as const;
const TODO_TYPES = ['change', 'clarify', 'verify', 'doc_update', 'followup'] as const;
const TODO_STATUSES = ['pending', 'queued', 'in_progress', 'done', 'blocked', 'cancelled'] as const;

export interface OpenConversationInput {
  feature: string;
  kind: ConversationKind;
  anchor: ConversationAnchor;
  initiator: string;
  participants: string[];
  priority: ConversationPriority;
}

export interface AppendConversationMessageInput {
  feature: string;
  threadId: string;
  from: string;
  to: string[];
  intent: ConversationIntent;
  content: string;
}

export interface MaterializeTodoInput {
  feature: string;
  threadId: string;
  title: string;
  owner: string;
  type: TodoType;
  successCriteria: string[];
  status?: TodoStatus;
  artifacts?: string[];
  scope?: string[];
  stage?: number;
  agent?: string;
}

export interface ResolveConversationInput {
  feature: string;
  threadId: string;
  summary: string;
  decision: string;
  todos: MaterializeTodoInput[];
  escalation?: {
    artifact: string;
    from: string;
    to: string;
    reason: string;
    priority?: string;
  };
}

function missingRequiredArgument(argument: string): CliUserError {
  return new CliUserError({
    code: 'missing_required_argument',
    message: `Missing ${argument} argument`,
    input: { argument },
    retryable: false,
    suggestion: 'Run this command with --describe to see required parameters',
  });
}

function requireInputString(value: unknown, argument: string): string {
  if (value === undefined || value === null || value === '') {
    throw missingRequiredArgument(argument);
  }
  return String(value);
}

function optionalInputString(value: unknown): string | undefined {
  return value === undefined || value === null || value === '' ? undefined : String(value);
}

function requireOptionValue(flag: string, value: string | undefined): string {
  if (!value || value.startsWith('-')) {
    throw new CliUserError({
      code: 'missing_option_value',
      message: `${flag} requires a value`,
      input: { option: flag },
      retryable: false,
      suggestion: `Pass a value after ${flag}`,
    });
  }
  return value;
}

export function toFeatureNotFoundError(err: unknown, feature: string): unknown {
  const message = err instanceof Error ? err.message : String(err);
  if (message.includes('未找到执行文件') || message.includes('未找到事件文件')) {
    return new CliUserError({
      code: 'feature_not_found',
      message,
      input: { feature },
      retryable: false,
      suggestion: 'Run boss runtime init-pipeline <feature> first',
    });
  }
  return err;
}

function parseStringList(raw: unknown): string[] {
  if (Array.isArray(raw)) {
    return raw.map((value) => String(value).trim()).filter(Boolean);
  }
  if (typeof raw !== 'string') {
    return [];
  }
  return raw
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean);
}

function ensureAnchor(anchor: ConversationAnchor): ConversationAnchor {
  if (!anchor.artifact && !anchor.task && !anchor.scope && !anchor.decision) {
    throw new CliUserError({
      code: 'missing_anchor',
      message: 'Conversation requires at least one anchor field',
      input: anchor as JsonObject,
      retryable: false,
      suggestion: 'Pass one of --artifact, --task, --scope, or --decision',
    });
  }
  return anchor;
}

function ensureEnum<T extends string>(value: string, allowed: readonly T[], argument: string): T {
  if ((allowed as readonly string[]).includes(value)) {
    return value as T;
  }
  throw new CliUserError({
    code: 'invalid_argument',
    message: `Invalid ${argument}: ${value}`,
    input: { [argument]: value },
    retryable: false,
    suggestion: `Allowed values: ${allowed.join(', ')}`,
  });
}

function parseStage(raw: string | undefined): number | undefined {
  if (!raw) return undefined;
  const stage = Number(raw);
  if (!Number.isInteger(stage) || stage < 0) {
    throw new CliUserError({
      code: 'invalid_stage',
      message: `Invalid stage value: ${raw}`,
      input: { stage: raw },
      retryable: false,
      suggestion: 'Use a non-negative integer stage number',
    });
  }
  return stage;
}

function parseBaseFeatureArg(argv: string[]): { feature: string; consumedIndex: number } {
  let feature = '';
  let consumedIndex = -1;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      continue;
    }
    feature = arg;
    consumedIndex = index;
    break;
  }

  return {
    feature: requireInputString(feature, 'feature'),
    consumedIndex,
  };
}

export function buildThreadId(feature: string): string {
  return `conv-${feature}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function buildTodoId(threadId: string): string {
  return `todo-${threadId}-${Math.random().toString(36).slice(2, 8)}`;
}

export function resolveOpenConversationInput(
  argv: string[],
  context: CliContext,
): OpenConversationInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      kind: ensureEnum(requireInputString(input.kind, 'kind'), CONVERSATION_KINDS, 'kind'),
      anchor: ensureAnchor({
        artifact: optionalInputString(input.artifact),
        task: optionalInputString(input.task),
        scope: optionalInputString(input.scope),
        decision: optionalInputString(input.decision),
      }),
      initiator: requireInputString(input.initiator, 'initiator'),
      participants: parseStringList(input.participants),
      priority: ensureEnum(
        optionalInputString(input.priority) || 'medium',
        CONVERSATION_PRIORITIES,
        'priority',
      ),
    };
  }

  const { feature, consumedIndex } = parseBaseFeatureArg(argv);
  let kind = 'ask';
  let artifact = '';
  let task = '';
  let scope = '';
  let decision = '';
  let initiator = '';
  let participants = '';
  let priority = 'medium';

  for (let index = 0; index < argv.length; index += 1) {
    if (index === consumedIndex) continue;
    const arg = argv[index]!;
    switch (arg) {
      case '--kind':
        kind = requireOptionValue('--kind', argv[index + 1]);
        index += 1;
        continue;
      case '--artifact':
        artifact = requireOptionValue('--artifact', argv[index + 1]);
        index += 1;
        continue;
      case '--task':
        task = requireOptionValue('--task', argv[index + 1]);
        index += 1;
        continue;
      case '--scope':
        scope = requireOptionValue('--scope', argv[index + 1]);
        index += 1;
        continue;
      case '--decision':
        decision = requireOptionValue('--decision', argv[index + 1]);
        index += 1;
        continue;
      case '--initiator':
        initiator = requireOptionValue('--initiator', argv[index + 1]);
        index += 1;
        continue;
      case '--participants':
        participants = requireOptionValue('--participants', argv[index + 1]);
        index += 1;
        continue;
      case '--priority':
        priority = requireOptionValue('--priority', argv[index + 1]);
        index += 1;
        continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (index !== consumedIndex) {
      throw new Error(`多余的参数: ${arg}`);
    }
  }

  return {
    feature,
    kind: ensureEnum(kind, CONVERSATION_KINDS, 'kind'),
    anchor: ensureAnchor({
      artifact: optionalInputString(artifact),
      task: optionalInputString(task),
      scope: optionalInputString(scope),
      decision: optionalInputString(decision),
    }),
    initiator: requireInputString(initiator, 'initiator'),
    participants: parseStringList(participants),
    priority: ensureEnum(priority, CONVERSATION_PRIORITIES, 'priority'),
  };
}

export function resolveAppendConversationMessageInput(
  argv: string[],
  context: CliContext,
): AppendConversationMessageInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      threadId: requireInputString(input.threadId, 'threadId'),
      from: requireInputString(input.from, 'from'),
      to: parseStringList(input.to),
      intent: ensureEnum(
        optionalInputString(input.intent) || 'question',
        CONVERSATION_INTENTS,
        'intent',
      ),
      content: requireInputString(input.content, 'content'),
    };
  }

  const { feature, consumedIndex } = parseBaseFeatureArg(argv);
  let threadId = '';
  let from = '';
  let to = '';
  let intent = 'question';
  let content = '';

  for (let index = 0; index < argv.length; index += 1) {
    if (index === consumedIndex) continue;
    const arg = argv[index]!;
    switch (arg) {
      case '--thread-id':
        threadId = requireOptionValue('--thread-id', argv[index + 1]);
        index += 1;
        continue;
      case '--from':
        from = requireOptionValue('--from', argv[index + 1]);
        index += 1;
        continue;
      case '--to':
        to = requireOptionValue('--to', argv[index + 1]);
        index += 1;
        continue;
      case '--intent':
        intent = requireOptionValue('--intent', argv[index + 1]);
        index += 1;
        continue;
      case '--content':
        content = requireOptionValue('--content', argv[index + 1]);
        index += 1;
        continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (index !== consumedIndex) {
      throw new Error(`多余的参数: ${arg}`);
    }
  }

  return {
    feature,
    threadId: requireInputString(threadId, 'threadId'),
    from: requireInputString(from, 'from'),
    to: parseStringList(to),
    intent: ensureEnum(intent, CONVERSATION_INTENTS, 'intent'),
    content: requireInputString(content, 'content'),
  };
}

export function resolveMaterializeTodoInput(
  argv: string[],
  context: CliContext,
): MaterializeTodoInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    return {
      feature: requireInputString(input.feature, 'feature'),
      threadId: requireInputString(input.threadId, 'threadId'),
      title: requireInputString(input.title, 'title'),
      owner: requireInputString(input.owner, 'owner'),
      type: ensureEnum(optionalInputString(input.type) || 'change', TODO_TYPES, 'type'),
      successCriteria: parseStringList(input.successCriteria),
      status: ensureEnum(optionalInputString(input.status) || 'pending', TODO_STATUSES, 'status'),
      artifacts: parseStringList(input.artifacts),
      scope: parseStringList(input.scope),
      stage: parseStage(optionalInputString(input.stage)),
      agent: optionalInputString(input.agent),
    };
  }

  const { feature, consumedIndex } = parseBaseFeatureArg(argv);
  let threadId = '';
  let title = '';
  let owner = '';
  let type = 'change';
  let successCriteria = '';
  let status = 'pending';
  let artifacts = '';
  let scope = '';
  let stage = '';
  let agent = '';

  for (let index = 0; index < argv.length; index += 1) {
    if (index === consumedIndex) continue;
    const arg = argv[index]!;
    switch (arg) {
      case '--thread-id':
        threadId = requireOptionValue('--thread-id', argv[index + 1]);
        index += 1;
        continue;
      case '--title':
        title = requireOptionValue('--title', argv[index + 1]);
        index += 1;
        continue;
      case '--owner':
        owner = requireOptionValue('--owner', argv[index + 1]);
        index += 1;
        continue;
      case '--type':
        type = requireOptionValue('--type', argv[index + 1]);
        index += 1;
        continue;
      case '--success-criteria':
        successCriteria = requireOptionValue('--success-criteria', argv[index + 1]);
        index += 1;
        continue;
      case '--status':
        status = requireOptionValue('--status', argv[index + 1]);
        index += 1;
        continue;
      case '--artifacts':
        artifacts = requireOptionValue('--artifacts', argv[index + 1]);
        index += 1;
        continue;
      case '--scope':
        scope = requireOptionValue('--scope', argv[index + 1]);
        index += 1;
        continue;
      case '--stage':
        stage = requireOptionValue('--stage', argv[index + 1]);
        index += 1;
        continue;
      case '--agent':
        agent = requireOptionValue('--agent', argv[index + 1]);
        index += 1;
        continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (index !== consumedIndex) {
      throw new Error(`多余的参数: ${arg}`);
    }
  }

  return {
    feature,
    threadId: requireInputString(threadId, 'threadId'),
    title: requireInputString(title, 'title'),
    owner: requireInputString(owner, 'owner'),
    type: ensureEnum(type, TODO_TYPES, 'type'),
    successCriteria: parseStringList(successCriteria),
    status: ensureEnum(status, TODO_STATUSES, 'status'),
    artifacts: parseStringList(artifacts),
    scope: parseStringList(scope),
    stage: parseStage(stage),
    agent: optionalInputString(agent),
  };
}

export function resolveResolveConversationInput(
  argv: string[],
  context: CliContext,
): ResolveConversationInput {
  const jsonInput = readJsonInput(context.values.jsonInput);
  if (jsonInput) {
    const input = jsonInput as Record<string, unknown>;
    const todos = Array.isArray(input.todos)
      ? input.todos.map((todo) => {
          const record = todo as Record<string, unknown>;
          return {
            feature: requireInputString(input.feature, 'feature'),
            threadId: requireInputString(input.threadId, 'threadId'),
            title: requireInputString(record.title, 'title'),
            owner: requireInputString(record.owner, 'owner'),
            type: ensureEnum(optionalInputString(record.type) || 'change', TODO_TYPES, 'type'),
            successCriteria: parseStringList(record.successCriteria),
            status: ensureEnum(
              optionalInputString(record.status) || 'pending',
              TODO_STATUSES,
              'status',
            ),
            artifacts: parseStringList(record.artifacts),
            scope: parseStringList(record.scope),
            stage: parseStage(optionalInputString(record.stage)),
            agent: optionalInputString(record.agent),
          };
        })
      : [];

    return {
      feature: requireInputString(input.feature, 'feature'),
      threadId: requireInputString(input.threadId, 'threadId'),
      summary: requireInputString(input.summary, 'summary'),
      decision: requireInputString(input.decision, 'decision'),
      todos,
    };
  }

  const { feature, consumedIndex } = parseBaseFeatureArg(argv);
  let threadId = '';
  let summary = '';
  let decision = '';
  let todoTitle = '';
  let todoOwner = '';
  let todoType = 'change';
  let successCriteria = '';
  let escalateArtifact = '';
  let escalateFrom = '';
  let escalateTo = '';
  let escalateReason = '';
  let escalatePriority = '';

  for (let index = 0; index < argv.length; index += 1) {
    if (index === consumedIndex) continue;
    const arg = argv[index]!;
    switch (arg) {
      case '--thread-id':
        threadId = requireOptionValue('--thread-id', argv[index + 1]);
        index += 1;
        continue;
      case '--summary':
        summary = requireOptionValue('--summary', argv[index + 1]);
        index += 1;
        continue;
      case '--decision':
        decision = requireOptionValue('--decision', argv[index + 1]);
        index += 1;
        continue;
      case '--todo-title':
        todoTitle = requireOptionValue('--todo-title', argv[index + 1]);
        index += 1;
        continue;
      case '--todo-owner':
        todoOwner = requireOptionValue('--todo-owner', argv[index + 1]);
        index += 1;
        continue;
      case '--todo-type':
        todoType = requireOptionValue('--todo-type', argv[index + 1]);
        index += 1;
        continue;
      case '--success-criteria':
        successCriteria = requireOptionValue('--success-criteria', argv[index + 1]);
        index += 1;
        continue;
      case '--escalate-artifact':
        escalateArtifact = requireOptionValue('--escalate-artifact', argv[index + 1]);
        index += 1;
        continue;
      case '--escalate-from':
        escalateFrom = requireOptionValue('--escalate-from', argv[index + 1]);
        index += 1;
        continue;
      case '--escalate-to':
        escalateTo = requireOptionValue('--escalate-to', argv[index + 1]);
        index += 1;
        continue;
      case '--escalate-reason':
        escalateReason = requireOptionValue('--escalate-reason', argv[index + 1]);
        index += 1;
        continue;
      case '--escalate-priority':
        escalatePriority = requireOptionValue('--escalate-priority', argv[index + 1]);
        index += 1;
        continue;
    }
    const contractOptionEnd = consumeCliContractOption(argv, index);
    if (contractOptionEnd !== null) {
      index = contractOptionEnd;
      continue;
    }
    if (arg.startsWith('-')) {
      throw new Error(`未知选项: ${arg}`);
    }
    if (index !== consumedIndex) {
      throw new Error(`多余的参数: ${arg}`);
    }
  }

  const todos: MaterializeTodoInput[] = [];
  if (todoTitle || todoOwner || successCriteria) {
    todos.push({
      feature,
      threadId: requireInputString(threadId, 'threadId'),
      title: requireInputString(todoTitle, 'todoTitle'),
      owner: requireInputString(todoOwner, 'todoOwner'),
      type: ensureEnum(todoType, TODO_TYPES, 'todoType'),
      successCriteria: parseStringList(successCriteria),
      status: 'pending',
    });
  }

  const escalation =
    escalateArtifact || escalateFrom || escalateTo || escalateReason || escalatePriority
      ? {
          artifact: requireInputString(escalateArtifact, 'escalateArtifact'),
          from: requireInputString(escalateFrom, 'escalateFrom'),
          to: requireInputString(escalateTo, 'escalateTo'),
          reason: requireInputString(escalateReason, 'escalateReason'),
          priority: optionalInputString(escalatePriority),
        }
      : undefined;

  return {
    feature,
    threadId: requireInputString(threadId, 'threadId'),
    summary: requireInputString(summary, 'summary'),
    decision: requireInputString(decision, 'decision'),
    todos,
    escalation,
  };
}

export function buildThread(input: OpenConversationInput): ConversationThread {
  const createdAt = new Date().toISOString();
  return {
    id: buildThreadId(input.feature),
    kind: input.kind,
    anchor: input.anchor,
    initiator: input.initiator,
    participants: input.participants,
    status: 'open',
    priority: input.priority,
    createdAt,
    updatedAt: createdAt,
  };
}

export function buildMessage(input: AppendConversationMessageInput): ConversationMessage {
  return {
    id: `msg-${input.threadId}-${Math.random().toString(36).slice(2, 8)}`,
    threadId: input.threadId,
    from: input.from,
    to: input.to,
    intent: input.intent,
    content: input.content,
    createdAt: new Date().toISOString(),
  };
}

export function buildResolution(input: ResolveConversationInput): ConversationResolution {
  const todos: ResolutionTodo[] = input.todos.map((todo) => ({
    id: buildTodoId(input.threadId),
    owner: todo.owner,
    title: todo.title,
    status: 'pending',
  }));

  return {
    threadId: input.threadId,
    summary: input.summary,
    decision: input.decision,
    todos,
    createdAt: new Date().toISOString(),
  };
}

export function buildDerivedTodo(input: MaterializeTodoInput, todoId?: string): DerivedTodo {
  return {
    id: todoId || buildTodoId(input.threadId),
    sourceThreadId: input.threadId,
    title: input.title,
    owner: input.owner,
    type: input.type,
    status: input.status || 'pending',
    successCriteria: input.successCriteria,
    impact: {
      artifacts: input.artifacts || [],
      scope: input.scope || [],
    },
    dispatchHint: {
      stage: input.stage ?? 0,
      agent: input.agent || input.owner,
    },
    createdAt: new Date().toISOString(),
  };
}

function rematerialize(feature: string, cwd: string): ExecutionState {
  return materializeState(feature, cwd).state;
}

export function openConversationRuntime(
  input: OpenConversationInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const { feature, ...serviceInput } = input;
  return openConversation(feature, serviceInput, { cwd });
}

export function appendConversationMessageRuntime(
  input: AppendConversationMessageInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const { feature, ...serviceInput } = input;
  return appendConversationMessage(feature, serviceInput, { cwd });
}

export function materializeTodoRuntime(
  input: MaterializeTodoInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const todo = buildDerivedTodo(input);
  appendRuntimeEvent(cwd, input.feature, EVENT_TYPES.TODO_MATERIALIZED, { todo });
  rematerialize(input.feature, cwd);
  return {
    feature: input.feature,
    threadId: input.threadId,
    todo,
  };
}

export function resolveConversationRuntime(
  input: ResolveConversationInput,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const { feature, todos, ...serviceInput } = input;
  return resolveConversation(
    feature,
    {
      ...serviceInput,
      todos: todos.map((todo) => ({
        title: todo.title,
        owner: todo.owner,
        type: todo.type,
        successCriteria: todo.successCriteria,
        impact: {
          artifacts: todo.artifacts,
          scope: todo.scope,
        },
      })),
    },
    { cwd },
  );
}

export function listConversationsRuntime(
  feature: string,
  context: CliContext,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  const threads = listConversations(feature, { cwd });
  const state = rematerialize(feature, cwd);
  const items = threads.map((thread) => ({
    id: thread.id,
    kind: thread.kind,
    status: thread.status,
    priority: thread.priority,
    initiator: thread.initiator,
    participants: thread.participants,
    anchor: thread.anchor,
    createdAt: thread.createdAt,
    updatedAt: thread.updatedAt,
    messageCount: state.conversations.messages.filter((message) => message.threadId === thread.id)
      .length,
    todoCount: state.derivedTodos.filter((todo) => todo.sourceThreadId === thread.id).length,
  }));
  return outputList(items as JsonObject[], context);
}

export function listTodosRuntime(
  feature: string,
  context: CliContext,
  { cwd = process.cwd() }: { cwd?: string } = {},
) {
  return outputList(listTodos(feature, { cwd }) as unknown as JsonObject[], context);
}

export function renderConversationListText(items: Array<Record<string, unknown>>): string {
  if (items.length === 0) return 'No conversations\n';
  return `${items
    .map(
      (item) =>
        `${String(item.id)} ${String(item.kind)} ${String(item.status)} messages=${String(item.messageCount ?? 0)} todos=${String(item.todoCount ?? 0)}`,
    )
    .join('\n')}\n`;
}

export function renderTodoListText(items: Array<Record<string, unknown>>): string {
  if (items.length === 0) return 'No todos\n';
  return `${items
    .map(
      (item) =>
        `${String(item.id)} ${String(item.owner)} ${String(item.status)} ${String(item.title)}`,
    )
    .join('\n')}\n`;
}

export function renderMutationText(payload: Record<string, unknown>): string {
  return `${JSON.stringify(payload, null, 2)}\n`;
}
