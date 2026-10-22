/**
 * Pipeline agent reuse — builds fingerprints and evaluates whether
 * an agent can reuse its prior completed run.
 */
import * as fs from 'node:fs';
import * as path from 'node:path';
import { EVENT_TYPES } from '../domain/event-types.mts';
import { resolvePipelinePack } from './packs.mts';
import {
  hashFile,
  hashRuntimeValue,
  isArtifactDagStale,
  readRuntimeEvents,
  sha256Hex,
} from './pipeline-dag.mts';
import type { AgentReuseDecision, AgentReuseInput } from './pipeline-types.mts';
import { ensureFeatureName, readExecutionView } from './state.mts';
import { hashPipelinePack } from './workflow.mts';

/**
 * pipeline pack 是否已与初始化时不同。
 *
 * 与 `isArtifactDagStale` 对称：初始化时 pack 的指纹写进 `execution.parameters.packHash`，
 * 这里重算当前 pack 的指纹并比对。此前这个字段被记录、被文档描述，却没有任何一处读它做判断，
 * 于是改掉 pack 的 stages / agents / gates 之后恢复，仍会复用按旧流水线产出的 agent 产物。
 * 取不到当前 pack 时按「已漂移」处理：宁可重跑，不可拿不确定的前提复用。
 */
export function isPipelinePackStale(
  cwd: string,
  execution = {} as { parameters?: Record<string, unknown> },
): boolean {
  const recorded = execution.parameters?.packHash;
  if (typeof recorded !== 'string' || recorded.length === 0) return false;
  try {
    return hashPipelinePack(resolvePipelinePack(cwd)).value !== recorded;
  } catch {
    return true;
  }
}

function readArtifactDigest(
  cwd: string,
  feature: string,
  artifact: string,
): ReturnType<typeof hashFile> | null {
  const artifactPath = path.join(cwd, '.boss', feature, artifact);
  if (!fs.existsSync(artifactPath) || !fs.statSync(artifactPath).isFile()) return null;
  return hashFile(artifactPath);
}

export function buildAgentFingerprints(
  feature: string,
  agent: string,
  stage: number,
  {
    cwd,
    prompt,
    promptFingerprint,
    dependencyArtifacts = [],
    opts = {},
  }: AgentReuseInput & { cwd: string },
): {
  promptFingerprint: ReturnType<typeof hashRuntimeValue>;
  inputDigest: ReturnType<typeof hashRuntimeValue>;
} {
  const promptHash = {
    algorithm: 'sha256' as const,
    value: promptFingerprint || sha256Hex(prompt || ''),
  };
  const dependencies = dependencyArtifacts
    .slice()
    .sort()
    .map((artifact) => ({
      artifact,
      hash: readArtifactDigest(cwd, feature, artifact),
    }));
  const inputDigest = hashRuntimeValue({
    agent,
    stage,
    promptFingerprint: promptHash,
    opts,
    dependencies,
  });
  return { promptFingerprint: promptHash, inputDigest };
}

export function evaluateAgentReuse(
  feature: string,
  stage: number | string,
  agent: string,
  {
    cwd = process.cwd(),
    prompt,
    promptFingerprint,
    dependencyArtifacts = [],
    opts = {},
  }: AgentReuseInput & { cwd?: string } = {},
): AgentReuseDecision {
  ensureFeatureName(feature);
  const stageNumber = Number(stage);
  if (!Number.isInteger(stageNumber)) {
    throw new Error('stage 必须是整数');
  }
  if (stageNumber < 1 || stageNumber > 4) {
    throw new Error('stage 必须是 1-4');
  }
  const execution = readExecutionView(cwd, feature);
  const dagStale = isArtifactDagStale(cwd, feature, execution);
  const packStale = isPipelinePackStale(cwd, execution);
  const fingerprints = buildAgentFingerprints(feature, agent, stageNumber, {
    cwd,
    prompt,
    promptFingerprint,
    dependencyArtifacts,
    opts,
  });

  const completed = readRuntimeEvents(cwd, feature)
    .slice()
    .reverse()
    .find(
      (event) =>
        event.type === EVENT_TYPES.AGENT_COMPLETED &&
        event.data.agent === agent &&
        Number(event.data.stage) === stageNumber,
    );

  if (!completed) {
    return {
      reusable: false,
      reason: 'no-completed-agent-event',
      dagStale,
      packStale,
      ...fingerprints,
    };
  }

  if (completed.data.promptFingerprint !== fingerprints.promptFingerprint.value) {
    return {
      reusable: false,
      reason: 'prompt-fingerprint-changed',
      dagStale,
      packStale,
      completedEventId: completed.id,
      ...fingerprints,
    };
  }

  if (completed.data.inputDigest !== fingerprints.inputDigest.value) {
    return {
      reusable: false,
      reason: 'input-digest-changed',
      dagStale,
      packStale,
      completedEventId: completed.id,
      ...fingerprints,
    };
  }

  return {
    reusable: !dagStale && !packStale,
    reason: dagStale
      ? 'artifact-dag-stale'
      : packStale
        ? 'pipeline-pack-stale'
        : 'input-digest-matched',
    dagStale,
    packStale,
    completedEventId: completed.id,
    ...fingerprints,
  };
}
