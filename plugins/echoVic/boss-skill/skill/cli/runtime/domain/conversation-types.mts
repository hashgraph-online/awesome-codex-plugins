export interface ConversationAnchor {
  artifact?: string;
  task?: string;
  scope?: string;
  decision?: string;
}

export interface ConversationThread {
  id: string;
  kind: 'ask' | 'challenge' | 'propose' | 'request_change' | 'escalate' | 'huddle';
  anchor: ConversationAnchor;
  initiator: string;
  participants: string[];
  status: 'open' | 'discussing' | 'converged' | 'materialized' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
  updatedAt: string;
}

export interface ConversationEvidence {
  type: 'artifact' | 'file' | 'test';
  ref: string;
}

export interface ConversationMessage {
  id: string;
  threadId: string;
  from: string;
  to: string[];
  intent: 'question' | 'objection' | 'proposal' | 'evidence' | 'decision';
  content: string;
  evidence?: ConversationEvidence[];
  createdAt: string;
}

export interface ResolutionTodo {
  id: string;
  owner: string;
  title: string;
  status: 'pending' | 'queued' | 'in_progress';
}

export interface ConversationResolution {
  threadId: string;
  summary: string;
  decision: string;
  todos: ResolutionTodo[];
  createdAt: string;
}

export interface DerivedTodo {
  id: string;
  sourceThreadId: string;
  title: string;
  owner: string;
  type: 'change' | 'clarify' | 'verify' | 'doc_update' | 'followup';
  status: 'pending' | 'queued' | 'in_progress' | 'done' | 'blocked' | 'cancelled';
  successCriteria: string[];
  impact: { artifacts: string[]; scope: string[] };
  dispatchHint: { stage: number; agent: string };
  createdAt: string;
}
