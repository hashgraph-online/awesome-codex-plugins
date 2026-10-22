/**
 * Pipeline — main module that re-exports all split pipeline modules
 * and contains initPipeline, pausePipeline, getReadyArtifacts,
 * tech stack caching, and stall detection.
 */
import * as fs from 'node:fs';
import * as path from 'node:path';
import { EVENT_TYPES } from '../domain/event-types.mts';
import { materializeState } from '../projectors/materialize-state.mts';
import type { RuntimeEvent } from '../projectors/types.mts';
import { getPackStateParameters, resolvePipelinePack } from './packs.mts';
import {
  collectCompletedArtifacts,
  describeArtifactDag,
  hashRuntimeValue,
  loadDagForFeature,
  resolveReadyArtifacts,
} from './pipeline-dag.mts';
import { buildGateState, buildStageState } from './pipeline-transitions.mts';
import type { CheckStallResult, ReadyArtifact, StalledAgent } from './pipeline-types.mts';
import { registerPlugins as registerPluginsRuntime } from './plugins.mts';
import {
  type ArtifactDag,
  appendRuntimeEvent,
  ensureDir,
  ensureFeatureName,
  type PipelineExecutionState,
  readExecutionView,
  readJson,
  refreshMemory,
  writeJson,
} from './state.mts';
import {
  compileWorkflowPlan,
  createWorkflowExecutionState,
  persistWorkflowPlan,
} from './workflow.mts';

// ── Re-exports ─────────────────────────────────────────────────

// Artifacts
export {
  collectCompletedArtifactsVersioned,
  getArtifactVersion,
  recordArtifact,
  recordArtifacts,
  skipUpTo,
} from './pipeline-artifacts.mts';
// DAG
export {
  getArtifactDagFingerprint,
  getArtifactStatus,
  hashRuntimeValue,
  listArtifactStatuses,
} from './pipeline-dag.mts';
// Agent reuse
export { evaluateAgentReuse } from './pipeline-reuse.mts';
// Transitions
export {
  buildGateState,
  buildStageState,
  recordFeedback,
  recordUserChoice,
  retryAgent,
  retryStage,
  updateAgent,
  updateStage,
} from './pipeline-transitions.mts';
// Types
export type {
  AgentReuseDecision,
  AgentReuseInput,
  ArtifactDagFingerprint,
  ArtifactStatus,
  CheckStallResult,
  ReadyArtifact,
  RuntimeHashDescriptor,
  StalledAgent,
} from './pipeline-types.mts';
export {
  FORMAL_SOURCE_OF_TRUTH_ARTIFACTS,
  isFormalSourceOfTruthArtifact,
} from './pipeline-types.mts';

// ── initPipeline ───────────────────────────────────────────────

