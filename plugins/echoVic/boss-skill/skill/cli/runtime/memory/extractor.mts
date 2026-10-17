import type { PersistedMemoryRecord } from './store.mts';

export interface MemoryExtractionInput {
  feature: string;
  events?: Array<{
    id: number;
    type: string;
    timestamp: string;
    data?: Record<string, any>;
  }>;
  execution?: {
    parameters?: Record<string, any>;
    stages?: Record<string, any>;
  };
  now: string;
}

type PersistedMemoryRecordSeed = Omit<PersistedMemoryRecord, 'influence' | 'tags'> & {
  tags?: string[];
};

function buildRecord(base: PersistedMemoryRecordSeed): PersistedMemoryRecord {
  return {
    influence: 'preference',
    tags: [],
    ...base,
  };
}

export function extractFeatureMemories({
  feature,
  events = [],
  execution = {},
  now,
}: MemoryExtractionInput): PersistedMemoryRecord[] {
  const records: PersistedMemoryRecord[] = [];

  for (const event of events) {
    if (event.type === 'GateEvaluated' && event.data && event.data.passed === false) {
      records.push(
        buildRecord({
          id: `gate-${event.id}`,
          scope: 'feature',
          kind: 'execution',
          category: 'gate_failure_pattern',
          feature,
          stage: event.data.stage as number,
          agent: null,
          summary: `Gate ${event.data.gate} failed in stage ${event.data.stage}`,
          source: { type: 'events', window: 'latest' },
          evidence: [{ type: 'event', ref: String(event.id) }],
          tags: [String(event.data.gate)],
          confidence: 0.8,
          createdAt: event.timestamp,
          lastSeenAt: event.timestamp,
          expiresAt: null,
          decayScore: 10,
        }),
      );
    }

    if (event.type === 'AgentFailed' && event.data) {
      records.push(
        buildRecord({
          id: `agent-${event.id}`,
          scope: 'feature',
          kind: 'execution',
          category: 'agent_failure_pattern',
          feature,
          stage: event.data.stage as number,
          agent: String(event.data.agent),
          summary: `${event.data.agent} failed in stage ${event.data.stage}`,
          source: { type: 'events', window: 'latest' },
          evidence: [{ type: 'event', ref: String(event.id) }],
          tags: [String(event.data.agent)],
          confidence: 0.8,
          createdAt: event.timestamp,
          lastSeenAt: event.timestamp,
          expiresAt: null,
          decayScore: 9,
        }),
      );
    }

    if (event.type === 'StageCompleted' && event.data) {
      const stages = execution.stages ?? {};
      const parameters = execution.parameters ?? {};
      const stage = stages[String(event.data.stage)] ?? {};
      if ((stage.retryCount ?? 0) === 0) {
        const roles = parameters.roles || 'full';
        const pipelinePack = parameters.pipelinePack || 'default';
        records.push(
          buildRecord({
            id: `stable-${event.id}`,
            scope: 'feature',
            kind: 'long_term',
            category: 'stable_decision',
            feature,
            stage: event.data.stage as number,
            agent: null,
            summary: `Stable completion with roles=${roles} pack=${pipelinePack}`,
            source: { type: 'execution-parameters', window: 'latest' },
            evidence: [{ type: 'event', ref: String(event.id) }],
            tags: [String(roles)],
            confidence: 0.7,
            createdAt: event.timestamp,
            lastSeenAt: event.timestamp,
            expiresAt: null,
            decayScore: 7,
          }),
        );
      }
    }

    if (event.type === 'ConversationOpened' && event.data?.thread) {
      const thread = event.data.thread as Record<string, any>;
      const kind = String(thread.kind ?? 'conversation');
      const anchor = String(
        thread.anchor?.artifact ??
          thread.anchor?.task ??
          thread.anchor?.scope ??
          thread.anchor?.decision ??
          'unanchored',
      );
      records.push(
        buildRecord({
          id: `conversation-open-${event.id}`,
          scope: 'feature',
          kind: 'execution',
          category: kind === 'huddle' ? 'conversation_huddle' : 'conversation_pattern',
          feature,
          stage: null,
          agent: typeof thread.initiator === 'string' ? thread.initiator : null,
          summary: `${kind} opened on ${anchor}`,
          source: { type: 'events', window: 'latest' },
          evidence: [{ type: 'event', ref: String(event.id) }],
          tags: [kind, anchor],
          confidence: 0.75,
          createdAt: event.timestamp,
          lastSeenAt: event.timestamp,
          expiresAt: null,
          decayScore: kind === 'huddle' ? 11 : 9,
        }),
      );
    }

    if (event.type === 'ConversationResolved' && event.data?.resolution) {
      const resolution = event.data.resolution as Record<string, any>;
      const decision = String(resolution.decision ?? 'resolved');
      records.push(
        buildRecord({
          id: `conversation-resolved-${event.id}`,
          scope: 'feature',
          kind: 'execution',
          category: 'conversation_pattern',
          feature,
          stage: null,
          agent: null,
          summary: `conversation resolved with decision=${decision}`,
          source: { type: 'events', window: 'latest' },
          evidence: [{ type: 'event', ref: String(event.id) }],
          tags: [decision],
          confidence: 0.7,
          createdAt: event.timestamp,
          lastSeenAt: event.timestamp,
          expiresAt: null,
          decayScore: 8,
        }),
      );
    }

    if (event.type === 'RevisionRequested' && event.data) {
      records.push(
        buildRecord({
          id: `conversation-revision-${event.id}`,
          scope: 'feature',
          kind: 'execution',
          category: 'conversation_revision',
          feature,
          stage: null,
          agent: typeof event.data.to === 'string' ? event.data.to : null,
          summary: `formal revision requested for ${String(event.data.artifact)}`,
          source: { type: 'events', window: 'latest' },
          evidence: [{ type: 'event', ref: String(event.id) }],
          tags: [String(event.data.artifact)],
          confidence: 0.85,
          createdAt: event.timestamp,
          lastSeenAt: event.timestamp,
          expiresAt: null,
          decayScore: 12,
        }),
      );
    }
  }

  const stages = execution.stages ?? {};
  const stage3 = stages['3'];
  if (stage3 && (stage3.retryCount ?? 0) > 0) {
    records.push(
      buildRecord({
        id: `retry-${feature}-3`,
        scope: 'feature',
        kind: 'execution',
        category: 'retry_lesson',
        feature,
        stage: 3,
        agent: null,
        summary: `Stage 3 retried ${stage3.retryCount} times`,
        source: { type: 'execution-stage', window: 'latest' },
        evidence: [{ type: 'stage', ref: '3' }],
        tags: ['retry'],
        confidence: 0.75,
        createdAt: now,
        lastSeenAt: now,
        expiresAt: null,
        decayScore: 8,
      }),
    );
  }

  const conversationMetrics = (execution as Record<string, any>).conversationMetrics ?? {};
  if ((conversationMetrics.unresolved ?? 0) > 0) {
    records.push(
      buildRecord({
        id: `conversation-unresolved-${feature}`,
        scope: 'feature',
        kind: 'execution',
        category: 'conversation_pattern',
        feature,
        stage: null,
        agent: null,
        summary: `${conversationMetrics.unresolved} unresolved conversation threads remain`,
        source: { type: 'execution-state', window: 'latest' },
        evidence: [{ type: 'stage', ref: 'conversation' }],
        tags: ['unresolved'],
        confidence: 0.8,
        createdAt: now,
        lastSeenAt: now,
        expiresAt: null,
        decayScore: 10,
      }),
    );
  }

  return records;
}
