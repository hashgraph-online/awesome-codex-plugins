import type { MemoryQueryRecord } from './store.mts';

export interface MemoryQueryOptions {
  agent?: string;
  stage?: number;
  limit?: number;
}

function score(
  record: MemoryQueryRecord,
  target: Pick<MemoryQueryOptions, 'agent' | 'stage'>,
): number {
  let value = (record.decayScore ?? 0) * 100 + (record.confidence ?? 0) * 10;
  if (record.category && record.category.startsWith('conversation_')) {
    value += 50;
  }
  if (record.agent && record.agent === target.agent) {
    value += 1000;
  }
  if (record.stage && record.stage === target.stage) {
    value += 100;
  }
  return value;
}

export function queryAgentMemories(
  records: MemoryQueryRecord[],
  { agent, stage, limit = 3 }: MemoryQueryOptions = {},
): MemoryQueryRecord[] {
  return records
    .filter((record) => {
      if (record.stage != null && stage != null && record.stage !== stage) {
        return false;
      }
      if (record.agent && record.agent !== agent) {
        return false;
      }
      return true;
    })
    .sort((left, right) => score(right, { agent, stage }) - score(left, { agent, stage }))
    .slice(0, limit);
}