export function initPipeline(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  const bossDir = path.join(cwd, '.boss', feature);
  const metaDir = path.join(bossDir, '.meta');
  ensureDir(metaDir);

  const execJsonPath = path.join(metaDir, 'execution.json');
  const eventsFile = path.join(metaDir, 'events.jsonl');
  const execExists = fs.existsSync(execJsonPath);
  const eventsExists = fs.existsSync(eventsFile);
  if (execExists && eventsExists) {
    throw new Error(`流水线已存在: ${path.relative(cwd, metaDir)}`);
  }
  if (execExists || eventsExists) {
    throw new Error(`检测到不完整的流水线状态: ${path.relative(cwd, metaDir)}`);
  }

  const now = new Date().toISOString();
  const initialState: PipelineExecutionState = {
    schemaVersion: '0.2.0',
    feature,
    createdAt: now,
    updatedAt: now,
    status: 'initialized',
    parameters: {
      pipelinePack: 'default',
      pipelinePackVersion: '',
      enabledGates: [],
      activeAgents: [],
      packConfig: {},
      skipUI: false,
      skipDeploy: false,
      quick: false,
      hitlLevel: 'auto',
      roles: 'full',
    },
    stages: {
      '1': buildStageState('planning'),
      '2': buildStageState('review'),
      '3': buildStageState('development'),
      '4': buildStageState('deployment'),
    },
    qualityGates: {
      gate0: buildGateState(),
      gate1: buildGateState(),
      gate2: buildGateState(),
    },
    metrics: {
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
    plugins: [],
    pluginLifecycle: {
      discovered: [],
      activated: [],
      executed: [],
      failed: [],
    },
    conversations: {
      threads: [],
      messages: [],
      resolutions: [],
    },
    derivedTodos: [],
    conversationMetrics: {
      opened: 0,
      resolved: 0,
      todos: 0,
      huddles: 0,
      unresolved: 0,
    },
    humanInterventions: [],
    revisionRequests: [],
    feedbackLoops: { maxRounds: 2, currentRound: 0, rounds: {} },
    pause: null,
  };

  const pack = resolvePipelinePack(cwd);
  const packParameters = getPackStateParameters(pack);
  const packDagPath =
    typeof packParameters.packConfig?.artifactDag === 'string'
      ? packParameters.packConfig.artifactDag
      : undefined;
  const artifactDag = describeArtifactDag(cwd, feature, packDagPath);
  const artifactDagPath = path.isAbsolute(artifactDag.path)
    ? artifactDag.path
    : path.resolve(cwd, artifactDag.path);
  const workflowPlan = compileWorkflowPlan({
    feature,
    pack,
    artifactDag: readJson<ArtifactDag>(artifactDagPath),
    artifactDagFingerprint: artifactDag,
  });
  const workflow = persistWorkflowPlan({ cwd, feature, plan: workflowPlan });
  const runId = hashRuntimeValue({
    feature,
    createdAt: now,
    workflowHash: workflow.workflowHash,
    artifactDag,
  }).value;
  const initializedWithPack: PipelineExecutionState = {
    ...initialState,
    workflow: createWorkflowExecutionState({
      plan: workflow.plan,
      workflowPlanPath: workflow.workflowPlanPath,
      workflowHash: workflow.workflowHash,
    }),
    parameters: {
      ...initialState.parameters,
      ...packParameters,
      artifactDag,
      workflowPlanPath: workflow.workflowPlanPath,
      workflowHash: workflow.workflowHash.value,
      packHash: workflow.packHash.value,
      artifactDagHash: workflow.artifactDagHash.value,
      runId,
    },
  };

  writeJson(execJsonPath, initializedWithPack);
  const initEvent: RuntimeEvent = {
    id: 1,
    type: EVENT_TYPES.PIPELINE_INITIALIZED,
    timestamp: now,
    data: {
      initialState: initializedWithPack,
      artifactDag,
      workflowPlan: {
        path: workflow.workflowPlanPath,
        hash: workflow.workflowHash,
      },
      runId,
    },
  };
  const events: RuntimeEvent[] = [initEvent];
  if (pack.name !== 'default') {
    events.push({
      id: 2,
      type: EVENT_TYPES.PACK_APPLIED,
      timestamp: now,
      data: {
        pack: pack.name,
        version: pack.version,
        config: pack.config,
        parameters: packParameters,
      },
    });
  }
  fs.writeFileSync(
    eventsFile,
    `${events.map((event) => JSON.stringify(event)).join('\n')}\n`,
    'utf8',
  );
  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

// ── pausePipeline ──────────────────────────────────────────────

export function pausePipeline(
  feature: string,
  {
    cwd = process.cwd(),
    reason = '',
    requestedBy = 'user',
  }: { cwd?: string; reason?: string; requestedBy?: string } = {},
): PipelineExecutionState {
  ensureFeatureName(feature);
  const execution = readExecutionView(cwd, feature);
  if (execution.status === 'paused') {
    throw new Error('流水线已处于暂停状态');
  }
  if (execution.status === 'completed' || execution.status === 'failed') {
    throw new Error(`流水线已终止（${execution.status}），无法暂停`);
  }
  appendRuntimeEvent(cwd, feature, EVENT_TYPES.PIPELINE_PAUSED, {
    reason,
    requestedBy,
  });
  const { state } = materializeState(feature, cwd);
  refreshMemory(feature, cwd);
  return state as PipelineExecutionState;
}

// ── getReadyArtifacts ──────────────────────────────────────────

export function getReadyArtifacts(
  feature: string,
  { cwd = process.cwd(), dagPath }: { cwd?: string; dagPath?: string } = {},
): ReadyArtifact[] {
  ensureFeatureName(feature);
  const execution = readExecutionView(cwd, feature);
  const { dag } = loadDagForFeature(cwd, feature, dagPath);
  const context = {
    cwd,
    feature,
    execution,
    dag,
    completedArtifacts: collectCompletedArtifacts(execution),
  };
  return resolveReadyArtifacts(context);
}

// ── registerPlugins ────────────────────────────────────────────

export function registerPlugins(
  feature: string,
  { cwd = process.cwd(), type }: { cwd?: string; type?: string } = {},
): ReturnType<typeof registerPluginsRuntime> {
  ensureFeatureName(feature);
  return registerPluginsRuntime(feature, { cwd, type });
}

// ── Tech Stack Cache ───────────────────────────────────────────

export function cacheTechStack(
  feature: string,
  techStack: Record<string, unknown>,
  { cwd = process.cwd() }: { cwd?: string } = {},
): void {
  ensureFeatureName(feature);
  const metaDir = path.join(cwd, '.boss', feature, '.meta');
  ensureDir(metaDir);
  writeJson(path.join(metaDir, 'tech-stack.json'), techStack);
}

export function readCachedTechStack(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): Record<string, unknown> | null {
  ensureFeatureName(feature);
  const filePath = path.join(cwd, '.boss', feature, '.meta', 'tech-stack.json');
  if (!fs.existsSync(filePath)) return null;
  return readJson<Record<string, unknown>>(filePath);
}

// ── Stall Detection ────────────────────────────────────────────

const DEFAULT_MAX_DURATION_MS = 30 * 60 * 1000; // 30 minutes

export function checkStall(
  feature: string,
  {
    cwd = process.cwd(),
    maxDurationMs = DEFAULT_MAX_DURATION_MS,
    autoFail = false,
  }: { cwd?: string; maxDurationMs?: number; autoFail?: boolean } = {},
): CheckStallResult {
  ensureFeatureName(feature);
  const execution = readExecutionView(cwd, feature);
  const now = Date.now();
  const stalled: StalledAgent[] = [];

  for (const [stageKey, stage] of Object.entries(execution.stages || {})) {
    if (!stage || !stage.agents) continue;
    for (const [agentName, agentState] of Object.entries(stage.agents)) {
      if (!agentState || agentState.status !== 'running' || !agentState.startTime) continue;
      const elapsed = now - new Date(agentState.startTime).getTime();
      if (elapsed > maxDurationMs) {
        const entry: StalledAgent = {
          agent: agentName,
          stage: Number(stageKey),
          startTime: agentState.startTime,
          elapsedMs: elapsed,
        };
        if (autoFail) {
          appendRuntimeEvent(cwd, feature, EVENT_TYPES.AGENT_FAILED, {
            agent: agentName,
            stage: Number(stageKey),
            reason: 'timeout',
          });
          entry.failed = true;
        }
        stalled.push(entry);
      }
    }
  }

  if (autoFail && stalled.length > 0) {
    materializeState(feature, cwd);
  }

  return { stalled };
}
