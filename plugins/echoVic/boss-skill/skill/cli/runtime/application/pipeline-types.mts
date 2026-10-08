/**
 * Pipeline types — shared interfaces used across pipeline modules.
 */

export interface ReadyArtifact {
  artifact: string;
  agent: string | string[];
  stage: number | undefined;
}

export interface ArtifactStatus {
  status: 'completed' | 'skipped' | 'ready' | 'blocked';
  missing?: string[];
}

export interface RuntimeHashDescriptor {
  algorithm: 'sha256';
  value: string;
}

export interface ArtifactDagFingerprint {
  path: string;
  version: string;
  hash: RuntimeHashDescriptor;
}

export interface AgentReuseInput {
  prompt?: string;
  promptFingerprint?: string;
  dependencyArtifacts?: string[];
  opts?: Record<string, unknown>;
}

export interface AgentReuseDecision {
  reusable: boolean;
  reason: string;
  dagStale: boolean;
  packStale: boolean;
  promptFingerprint: RuntimeHashDescriptor;
  inputDigest: RuntimeHashDescriptor;
  completedEventId?: number;
}

export interface StalledAgent {
  agent: string;
  stage: number;
  startTime: string;
  elapsedMs: number;
  failed?: boolean;
}

export interface CheckStallResult {
  stalled: StalledAgent[];
}

export const FORMAL_SOURCE_OF_TRUTH_ARTIFACTS = Object.freeze([
  'prd.md',
  'architecture.md',
  'ui-spec.md',
  'ui-design.json',
  'tech-review.md',
  'tasks.md',
] as const);

export function isFormalSourceOfTruthArtifact(artifact: string): boolean {
  return FORMAL_SOURCE_OF_TRUTH_ARTIFACTS.includes(
    artifact as (typeof FORMAL_SOURCE_OF_TRUTH_ARTIFACTS)[number],
  );
}

export { OPT_IN_OPTIONAL_ARTIFACTS } from '../domain/scheduling.mts';
