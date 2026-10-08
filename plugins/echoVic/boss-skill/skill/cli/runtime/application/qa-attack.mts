import * as fs from 'node:fs';
import * as path from 'node:path';

import { readExecution } from './inspection.mts';

export type QaFindingSeverity = 'critical' | 'high' | 'medium' | 'low';
export type QaFindingStatus = 'open' | 'closed' | 'accepted';

export interface QaFinding {
  id: string;
  severity: QaFindingSeverity;
  status: QaFindingStatus;
  evidence: string;
}

export interface QaAttackResult {
  feature: string;
  status: 'passed' | 'failed';
  findings: QaFinding[];
}

const REQUIRED_QA_EVIDENCE_GROUPS = [
  {
    id: 'verification',
    label: 'verification evidence',
    headings: [/Verification/i, /自动化测试结果/, /测试工具与方法/],
  },
  {
    id: 'evidence',
    label: 'evidence summary',
    headings: [/Evidence(?:\s+Summary)?/i],
  },
  {
    id: 'findings',
    label: 'findings or bug summary',
    headings: [/Findings/i, /发现的\s*Bug/i, /Bug\s*汇总/i, /失败用例详情/],
  },
  {
    id: 'attack-checks',
    label: 'QA attack checks',
    headings: [/QA\s+Attack\s+Checks/i],
  },
] as const;

function recordedArtifacts(feature: string, cwd: string): Set<string> {
  const execution = readExecution(feature, cwd);
  const artifacts = new Set<string>();
  for (const stage of Object.values(execution.stages ?? {})) {
    for (const artifact of stage?.artifacts ?? []) {
      if (artifact) artifacts.add(artifact);
    }
  }
  return artifacts;
}

function hasMarkdownHeading(report: string, heading: RegExp): boolean {
  return report.split('\n').some((line) => {
    const match = line.match(/^#{1,6}\s+(?:\d+(?:\.\d+)*\.?\s+)?(.+)$/);
    return Boolean(match?.[1] && heading.test(match[1]));
  });
}

function containsOpenCriticalFinding(report: string): boolean {
  return report.split('\n').some((line) => {
    if (!/\bcritical\b/i.test(line)) return false;
    return /\bopen\b/i.test(line) || /\[[ -]\]/.test(line);
  });
}

export function runQaAttack(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): QaAttackResult {
  const findings: QaFinding[] = [];
  const artifacts = recordedArtifacts(feature, cwd);
  const reportPath = path.join(cwd, '.boss', feature, 'qa-report.md');

  if (!artifacts.has('qa-report.md') || !fs.existsSync(reportPath)) {
    findings.push({
      id: 'qa-report-missing',
      severity: 'critical',
      status: 'open',
      evidence:
        'qa-report.md is not recorded in execution state or is missing from .boss/<feature>/',
    });
  } else {
    const report = fs.readFileSync(reportPath, 'utf8');
    for (const group of REQUIRED_QA_EVIDENCE_GROUPS) {
      if (!group.headings.some((heading) => hasMarkdownHeading(report, heading))) {
        findings.push({
          id: `qa-report-${group.id}-missing`,
          severity: 'high',
          status: 'open',
          evidence: `qa-report.md is missing ${group.label}`,
        });
      }
    }

    if (containsOpenCriticalFinding(report)) {
      findings.push({
        id: 'qa-report-open-critical',
        severity: 'critical',
        status: 'open',
        evidence: 'qa-report.md contains an open critical finding',
      });
    }
  }

  return {
    feature,
    status: findings.some((finding) => finding.status === 'open') ? 'failed' : 'passed',
    findings,
  };
}
