/**
 * Pipeline state transitions — stage and agent status updates,
 * feedback recording, retry logic.
 */

import { emitProgress } from '../../infrastructure/process.mts';
import { EVENT_TYPES, type EventType } from '../domain/event-types.mts';
import { materializeState } from '../projectors/materialize-state.mts';
import { buildAgentFingerprints } from './pipeline-reuse.mts';
import type { PipelineExecutionState } from './state.mts';
import {
  appendRuntimeEvent,
  ensureFeatureName,
  readExecutionView,
  refreshMemory,
} from './state.mts';

export function buildStageState(name: string): import('../projectors/types.mts').StageState {
  return {
    name,
    status: 'pending',
    startTime: null,
    endTime: null,
    retryCount: 0,
    maxRetries: 2,
    failureReason: null,
    artifacts: [],
    gateResults: {},
  };
}

export function buildGateState(): import('../projectors/types.mts').GateState {
  return {
    status: 'pending',
    passed: null,
    checks: [],
    executedAt: null,
  };
}

function validateStageTransition(from: string, to: string): boolean {
  switch (`${from}:${to}`) {
    case 'pending:running':
    case 'pending:skipped':
    case 'running:completed':
    case 'running:failed':
    case 'failed:retrying':
    case 'retrying:running':
    case 'completed:running':
      return true;
    default:
      return false;
  }
}

function normalizeStageNumber(stage: number | string | null | undefined): number {
  if (stage == null) throw new Error('缺少 stage 参数');
  const stageNumber = Number(stage);
  if (!Number.isInteger(stageNumber)) {
    throw new Error('stage 必须是整数');
  }
  if (stageNumber < 1 || stageNumber > 4) {
    throw new Error('stage 必须是 1-4');
  }
  return stageNumber;
}

function mapStageStatusToEvent(status: string): EventType | null {
  switch (status) {
    case 'running':
      return EVENT_TYPES.STAGE_STARTED;
    case 'completed':
      return EVENT_TYPES.STAGE_COMPLETED;
    case 'failed':
      return EVENT_TYPES.STAGE_FAILED;
    case 'retrying':
      return EVENT_TYPES.STAGE_RETRYING;
    case 'skipped':
      return EVENT_TYPES.STAGE_SKIPPED;
    default:
      return null;
  }
}

function mapAgentStatusToEvent(status: string): EventType | null {
  switch (status) {
    case 'running':
      return EVENT_TYPES.AGENT_STARTED;
    case 'completed':
      return EVENT_TYPES.AGENT_COMPLETED;
    case 'failed':
      return EVENT_TYPES.AGENT_FAILED;
    default:
      return null;
  }
}

function normalizeArtifacts(value: string | string[] | null | undefined): string[] {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  return [value].filter(Boolean);
}

function parseGatePassed(value: boolean | string | null | undefined): boolean | null {
  if (value === undefined || value === null) return null;
  if (typeof value === 'boolean') return value;
  if (value === 'true') return true;
  if (value === 'false') return false;
  throw new Error('gate-passed 必须是 true 或 false');
}

function inferArtifactFromPrompt(agent: string, prompt?: string): string | undefined {
  if (!prompt) return undefined;
  const prefix = `${agent}:`;
  if (!prompt.startsWith(prefix)) return undefined;
  const artifact = prompt.slice(prefix.length).trim();
  return artifact.length > 0 ? artifact : undefined;
}

