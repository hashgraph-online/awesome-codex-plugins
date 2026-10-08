import { createHash } from 'node:crypto';
import * as path from 'node:path';

import { EVENT_TYPES } from '../domain/event-types.mts';
import { computeNextNodeIds } from '../domain/scheduling.mts';
import { materializeState } from '../projectors/materialize-state.mts';
import type { PipelinePackDefinition } from './packs.mts';
import type { RuntimeHashDescriptor } from './pipeline.mts';
import { evaluateAgentReuse } from './pipeline.mts';
import { stableStringify } from './pipeline-dag.mts';
import type { ArtifactDag } from './state.mts';
import {
  appendRuntimeEvent,
  ensureFeatureName,
  readExecutionView,
  readJson,
  writeJson,
} from './state.mts';

export type WorkflowNodeKind = 'input' | 'agent' | 'gate';
export type WorkflowResumeDecision = 'reuse' | 'run' | 'skip';
export type WorkflowNodeExecutionStatus =
  | 'pending'
  | 'ready'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped'
  | 'reused'
  | 'blocked';

export interface WorkflowPlanNode {
  id: string;
  kind: WorkflowNodeKind;
  artifact?: string;
  gate?: string;
  agent?: string | string[] | null;
  stage: number;
  phase: string;
  inputs: string[];
  /** 该节点写入的路径集合；用于并行安全组分组。缺省回退到 artifact 名。 */
  writes?: string[];
  optional: boolean;
  parallelGroup?: string;
  description?: string;
}

export interface WorkflowPlanPhase {
  id: string;
  stage: number;
  name: string;
  nodeIds: string[];
}

export interface WorkflowPlan {
  schemaVersion: '1.0.0';
  feature: string;
  source: {
    pack: {
      name: string;
      version: string;
      hash: RuntimeHashDescriptor;
    };
    artifactDag: {
      path: string;
      version: string;
      hash: RuntimeHashDescriptor;
    };
  };
  phases: WorkflowPlanPhase[];
  nodes: WorkflowPlanNode[];
  validation: {
    deterministic: boolean;
    errors: string[];
  };
}

