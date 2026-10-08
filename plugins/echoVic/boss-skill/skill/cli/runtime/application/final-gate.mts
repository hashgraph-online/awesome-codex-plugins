import {
  type ActiveAgentSummary,
  type FailureSummary,
  inspectPipeline,
  readExecution,
} from './inspection.mts';
import { type QaFinding, runQaAttack } from './qa-attack.mts';

const REQUIRED_ARTIFACTS = ['prd.md', 'architecture.md', 'tasks.md', 'qa-report.md'] as const;

export type FinalGateCheck =
  | {
      name: 'required-artifacts';
      passed: boolean;
      required: string[];
      recorded: string[];
      missing: string[];
    }
  | {
      name: 'no-active-agents';
      passed: boolean;
      activeAgents: ActiveAgentSummary[];
    }
  | {
      name: 'no-recent-failures';
      passed: boolean;
      recentFailures: FailureSummary[];
    }
  | {
      name: 'qa-attack-findings';
      passed: boolean;
      findings: QaFinding[];
    }
  | {
      name: 'no-failed-gates';
      passed: boolean;
      failedGates: FailedGate[];
    };

export interface FailedGate {
  gate: string;
  stage: string;
  executedAt: string;
}

export interface FinalGateResult {
  feature: string;
  passed: boolean;
  checks: FinalGateCheck[];
}

function collectRecordedArtifacts(feature: string, cwd: string): string[] {
  const execution = readExecution(feature, cwd);
  const recorded = new Set<string>();
  for (const stage of Object.values(execution.stages ?? {})) {
    for (const artifact of stage?.artifacts ?? []) {
      if (artifact) recorded.add(artifact);
    }
  }
  return [...recorded].sort();
}

/**
 * 找出「阶段已完成，但它的门禁最近一次评估未通过」的矛盾。
 *
 * 阶段推进没有门禁前置条件：`validateStageTransition` 是纯状态表，`running:completed`
 * 无条件合法，而门禁结果经同一次调用的可选参数在阶段完成事件之后追加。于是状态里可以
 * 同时存在「门禁未通过」与「阶段已完成」。这里不改变写入是否被允许，只保证矛盾会被看见。
 *
 * 以每个门禁的最新一次评估为准：返工后重跑并通过，矛盾即解除。
 */
export function findFailedGates(feature: string, cwd = process.cwd()): FailedGate[] {
  const execution = readExecution(feature, cwd);
  const failed: FailedGate[] = [];
  for (const [stageId, stage] of Object.entries(execution.stages ?? {})) {
    if (stage?.status !== 'completed') continue;
    for (const [gate, result] of Object.entries(stage.gateResults ?? {})) {
      const latest = execution.qualityGates?.[gate];
      // 以 qualityGates 里的最新评估为准；缺失时回退到该阶段记录的这一次
      const passed = latest ? latest.passed : result.passed;
      if (passed === false) {
        failed.push({
          gate,
          stage: stageId,
          executedAt: String(latest?.executedAt ?? result.executedAt ?? ''),
        });
      }
    }
  }
  return failed.sort((left, right) => left.gate.localeCompare(right.gate));
}

export function evaluateFinalGate(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): FinalGateResult {
  const recorded = collectRecordedArtifacts(feature, cwd);
  const failedGates = findFailedGates(feature, cwd);
  const missing = REQUIRED_ARTIFACTS.filter((artifact) => !recorded.includes(artifact));
  const inspection = inspectPipeline(feature, { cwd });
  const qaAttack = runQaAttack(feature, { cwd });

  const checks: FinalGateCheck[] = [
    {
      name: 'required-artifacts',
      passed: missing.length === 0,
      required: [...REQUIRED_ARTIFACTS],
      recorded,
      missing,
    },
    {
      name: 'no-active-agents',
      passed: inspection.activeAgents.length === 0,
      activeAgents: inspection.activeAgents,
    },
    {
      name: 'no-recent-failures',
      passed: inspection.recentFailures.length === 0,
      recentFailures: inspection.recentFailures,
    },
    {
      name: 'qa-attack-findings',
      passed: qaAttack.findings.filter((finding) => finding.status === 'open').length === 0,
      findings: qaAttack.findings,
    },
    {
      name: 'no-failed-gates',
      passed: failedGates.length === 0,
      failedGates,
    },
  ];

  return {
    feature,
    passed: checks.every((check) => check.passed),
    checks,
  };
}