export function updateStage(
  feature: string,
  stage: number | string,
  status: string,
  {
    cwd = process.cwd(),
    reason,
    artifacts,
    gate,
    gatePassed,
  }: {
    cwd?: string;
    reason?: string;
    artifacts?: string | string[];
    gate?: string;
    gatePassed?: boolean | string | null;
  } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  if (!status) throw new Error('缺少 status 参数');
  const validStatuses = ['running', 'completed', 'failed', 'retrying', 'skipped'];
  if (!validStatuses.includes(status)) {
    throw new Error(`无效状态: ${status}（允许: ${validStatuses.join(' ')}）`);
  }

  const stageNumber = normalizeStageNumber(stage);
  const { state: currentState } = materializeState(feature, cwd);
  const currentStage = currentState.stages ? currentState.stages[String(stageNumber)] : null;
  const currentStatus = currentStage ? currentStage.status : 'pending';
  if (!validateStageTransition(currentStatus, status)) {
    throw new Error(`无效的状态转换: ${currentStatus} → ${status}（阶段 ${stageNumber}）`);
  }

  const eventType = mapStageStatusToEvent(status);
  if (!eventType) throw new Error(`无效状态: ${status}`);

  if (status === 'running' && currentState.status === 'paused') {
    appendRuntimeEvent(cwd, feature, EVENT_TYPES.PIPELINE_RESUMED, {
      stage: stageNumber,
      requestedBy: 'runtime',
    });
  }

  appendRuntimeEvent(cwd, feature, eventType, {
    stage: stageNumber,
    ...(reason ? { reason } : {}),
  });

  if (status === 'running') {
    emitProgress(cwd, feature, { type: 'stage-start', data: { stage: stageNumber } });
  } else if (status === 'completed') {
    emitProgress(cwd, feature, { type: 'stage-complete', data: { stage: stageNumber } });
  } else if (status === 'failed') {
    emitProgress(cwd, feature, { type: 'stage-failed', data: { stage: stageNumber } });
  }

  const artifactList = normalizeArtifacts(artifacts);
  for (const artifact of artifactList) {
    appendRuntimeEvent(cwd, feature, EVENT_TYPES.ARTIFACT_RECORDED, {
      artifact,
      stage: stageNumber,
    });
  }

  const passed = parseGatePassed(gatePassed);
  if (gate && passed !== null) {
    appendRuntimeEvent(cwd, feature, EVENT_TYPES.GATE_EVALUATED, {
      gate,
      passed,
      stage: stageNumber,
    });
  }

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

export function updateAgent(
  feature: string,
  stage: number | string,
  agent: string,
  status: string,
  {
    cwd = process.cwd(),
    reason,
    prompt,
    promptFingerprint,
    dependencyArtifacts,
    opts,
  }: {
    cwd?: string;
    reason?: string;
    prompt?: string;
    promptFingerprint?: string;
    dependencyArtifacts?: string[];
    opts?: Record<string, unknown>;
  } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  if (!agent) throw new Error('缺少 agent 参数');
  if (!status) throw new Error('缺少 status 参数');
  const validStatuses = ['running', 'completed', 'failed'];
  if (!validStatuses.includes(status)) {
    throw new Error(`无效状态: ${status}`);
  }
  const stageNumber = normalizeStageNumber(stage);
  const eventType = mapAgentStatusToEvent(status);
  if (!eventType) throw new Error(`无效状态: ${status}`);

  const currentExecution = readExecutionView(cwd, feature);
  const currentAgent = currentExecution.stages?.[String(stageNumber)]?.agents?.[agent];
  const hasFingerprintInput =
    prompt !== undefined ||
    promptFingerprint !== undefined ||
    (dependencyArtifacts !== undefined && dependencyArtifacts.length > 0) ||
    (opts !== undefined && Object.keys(opts).length > 0);
  const fingerprints =
    !hasFingerprintInput && currentAgent?.promptFingerprint && currentAgent?.inputDigest
      ? {
          promptFingerprint: {
            algorithm: 'sha256' as const,
            value: currentAgent.promptFingerprint,
          },
          inputDigest: { algorithm: 'sha256' as const, value: currentAgent.inputDigest },
        }
      : buildAgentFingerprints(feature, agent, stageNumber, {
          cwd,
          prompt,
          promptFingerprint,
          dependencyArtifacts,
          opts,
        });

  appendRuntimeEvent(cwd, feature, eventType, {
    agent,
    stage: stageNumber,
    promptFingerprint: fingerprints.promptFingerprint.value,
    inputDigest: fingerprints.inputDigest.value,
    ...(inferArtifactFromPrompt(agent, prompt)
      ? { artifact: inferArtifactFromPrompt(agent, prompt) }
      : {}),
    ...(reason ? { reason } : {}),
  });

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

export function recordFeedback(
  feature: string,
  opts: {
    from: string;
    to: string;
    artifact: string;
    reason: string;
    priority?: string;
    cwd?: string;
  },
): PipelineExecutionState {
  const { cwd = process.cwd(), from, to, artifact, reason, priority = 'recommended' } = opts;
  ensureFeatureName(feature);
  if (!from) throw new Error('缺少 from 参数');
  if (!to) throw new Error('缺少 to 参数');
  if (!artifact) throw new Error('缺少 artifact 参数');
  if (!reason) throw new Error('缺少 reason 参数');

  const execution = readExecutionView(cwd, feature);
  const feedbackLoops = (execution as any).feedbackLoops || { currentRound: 0, maxRounds: 2 };
  const { maxRounds = 2, rounds = {} } = feedbackLoops;
  // 按产物计数：防死循环的原意是「同一产物不要反复返工」，而不是限制 feature 的一生。
  // 旧版本创建的 run 没有 rounds，从 0 起算——这正是要修的那种「活得久就失去反馈能力」。
  const artifactRound = Number((rounds as Record<string, unknown>)[artifact] ?? 0);
  if (artifactRound >= maxRounds) {
    throw new Error(
      `产物 ${artifact} 的反馈循环已达上限（${artifactRound}/${maxRounds}），不再接受修订请求`,
    );
  }

  appendRuntimeEvent(cwd, feature, EVENT_TYPES.REVISION_REQUESTED, {
    from,
    to,
    artifact,
    reason,
    priority,
  });

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

export function recordUserChoice(
  feature: string,
  opts: {
    choiceType: string;
    selected: string;
    options?: string[];
    reason?: string;
    agent?: string;
    stage?: number | null;
    cwd?: string;
  },
): PipelineExecutionState {
  const { cwd = process.cwd(), choiceType, selected, options, reason, agent, stage } = opts;
  ensureFeatureName(feature);
  if (!choiceType) throw new Error('缺少 choiceType 参数');
  if (!selected) throw new Error('缺少 selected 参数');

  appendRuntimeEvent(cwd, feature, EVENT_TYPES.USER_CHOICE_RECORDED, {
    choiceType,
    selected,
    ...(options ? { options } : {}),
    ...(reason ? { reason } : {}),
    ...(agent ? { agent } : {}),
    ...(stage != null ? { stage } : {}),
  });

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

export function retryAgent(
  feature: string,
  stage: number | string,
  agentName: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  if (!agentName) throw new Error('缺少 agent 参数');
  const stageNum = Number(stage);

  const { state: cur } = materializeState(feature, cwd);
  const agentState = cur.stages?.[String(stageNum)]?.agents?.[agentName];
  if (!agentState || agentState.status !== 'failed') {
    throw new Error(
      `Agent ${agentName} 状态为 ${agentState?.status ?? 'unknown'}，只有 failed 状态可以重试`,
    );
  }
  const maxRetries = agentState.maxRetries ?? 2;
  if ((agentState.retryCount ?? 0) >= maxRetries) {
    throw new Error(
      `Agent ${agentName} 已达最大重试次数（${agentState.retryCount}/${maxRetries}）`,
    );
  }

  appendRuntimeEvent(cwd, feature, EVENT_TYPES.AGENT_RETRY_SCHEDULED, {
    agent: agentName,
    stage: stageNum,
  });
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.AGENT_STARTED, {
    agent: agentName,
    stage: stageNum,
  });

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

export function retryStage(
  feature: string,
  stage: number | string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  const stageNum = Number(stage);

  const { state: cur } = materializeState(feature, cwd);
  const stageState = cur.stages?.[String(stageNum)];
  if (!stageState || stageState.status !== 'failed') {
    throw new Error(
      `阶段 ${stageNum} 状态为 ${stageState?.status ?? 'pending'}，只有 failed 状态可以重试`,
    );
  }
  const maxRetries = stageState.maxRetries ?? 2;
  if ((stageState.retryCount ?? 0) >= maxRetries) {
    throw new Error(`阶段 ${stageNum} 已达最大重试次数（${stageState.retryCount}/${maxRetries}）`);
  }

  appendRuntimeEvent(cwd, feature, EVENT_TYPES.STAGE_RETRYING, { stage: stageNum });
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.STAGE_STARTED, { stage: stageNum });

  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}
