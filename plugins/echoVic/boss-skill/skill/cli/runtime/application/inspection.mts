import * as fs from 'node:fs';
import * as path from 'node:path';
import { readJsonlTolerant } from '../../infrastructure/fs.mts';
import type { FeatureMemorySummary } from '../memory/store.mts';
import {
  type ExecutionState,
  projectState,
  type RuntimeEvent,
} from '../projectors/materialize-state.mts';
import * as pipelineRuntime from './pipeline.mts';

export interface ActiveAgentSummary {
  stage: number;
  agent: string;
  status: string;
}

export interface CurrentStageSummary {
  id: number;
  name: string;
  status: string;
}

export interface FailureSummary {
  scope: 'stage' | 'agent';
  stage: number;
  reason: string;
  agent?: string;
}

export interface PipelineInspection {
  feature: string;
  runId: string;
  status: string;
  currentStage: CurrentStageSummary | null;
  readyArtifacts: string[];
  activeAgents: ActiveAgentSummary[];
  recentFailures: FailureSummary[];
  memory: FeatureMemorySummary;
  pack: {
    name: string;
    version: string;
  };
  plugins: {
    active: ExecutionState['plugins'];
    discovered: ExecutionState['pluginLifecycle']['discovered'];
    activated: ExecutionState['pluginLifecycle']['activated'];
    executed: ExecutionState['pluginLifecycle']['executed'];
    failed: ExecutionState['pluginLifecycle']['failed'];
  };
  metrics: ExecutionState['metrics'];
  conversationMetrics: ExecutionState['conversationMetrics'];
  derivedTodos: ExecutionState['derivedTodos'];
  pause: ExecutionState['pause'] | null;
  artifactDag: {
    initialized: unknown;
    current: unknown;
    matches: boolean | null;
    warning: string | null;
  };
}

export interface EventInspection<TEvent = RuntimeEvent | Record<string, unknown>> {
  feature: string;
  limit: number;
  type: string | null;
  events: TEvent[];
}

function ensureFeatureName(feature: string): void {
  if (!feature) {
    throw new Error('缺少 feature 参数');
  }
}

export function readExecution(feature: string, cwd = process.cwd()): ExecutionState {
  const executionPath = path.join(cwd, '.boss', feature, '.meta', 'execution.json');
  if (!fs.existsSync(executionPath)) {
    throw new Error(`未找到执行文件: ${path.relative(cwd, executionPath)}`);
  }
  return JSON.parse(fs.readFileSync(executionPath, 'utf8')) as ExecutionState;
}

export function readEvents(feature: string, cwd = process.cwd()): RuntimeEvent[] {
  const eventsPath = path.join(cwd, '.boss', feature, '.meta', 'events.jsonl');
  if (!fs.existsSync(eventsPath)) {
    throw new Error(`未找到事件文件: ${path.relative(cwd, eventsPath)}`);
  }
  return readJsonlTolerant<RuntimeEvent>(eventsPath).records;
}

export function readProgress(feature: string, cwd = process.cwd()): Array<Record<string, unknown>> {
  const progressPath = path.join(cwd, '.boss', feature, '.meta', 'progress.jsonl');
  if (!fs.existsSync(progressPath)) {
    return [];
  }
  return readJsonlTolerant<Record<string, unknown>>(progressPath).records;
}

function sortedStageEntries(
  stages: ExecutionState['stages'],
): Array<[string, ExecutionState['stages'][string]]> {
  return Object.entries(stages ?? {}).sort((left, right) => Number(left[0]) - Number(right[0]));
}

function getActiveAgents(execution: ExecutionState): ActiveAgentSummary[] {
  const activeAgents: ActiveAgentSummary[] = [];
  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    const agents = stage?.agents ?? {};
    for (const [agentName, agentState] of Object.entries(agents)) {
      if (!agentState || (agentState.status !== 'running' && agentState.status !== 'retrying')) {
        continue;
      }
      activeAgents.push({
        stage: Number(stageId),
        agent: agentName,
        status: agentState.status,
      });
    }
  }
  return activeAgents;
}

