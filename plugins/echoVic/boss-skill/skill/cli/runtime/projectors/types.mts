import type {
  ConversationMessage,
  ConversationResolution,
  ConversationThread,
  DerivedTodo,
} from '../domain/conversation-types.mts';
import type { AgentStatus, PipelineStatus, StageStatus } from '../domain/state-constants.mts';

type UnknownRecord = Record<string, unknown>;
type AgentLifecycleStatus = AgentStatus | 'retrying';

export interface PluginSummary {
  name: string;
  version: string;
  type: string;
  dependencies?: string[];
  manifestPath?: string;
}

export interface PluginHookResult {
  plugin: PluginSummary;
  hook: string;
  stage: number | null;
  exitCode: number;
  timestamp: string;
}

export interface AgentState {
  status: AgentLifecycleStatus;
  startTime: string | null;
  endTime: string | null;
  retryCount: number;
  maxRetries: number;
  failureReason: string | null;
  promptFingerprint?: string | null;
  inputDigest?: string | null;
}

export interface GateResult {
  passed: boolean;
  executedAt: string;
  checks: unknown[];
}

export interface StageState {
  name: string;
  status: StageStatus;
  startTime: string | null;
  endTime: string | null;
  retryCount: number;
  maxRetries: number;
  failureReason: string | null;
  artifacts: string[];
  gateResults: Record<string, GateResult>;
  agents?: Record<string, AgentState>;
}

export interface GateState {
  status: StageStatus;
  passed: boolean | null;
  checks: unknown[];
  executedAt: string | null;
}

export type WorkflowExecutionNodeStatus =
  | 'pending'
  | 'ready'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped'
  | 'reused'
  | 'blocked';

export interface WorkflowExecutionNode {
  id: string;
  kind: string;
  artifact?: string;
  gate?: string;
  agent?: string | string[] | null;
  stage: number;
  phase: string;
  inputs: string[];
  /** 该节点写入的路径集合；用于并行安全组分组。缺省回退到 artifact 名。 */
  writes?: string[];
  optional: boolean;
  status: WorkflowExecutionNodeStatus;
  /**
   * 计划编译时经 spread 带入，写集分组取代它之后已无人读取。
   * 保留声明是为了让本类型如实描述 execution.json 的落盘内容：
   * 类型漏掉真实存在的字段，会让任何从类型出发的审计得出错误结论。
   */
  parallelGroup?: string;
  description?: string;
  decision?: string;
  reason?: string;
  updatedAt?: string;
}

export interface WorkflowExecutionState {
  planPath: string;
  hash: string;
  nodes: Record<string, WorkflowExecutionNode>;
  nextNodeIds: string[];
  resumedFromRunId?: string;
  updatedAt?: string;
}

export interface ExecutionMetrics {
  totalDuration: number | null;
  stageTimings: Record<string, number>;
  gatePassRate: number | null;
  retryTotal: number;
  agentSuccessCount: number;
  agentFailureCount: number;
  meanRetriesPerStage: number;
  revisionLoopCount: number;
  pluginFailureCount: number;
}

export interface PluginLifecycleState {
  discovered: PluginSummary[];
  activated: PluginSummary[];
  executed: PluginHookResult[];
  failed: PluginHookResult[];
}

export interface RevisionRequest {
  from: string;
  to: string;
  artifact: string;
  reason: string;
  priority: string;
  timestamp: string;
  resolved: boolean;
}

export interface ConversationState {
  threads: ConversationThread[];
  messages: ConversationMessage[];
  resolutions: ConversationResolution[];
}

export interface ConversationMetrics {
  opened: number;
  resolved: number;
  todos: number;
  huddles: number;
  unresolved: number;
}

export interface ExecutionState {
  schemaVersion: string;
  feature: string;
  createdAt: string;
  updatedAt: string;
  status: PipelineStatus;
  parameters: UnknownRecord;
  stages: Record<string, StageState>;
  qualityGates: Record<string, GateState>;
  metrics: ExecutionMetrics;
  plugins: PluginSummary[];
  pluginLifecycle: PluginLifecycleState;
  conversations: ConversationState;
  derivedTodos: DerivedTodo[];
  conversationMetrics: ConversationMetrics;
  humanInterventions: unknown[];
  revisionRequests: RevisionRequest[];
  feedbackLoops: {
    maxRounds: number;
    /** 全部产物的返工总轮次；保留供报表与既有消费方使用。 */
    currentRound: number;
    /** 按产物分别计数：上限限制的是同一产物的返工轮次，不是 feature 的一生。 */
    rounds: Record<string, number>;
  };
  workflow?: WorkflowExecutionState;
  pause?: {
    paused: boolean;
    reason: string;
    requestedBy: string;
    pausedAt: string;
  } | null;
}

export interface RuntimeEvent {
  id: number;
  type: string;
  timestamp: string;
  data: UnknownRecord;
}