export interface WorkflowExecutionNode {
  id: string;
  kind: WorkflowNodeKind | 'wave';
  artifact?: string;
  gate?: string;
  agent?: string | string[] | null;
  stage: number;
  phase: string;
  inputs: string[];
  /** 该节点写入的路径集合；用于并行安全组分组。缺省回退到 artifact 名。 */
  writes?: string[];
  optional: boolean;
  status: WorkflowNodeExecutionStatus;
  decision?: WorkflowResumeDecision;
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

export interface WorkflowPlanPersistence {
  plan: WorkflowPlan;
  workflowHash: RuntimeHashDescriptor;
  workflowPlanPath: string;
  packHash: RuntimeHashDescriptor;
  artifactDagHash: RuntimeHashDescriptor;
}

export interface ResumeWorkflowNodeDecision {
  id: string;
  kind: WorkflowNodeKind;
  artifact?: string;
  gate?: string;
  agent?: string;
  stage: number;
  decision: WorkflowResumeDecision;
  reason: string;
}

export interface ResumeWorkflowResult {
  feature: string;
  fromRunId: string;
  runId: string;
  workflowPlanPath: string;
  workflowHash: string;
  nodes: ResumeWorkflowNodeDecision[];
  nextNodeIds: string[];
}

function sha256Hex(value: string | Buffer): string {
  return createHash('sha256').update(value).digest('hex');
}

/**
 * pipeline pack 的指纹。编译计划与检测 pack 漂移必须调用同一个函数：
 * 若两处各自内联字段列表，其中一处漏掉一个字段，漂移检查就会对该字段的变化视而不见。
 */
export function hashPipelinePack(pack: PipelinePackDefinition): RuntimeHashDescriptor {
  return hashWorkflowValue({
    name: pack.name,
    version: pack.version,
    type: pack.type,
    priority: pack.priority,
    config: pack.config,
  });
}

export function hashWorkflowValue(value: unknown): RuntimeHashDescriptor {
  return {
    algorithm: 'sha256',
    value: sha256Hex(stableStringify(value)),
  };
}

function phaseName(stage: number): string {
  switch (stage) {
    case 0:
      return 'intake';
    case 1:
      return 'planning';
    case 2:
      return 'review';
    case 3:
      return 'development';
    case 4:
      return 'deployment';
    default:
      return `stage-${stage}`;
  }
}

function normalizeStage(value: unknown): number {
  const stage = Number(value ?? 0);
  if (!Number.isInteger(stage) || stage < 0) {
    throw new Error(`workflow plan stage must be a non-negative integer: ${JSON.stringify(value)}`);
  }
  return stage;
}

function normalizeInputs(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string' && item.length > 0);
}

function includesDynamicScript(script: string): string | null {
  const banned = ['Date.now', 'new Date', 'Math.random', '$(', '`'];
  return banned.find((pattern) => script.includes(pattern)) ?? null;
}

function validateArtifactDag(artifactDag: ArtifactDag): void {
  const artifacts = artifactDag.artifacts || {};
  const names = new Set(Object.keys(artifacts));
  const errors: string[] = [];

  for (const [artifact, definition] of Object.entries(artifacts)) {
    const inputs = normalizeInputs(definition.inputs);
    for (const input of inputs) {
      if (!names.has(input)) {
        errors.push(`artifact ${artifact} references undeclared input ${input}`);
      }
    }

    if (typeof definition.script === 'string') {
      const dynamicPattern = includesDynamicScript(definition.script);
      if (dynamicPattern) {
        errors.push(`artifact ${artifact} uses non-deterministic script pattern ${dynamicPattern}`);
      }
    }

    if (
      definition.type !== 'gate' &&
      definition.agent == null &&
      normalizeStage(definition.stage) > 0
    ) {
      errors.push(`artifact ${artifact} has no agent or gate binding`);
    }
  }

  if (errors.length > 0) {
    throw new Error(`Invalid workflow plan: ${errors.join('; ')}`);
  }
}

function toWorkflowNode(
  artifact: string,
  definition: NonNullable<ArtifactDag['artifacts']>[string],
): WorkflowPlanNode {
  const stage = normalizeStage(definition.stage);
  const isGate = definition.type === 'gate' || artifact.startsWith('gate');
  const hasAgent = definition.agent != null;
  const phase = `stage-${stage}`;
  const node: WorkflowPlanNode = {
    id: isGate ? `gate:${artifact}` : `artifact:${artifact}`,
    kind: isGate ? 'gate' : hasAgent ? 'agent' : 'input',
    artifact,
    stage,
    phase,
    inputs: normalizeInputs(definition.inputs),
    writes: normalizeInputs(definition.writes),
    optional: definition.optional === true,
    description: definition.description,
  };

  if (isGate) {
    node.gate = artifact;
  } else {
    node.agent = definition.agent ?? null;
  }

  if (Array.isArray(definition.agent) && definition.agent.length > 1) {
    node.parallelGroup = `stage-${stage}-${artifact}`;
  }

  return node;
}

function sortNodes(left: WorkflowPlanNode, right: WorkflowPlanNode): number {
  if (left.stage !== right.stage) return left.stage - right.stage;
  return left.id.localeCompare(right.id);
}

export function compileWorkflowPlan({
  feature,
  pack,
  artifactDag,
  artifactDagFingerprint,
}: {
  feature: string;
  pack: PipelinePackDefinition;
  artifactDag: ArtifactDag;
  artifactDagFingerprint: { path: string; version: string; hash: RuntimeHashDescriptor };
}): WorkflowPlan {
  ensureFeatureName(feature);
  validateArtifactDag(artifactDag);

  const nodes = Object.entries(artifactDag.artifacts || {})
    .map(([artifact, definition]) => toWorkflowNode(artifact, definition))
    .sort(sortNodes);

  const phases = [...new Set(nodes.map((node) => node.stage))]
    .sort((left, right) => left - right)
    .map((stage) => ({
      id: `stage-${stage}`,
      stage,
      name: phaseName(stage),
      nodeIds: nodes.filter((node) => node.stage === stage).map((node) => node.id),
    }));

  return {
    schemaVersion: '1.0.0',
    feature,
    source: {
      pack: {
        name: pack.name,
        version: pack.version,
        hash: hashPipelinePack(pack),
      },
      artifactDag: artifactDagFingerprint,
    },
    phases,
    nodes,
    validation: {
      deterministic: true,
      errors: [],
    },
  };
}

export function persistWorkflowPlan({
  cwd,
  feature,
  plan,
}: {
  cwd: string;
  feature: string;
  plan: WorkflowPlan;
}): WorkflowPlanPersistence {
  const relativePlanPath = `.boss/${feature}/.meta/workflow-plan.json`;
  const absolutePlanPath = path.join(cwd, relativePlanPath);
  const workflowHash = hashWorkflowValue(plan);
  writeJson(absolutePlanPath, plan);
  return {
    plan,
    workflowHash,
    workflowPlanPath: relativePlanPath,
    packHash: plan.source.pack.hash,
    artifactDagHash: plan.source.artifactDag.hash,
  };
}

function isSatisfiedStatus(status: string | undefined): boolean {
  return status === 'completed' || status === 'reused' || status === 'skipped';
}

function findNodeIdByArtifact(
  nodes: Record<string, WorkflowExecutionNode>,
  artifact: string,
): string | null {
  for (const node of Object.values(nodes)) {
    if (node.artifact === artifact) return node.id;
  }
  return null;
}

function nodeInputsSatisfied(
  node: WorkflowExecutionNode,
  nodes: Record<string, WorkflowExecutionNode>,
): boolean {
  for (const input of node.inputs) {
    const inputNodeId = findNodeIdByArtifact(nodes, input);
    if (!inputNodeId) continue;
    if (!isSatisfiedStatus(nodes[inputNodeId]?.status)) return false;
  }
  return true;
}

export function refreshWorkflowSchedule(workflow: WorkflowExecutionState): WorkflowExecutionState {
  const nodes = { ...workflow.nodes };
  for (const [id, node] of Object.entries(nodes)) {
    if (node.kind === 'input') {
      nodes[id] = { ...node, status: 'skipped', decision: node.decision ?? 'skip' };
      continue;
    }
    if (isSatisfiedStatus(node.status) || node.status === 'running' || node.status === 'failed') {
      continue;
    }
    nodes[id] = {
      ...node,
      status: nodeInputsSatisfied(node, nodes) ? 'ready' : 'blocked',
    };
  }

  // 按写集不重叠的并行安全组派发，不再按 stage 分批：
  // DAG 的 inputs 已表达数据依赖，stage 仅作优先级提示。
  const nextNodeIds = computeNextNodeIds(Object.values(nodes));

  return {
    ...workflow,
    nodes,
    nextNodeIds,
  };
}

export function createWorkflowExecutionState({
  plan,
  workflowPlanPath,
  workflowHash,
}: {
  plan: WorkflowPlan;
  workflowPlanPath: string;
  workflowHash: RuntimeHashDescriptor;
}): WorkflowExecutionState {
  const nodes = Object.fromEntries(
    plan.nodes.map((node) => [
      node.id,
      {
        ...node,
        status: node.kind === 'input' ? 'skipped' : 'pending',
        decision: node.kind === 'input' ? 'skip' : undefined,
        reason: node.kind === 'input' ? 'input-node' : undefined,
      } satisfies WorkflowExecutionNode,
    ]),
  );
  return refreshWorkflowSchedule({
    planPath: workflowPlanPath,
    hash: workflowHash.value,
    nodes,
    nextNodeIds: [],
  });
}

/**
 * 校验计划文件与它落盘时的 workflowHash 一致，返回当前哈希。
 *
 * 计划在 `persistWorkflowPlan` 时被哈希并把哈希记进 `execution.parameters`。恢复时若不
 * 复算比对，被改过的计划会被当作原计划继续调度：节点集合、依赖边、门禁都可能已经不同，
 * 而恢复结果看起来完全正常。这类错误不会报错，只会让后续每一步都建立在错误的依据上，
 * 所以这里选择拒绝恢复而非告警继续。
 *
 * 旧版本创建的 run 没有记录哈希，无从比对：放行，并以当前计划的哈希为准。
 */
function verifyWorkflowPlanIntegrity(
  plan: WorkflowPlan,
  persistedHash: string,
  workflowPlanPath: string,
): string {
  const currentHash = hashWorkflowValue(plan).value;
  if (!persistedHash) return currentHash;
  if (currentHash !== persistedHash) {
    throw new Error(
      [
        `workflow-plan.json 与落盘时的 workflowHash 不一致，拒绝恢复：${workflowPlanPath}`,
        `  落盘哈希：${persistedHash}`,
        `  当前哈希：${currentHash}`,
        '  计划文件可能被修改或损坏。恢复该文件，或重新初始化流水线后再试。',
      ].join('\n'),
    );
  }
  return currentHash;
}

function readWorkflowPlan(cwd: string, workflowPlanPath: string): WorkflowPlan {
  const absolutePath = path.isAbsolute(workflowPlanPath)
    ? workflowPlanPath
    : path.join(cwd, workflowPlanPath);
  return readJson<WorkflowPlan>(absolutePath);
}

function firstAgent(agent: string | string[] | null | undefined): string {
  return Array.isArray(agent) ? (agent[0] ?? '') : (agent ?? '');
}

function nodePrompt(node: WorkflowPlanNode): string {
  return `${firstAgent(node.agent)}:${node.artifact ?? node.id}`;
}

function resumeDecisionForNode(
  feature: string,
  node: WorkflowPlanNode,
  cwd: string,
): ResumeWorkflowNodeDecision {
  if (node.kind === 'input') {
    return {
      id: node.id,
      kind: node.kind,
      artifact: node.artifact,
      stage: node.stage,
      decision: 'skip',
      reason: 'input-node',
    };
  }

  if (node.kind === 'gate') {
    return {
      id: node.id,
      kind: node.kind,
      artifact: node.artifact,
      gate: node.gate,
      stage: node.stage,
      decision: 'run',
      reason: 'gate-evaluation-required',
    };
  }

  const agent = firstAgent(node.agent);
  if (!agent) {
    return {
      id: node.id,
      kind: node.kind,
      artifact: node.artifact,
      stage: node.stage,
      decision: 'run',
      reason: 'agent-missing',
    };
  }

  const reuse = evaluateAgentReuse(feature, node.stage, agent, {
    cwd,
    prompt: nodePrompt(node),
    dependencyArtifacts: node.inputs,
  });
  return {
    id: node.id,
    kind: node.kind,
    artifact: node.artifact,
    agent,
    stage: node.stage,
    decision: reuse.reusable ? 'reuse' : 'run',
    reason: reuse.reason,
  };
}

export function resumeWorkflow(
  feature: string,
  {
    cwd = process.cwd(),
    fromRunId,
  }: {
    cwd?: string;
    fromRunId: string;
  },
): ResumeWorkflowResult {
  ensureFeatureName(feature);
  if (!fromRunId) throw new Error('缺少 fromRunId 参数');
  const execution = readExecutionView(cwd, feature);
  const runId = typeof execution.parameters?.runId === 'string' ? execution.parameters.runId : '';
  if (fromRunId !== runId) {
    throw new Error(`fromRunId does not match active runId: ${fromRunId}`);
  }

  const workflowPlanPath =
    typeof execution.parameters?.workflowPlanPath === 'string'
      ? execution.parameters.workflowPlanPath
      : `.boss/${feature}/.meta/workflow-plan.json`;
  const persistedHash =
    typeof execution.parameters?.workflowHash === 'string' ? execution.parameters.workflowHash : '';
  const plan = readWorkflowPlan(cwd, workflowPlanPath);
  const workflowHash = verifyWorkflowPlanIntegrity(plan, persistedHash, workflowPlanPath);
  const nodes = plan.nodes.map((node) => resumeDecisionForNode(feature, node, cwd));
  const projectedWorkflow = refreshWorkflowSchedule({
    planPath: workflowPlanPath,
    hash: workflowHash,
    nodes: Object.fromEntries(
      plan.nodes.map((node) => [
        node.id,
        {
          ...node,
          status:
            nodes.find((decision) => decision.id === node.id)?.decision === 'reuse'
              ? 'reused'
              : nodes.find((decision) => decision.id === node.id)?.decision === 'skip'
                ? 'skipped'
                : 'pending',
          decision: nodes.find((decision) => decision.id === node.id)?.decision,
          reason: nodes.find((decision) => decision.id === node.id)?.reason,
        } satisfies WorkflowExecutionNode,
      ]),
    ),
    nextNodeIds: [],
  });

  appendRuntimeEvent(cwd, feature, EVENT_TYPES.PIPELINE_RESUMED, {
    fromRunId,
    runId,
    workflowPlanPath,
    workflowHash,
    reusedNodes: nodes.filter((node) => node.decision === 'reuse').length,
    runnableNodes: nodes.filter((node) => node.decision === 'run').length,
    nextNodeIds: projectedWorkflow.nextNodeIds,
    nodes,
  });
  materializeState(feature, cwd);

  return {
    feature,
    fromRunId,
    runId,
    workflowPlanPath,
    workflowHash,
    nodes,
    nextNodeIds: projectedWorkflow.nextNodeIds,
  };
}