function getCurrentStage(
  execution: ExecutionState,
  activeAgents: ActiveAgentSummary[],
): CurrentStageSummary | null {
  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    if (stage && (stage.status === 'running' || stage.status === 'retrying')) {
      return {
        id: Number(stageId),
        name: stage.name || '',
        status: stage.status,
      };
    }
  }

  if (activeAgents.length > 0) {
    const stageId = activeAgents[0]!.stage;
    const stage = execution.stages[String(stageId)] ?? ({} as ExecutionState['stages'][string]);
    return {
      id: stageId,
      name: stage?.name || '',
      status: stage?.status || 'pending',
    };
  }

  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    if (stage && stage.status === 'failed') {
      return {
        id: Number(stageId),
        name: stage.name || '',
        status: stage.status,
      };
    }
  }

  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    if (stage && stage.status === 'pending') {
      return {
        id: Number(stageId),
        name: stage.name || '',
        status: stage.status,
      };
    }
  }

  const stageEntries = sortedStageEntries(execution.stages);
  if (stageEntries.length === 0) {
    return null;
  }
  const [stageId, stage] = stageEntries[stageEntries.length - 1]!;
  return {
    id: Number(stageId),
    name: stage?.name || '',
    status: stage?.status || 'pending',
  };
}

function getRecentFailures(execution: ExecutionState): FailureSummary[] {
  const failures: FailureSummary[] = [];
  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    if (stage && stage.status === 'failed') {
      failures.push({
        scope: 'stage',
        stage: Number(stageId),
        reason: stage.failureReason || '',
      });
    }
    const agents = stage?.agents ?? {};
    for (const [agentName, agentState] of Object.entries(agents)) {
      if (!agentState || agentState.status !== 'failed') {
        continue;
      }
      failures.push({
        scope: 'agent',
        stage: Number(stageId),
        agent: agentName,
        reason: agentState.failureReason || '',
      });
    }
  }
  return failures;
}

function readFeatureSummary(feature: string, cwd = process.cwd()): FeatureMemorySummary {
  const summaryPath = path.join(cwd, '.boss', feature, '.meta', 'memory-summary.json');
  try {
    if (!fs.existsSync(summaryPath)) {
      throw new Error('missing summary');
    }
    return JSON.parse(fs.readFileSync(summaryPath, 'utf8')) as FeatureMemorySummary;
  } catch {
    return {
      feature,
      generatedAt: null,
      startupSummary: [],
      agentSections: {},
    };
  }
}

