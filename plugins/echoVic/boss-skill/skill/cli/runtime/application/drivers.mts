export type BossDriverName = 'claude-code' | 'codex' | 'generic';

export interface BossDriverCapabilities {
  name: BossDriverName;
  hooks: boolean;
  checkpointPrompt: boolean;
  stopGuards: boolean;
  subagents: boolean;
}

export function normalizeDriverName(value: string | undefined): BossDriverName {
  if (value === 'claude-code' || value === 'codex' || value === 'generic') {
    return value;
  }
  return 'generic';
}

export function resolveDriverCapabilities(value: string | undefined): BossDriverCapabilities {
  const name = normalizeDriverName(value);
  if (name === 'claude-code') {
    return {
      name,
      hooks: true,
      checkpointPrompt: false,
      stopGuards: true,
      subagents: true,
    };
  }

  return {
    name,
    hooks: false,
    checkpointPrompt: true,
    stopGuards: false,
    subagents: false,
  };
}
