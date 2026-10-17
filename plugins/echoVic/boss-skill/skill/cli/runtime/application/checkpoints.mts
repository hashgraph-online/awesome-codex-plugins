import { artifactLayer, findStaleRunArtifacts, type StaleRunArtifact } from './artifact-layers.mts';
import { type BossDriverCapabilities, resolveDriverCapabilities } from './drivers.mts';
import { type CurrentStageSummary, inspectPipeline, readExecution } from './inspection.mts';
import { type EvidenceWave, readWaves } from './waves.mts';
import { listWipCheckpoints, type WipCheckpointListItem } from './wip-checkpoint.mts';

export interface RequiredCheck {
  id: string;
  command: string;
  required: boolean;
}

export interface BossCheckpoint {
  checkpointRequired: boolean;
  reason: string;
  changedFiles: string[];
  requiredChecks: RequiredCheck[];
  continueCommand: string;
  wipCheckpoints: WipCheckpointListItem[];
}

export interface ArtifactLayerGroups {
  product: string[];
  run: string[];
  derived: string[];
}

export interface BossStatus {
  feature: string;
  status: string;
  driver: BossDriverCapabilities;
  capabilities: Omit<BossDriverCapabilities, 'name'>;
  currentStage: CurrentStageSummary | null;
  currentWave: EvidenceWave | null;
  readyArtifacts: string[];
  blockedReason: string | null;
  /** 已记录产物按生命周期分组：产品资产 / 本轮记录 / 派生视图。 */
  artifactLayers: ArtifactLayerGroups;
  /** 上游产品资产已重做、因而不再对应当前状态的本轮记录。 */
  staleRunArtifacts: StaleRunArtifact[];
  checkpoint: BossCheckpoint;
}

function defaultRequiredChecks(stage: CurrentStageSummary | null): RequiredCheck[] {
  if (!stage || stage.id < 3) {
    return [];
  }

  return [
    { id: 'typecheck', command: 'npm run typecheck', required: true },
    { id: 'tests', command: 'npm test', required: true },
  ];
}

export function buildBossStatus(
  feature: string,
  { cwd = process.cwd(), driver = 'generic' }: { cwd?: string; driver?: string } = {},
): BossStatus {
  const inspection = inspectPipeline(feature, { cwd });
  const driverCapabilities = resolveDriverCapabilities(driver);
  const requiredChecks = defaultRequiredChecks(inspection.currentStage);
  const blockedReason = inspection.recentFailures[0]?.reason || null;
  // 全部阶段完成之后已经没有「下一步」可确认；此前只看 stage.id >= 3，于是收尾之后
  // 仍打印 CHECKPOINT_REQUIRED 并提示 `boss continue`，把用户指向一个空操作。
  const pipelineComplete = inspection.status === 'completed';
  const checkpointRequired =
    !pipelineComplete && (requiredChecks.length > 0 || blockedReason !== null);
  const currentWave =
    readWaves(feature, { cwd }).find((wave) => wave.status !== 'completed') ?? null;
  const wipCheckpoints = listWipCheckpoints(feature, { cwd });

  const artifactLayers: ArtifactLayerGroups = { product: [], run: [], derived: [] };
  const execution = readExecution(feature, cwd);
  for (const stage of Object.values(execution.stages ?? {})) {
    for (const artifact of stage?.artifacts ?? []) {
      const group = artifactLayers[artifactLayer(artifact)];
      if (!group.includes(artifact)) group.push(artifact);
    }
  }
  for (const group of Object.values(artifactLayers)) group.sort();

  return {
    feature,
    status: inspection.status,
    driver: driverCapabilities,
    capabilities: {
      hooks: driverCapabilities.hooks,
      checkpointPrompt: driverCapabilities.checkpointPrompt,
      stopGuards: driverCapabilities.stopGuards,
      subagents: driverCapabilities.subagents,
    },
    currentStage: inspection.currentStage,
    currentWave,
    readyArtifacts: inspection.readyArtifacts,
    blockedReason,
    artifactLayers,
    staleRunArtifacts: findStaleRunArtifacts(feature, { cwd }),
    checkpoint: {
      checkpointRequired,
      reason: checkpointRequired
        ? 'next-action-requires-explicit-confirmation'
        : pipelineComplete
          ? 'pipeline-complete'
          : 'next-action-ready',
      changedFiles: [],
      requiredChecks,
      // 已完成的流水线没有下一步可继续；给出命令会把用户指向一个空操作
      continueCommand: pipelineComplete ? '' : `boss continue ${feature}`,
      wipCheckpoints,
    },
  };
}
