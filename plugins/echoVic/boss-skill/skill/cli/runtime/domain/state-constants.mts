export const PIPELINE_STATUS = Object.freeze({
  INITIALIZED: 'initialized',
  RUNNING: 'running',
  PAUSED: 'paused',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const);

export const STAGE_STATUS = Object.freeze({
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  RETRYING: 'retrying',
  SKIPPED: 'skipped',
} as const);

export const AGENT_STATUS = Object.freeze({
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const);

export type PipelineStatus = (typeof PIPELINE_STATUS)[keyof typeof PIPELINE_STATUS];
export type StageStatus = (typeof STAGE_STATUS)[keyof typeof STAGE_STATUS];
export type AgentStatus = (typeof AGENT_STATUS)[keyof typeof AGENT_STATUS];

export const DEFAULT_SCHEMA_VERSION = '0.2.0';