export function inspectPipeline(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): PipelineInspection {
  ensureFeatureName(feature);
  const execution = readExecution(feature, cwd);
  const activeAgents = getActiveAgents(execution);
  const readyArtifacts = pipelineRuntime
    .getReadyArtifacts(feature, { cwd })
    .map((item) => item.artifact);
  const initializedDag = execution.parameters?.artifactDag || null;
  let currentDag: unknown = null;
  let dagMatches: boolean | null = null;
  let dagWarning: string | null = null;
  try {
    currentDag = pipelineRuntime.getArtifactDagFingerprint(feature, { cwd });
    const initialHash =
      initializedDag &&
      typeof initializedDag === 'object' &&
      'hash' in initializedDag &&
      initializedDag.hash &&
      typeof initializedDag.hash === 'object' &&
      'value' in initializedDag.hash
        ? initializedDag.hash.value
        : null;
    const currentHash =
      currentDag &&
      typeof currentDag === 'object' &&
      'hash' in currentDag &&
      currentDag.hash &&
      typeof currentDag.hash === 'object' &&
      'value' in currentDag.hash
        ? currentDag.hash.value
        : null;
    dagMatches =
      typeof initialHash === 'string' && typeof currentHash === 'string'
        ? initialHash === currentHash
        : null;
    if (dagMatches === false) {
      dagWarning =
        'Artifact DAG has changed since PipelineInitialized; cached agent/artifact decisions may be stale.';
    }
  } catch (err) {
    dagWarning = (err as Error).message;
  }

  return {
    feature,
    runId: typeof execution.parameters?.runId === 'string' ? execution.parameters.runId : '',
    status: execution.status,
    currentStage: getCurrentStage(execution, activeAgents),
    readyArtifacts,
    activeAgents,
    recentFailures: getRecentFailures(execution),
    memory: readFeatureSummary(feature, cwd),
    pack: {
      name:
        execution.parameters && typeof execution.parameters.pipelinePack === 'string'
          ? execution.parameters.pipelinePack
          : 'default',
      version:
        execution.parameters && typeof execution.parameters.pipelinePackVersion === 'string'
          ? execution.parameters.pipelinePackVersion
          : '',
    },
    plugins: {
      active: Array.isArray(execution.plugins) ? execution.plugins : [],
      discovered:
        execution.pluginLifecycle && Array.isArray(execution.pluginLifecycle.discovered)
          ? execution.pluginLifecycle.discovered
          : [],
      activated:
        execution.pluginLifecycle && Array.isArray(execution.pluginLifecycle.activated)
          ? execution.pluginLifecycle.activated
          : [],
      executed:
        execution.pluginLifecycle && Array.isArray(execution.pluginLifecycle.executed)
          ? execution.pluginLifecycle.executed
          : [],
      failed:
        execution.pluginLifecycle && Array.isArray(execution.pluginLifecycle.failed)
          ? execution.pluginLifecycle.failed
          : [],
    },
    metrics: execution.metrics || {
      totalDuration: null,
      stageTimings: {},
      gatePassRate: null,
      retryTotal: 0,
      agentSuccessCount: 0,
      agentFailureCount: 0,
      meanRetriesPerStage: 0,
      revisionLoopCount: 0,
      pluginFailureCount: 0,
    },
    conversationMetrics: execution.conversationMetrics || {
      opened: 0,
      resolved: 0,
      todos: 0,
      huddles: 0,
      unresolved: 0,
    },
    derivedTodos: Array.isArray(execution.derivedTodos) ? execution.derivedTodos : [],
    pause: execution.pause || null,
    artifactDag: {
      initialized: initializedDag,
      current: currentDag,
      matches: dagMatches,
      warning: dagWarning,
    },
  };
}

export function inspectEvents(
  feature: string,
  {
    cwd = process.cwd(),
    limit = 20,
    type = '',
  }: { cwd?: string; limit?: number | string; type?: string } = {},
): EventInspection<RuntimeEvent> {
  ensureFeatureName(feature);
  const max = Number(limit);
  if (!Number.isInteger(max) || max < 1) {
    throw new Error('limit 必须是正整数');
  }

  let events = readEvents(feature, cwd).slice().reverse();
  if (type) {
    events = events.filter((event) => event.type === type);
  }

  return {
    feature,
    limit: max,
    type: type || null,
    events: events.slice(0, max),
  };
}

export function inspectProgress(
  feature: string,
  {
    cwd = process.cwd(),
    limit = 20,
    type = '',
  }: { cwd?: string; limit?: number | string; type?: string } = {},
): EventInspection<Record<string, unknown>> {
  ensureFeatureName(feature);
  const max = Number(limit);
  if (!Number.isInteger(max) || max < 1) {
    throw new Error('limit 必须是正整数');
  }

  let events = readProgress(feature, cwd).slice().reverse();
  if (type) {
    events = events.filter((event) => event.type === type);
  }

  return {
    feature,
    limit: max,
    type: type || null,
    events: events.slice(0, max),
  };
}

function buildStageSummary(execution: ExecutionState): {
  status: string;
  stages: ExecutionState['stages'];
  qualityGates: ExecutionState['qualityGates'];
  metrics: ExecutionState['metrics'];
} {
  const stages: ExecutionState['stages'] = {};
  for (const [stageId, stage] of sortedStageEntries(execution.stages)) {
    stages[stageId] = stage;
  }
  return {
    status: execution.status,
    stages,
    qualityGates: execution.qualityGates || {},
    metrics: execution.metrics || {
      totalDuration: null,
      stageTimings: {},
      gatePassRate: null,
      retryTotal: 0,
      agentSuccessCount: 0,
      agentFailureCount: 0,
      meanRetriesPerStage: 0,
      revisionLoopCount: 0,
      pluginFailureCount: 0,
    },
  };
}

export function checkStage(
  feature: string,
  stageId = '',
  { cwd = process.cwd() }: { cwd?: string } = {},
): ExecutionState['stages'][string] | ReturnType<typeof buildStageSummary> | null {
  ensureFeatureName(feature);
  const execution = readExecution(feature, cwd);
  if (!stageId) {
    return buildStageSummary(execution);
  }
  const key = String(stageId);
  return execution.stages && execution.stages[key] ? execution.stages[key] : null;
}

export function checkCanProceed(
  feature: string,
  stageId: string | number,
  { cwd = process.cwd() }: { cwd?: string } = {},
): { ok: boolean; reason: string } {
  ensureFeatureName(feature);
  if (!stageId) {
    throw new Error('stage 必须是 1-4');
  }
  const execution = readExecution(feature, cwd);
  const key = String(stageId);
  const stage = execution.stages && execution.stages[key] ? execution.stages[key] : undefined;
  const status = stage?.status || 'pending';
  if (status === 'completed' || status === 'skipped') {
    return { ok: false, reason: `阶段 ${stageId} 已经完成（${status}），无需再执行` };
  }
  if (Number(stageId) === 1) {
    return {
      ok: status === 'pending',
      reason: status === 'pending' ? '' : `阶段 1 当前状态为 ${status}`,
    };
  }
  const prevStage =
    execution.stages && execution.stages[String(Number(stageId) - 1)]
      ? execution.stages[String(Number(stageId) - 1)]
      : undefined;
  const prevStatus = prevStage?.status || 'pending';
  const ok = prevStatus === 'completed' || prevStatus === 'skipped';
  return {
    ok,
    reason: ok
      ? ''
      : `阶段 ${stageId} 不能开始：阶段 ${Number(stageId) - 1} 状态为 ${prevStatus}（需要 completed 或 skipped）`,
  };
}

export function checkCanRetry(
  feature: string,
  stageId: string | number,
  { cwd = process.cwd() }: { cwd?: string } = {},
): { ok: boolean; reason: string } {
  ensureFeatureName(feature);
  if (!stageId) {
    throw new Error('stage 必须是 1-4');
  }
  const execution = readExecution(feature, cwd);
  const stage =
    execution.stages && execution.stages[String(stageId)]
      ? execution.stages[String(stageId)]
      : undefined;
  const status = stage?.status || 'pending';
  const retryCount = Number(stage?.retryCount || 0);
  const maxRetries = Number(stage?.maxRetries || 0);
  if (status !== 'failed') {
    return { ok: false, reason: `阶段 ${stageId} 状态为 ${status}，只有 failed 状态可以重试` };
  }
  if (retryCount >= maxRetries) {
    return {
      ok: false,
      reason: `阶段 ${stageId} 已达到最大重试次数（${retryCount}/${maxRetries}）`,
    };
  }
  return { ok: true, reason: '' };
}

export function replayEvents(
  feature: string,
  {
    cwd = process.cwd(),
    limit = 20,
    type = '',
  }: { cwd?: string; limit?: number | string; type?: string } = {},
): EventInspection<RuntimeEvent> {
  return inspectEvents(feature, { cwd, limit, type });
}

export function replaySnapshot(
  feature: string,
  at: string | number,
  { cwd = process.cwd() }: { cwd?: string } = {},
): { feature: string; at: number; snapshot: ExecutionState } {
  ensureFeatureName(feature);
  const target = Number(at);
  if (!Number.isInteger(target) || target < 1) {
    throw new Error('at 必须是正整数');
  }
  const allEvents = readEvents(feature, cwd);
  return {
    feature,
    at: target,
    snapshot: projectState(allEvents.slice(0, target), feature),
  };
}
