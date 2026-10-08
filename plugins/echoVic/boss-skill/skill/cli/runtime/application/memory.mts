import * as fs from 'node:fs';
import * as path from 'node:path';
import { readJsonlTolerant } from '../../infrastructure/fs.mts';
import { extractFeatureMemories } from '../memory/extractor.mts';
import { extractPreferenceMemories } from '../memory/preferences.mts';
import { queryAgentMemories } from '../memory/query.mts';
import type { MemorySummaryEntry } from '../memory/store.mts';
import {
  type FeatureMemoryPayload,
  type FeatureMemorySummary,
  type GlobalMemorySummary,
  type PersistedMemoryRecord,
  paths,
  replaceFeatureMemory,
  saveFeatureMemory,
  saveFeatureSummary,
  saveGlobalMemory,
  saveGlobalSummary,
} from '../memory/store.mts';
import {
  buildAgentSections,
  buildConversationSummary,
  buildStartupSummary,
} from '../memory/summarizer.mts';
import type { ExecutionState, RuntimeEvent } from '../projectors/materialize-state.mts';

function readJson<T>(filePath: string, fallback: T): T {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
}

function readExecution(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): ExecutionState | null {
  const filePath = paths
    .featureMemoryPath(cwd, feature)
    .replace('feature-memory.json', 'execution.json');
  return readJson<ExecutionState | null>(filePath, null);
}

function readEvents(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): RuntimeEvent[] {
  const filePath = paths
    .featureMemoryPath(cwd, feature)
    .replace('feature-memory.json', 'events.jsonl');
  if (!fs.existsSync(filePath)) {
    return [];
  }

  return readJsonlTolerant<RuntimeEvent>(filePath).records;
}

export function readFeatureMemory(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): FeatureMemoryPayload {
  const filePath = paths.featureMemoryPath(cwd, feature);
  return readJson(filePath, { feature, records: [] });
}

export function readFeatureSummary(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): FeatureMemorySummary {
  const filePath = paths.featureSummaryPath(cwd, feature);
  return readJson(filePath, {
    feature,
    generatedAt: null,
    startupSummary: [],
    agentSections: {},
  });
}

export function readGlobalMemory({ cwd = process.cwd() }: { cwd?: string } = {}): {
  records: PersistedMemoryRecord[];
} {
  return readJson(paths.globalMemoryPath(cwd), { records: [] });
}

export function writeFeatureMemory(
  feature: string,
  records: PersistedMemoryRecord[],
  { cwd = process.cwd() }: { cwd?: string } = {},
): FeatureMemoryPayload {
  return saveFeatureMemory(feature, records, { cwd });
}

export function rebuildFeatureMemory(
  feature: string,
  { cwd = process.cwd(), now = new Date().toISOString() }: { cwd?: string; now?: string } = {},
): FeatureMemoryPayload {
  const execution = readExecution(feature, { cwd }) ?? { parameters: {}, stages: {} };
  const events = readEvents(feature, { cwd });
  const records = [
    ...extractFeatureMemories({ feature, execution, events, now }),
    // 用户选择偏好：对事件流做确定性 fold，与其余 memory 记录同源、可重放
    ...extractPreferenceMemories(feature, events),
  ];
  // 全量替换而非 merge：这是一次完整重放，结果必须直接覆盖旧投影
  return replaceFeatureMemory(feature, records, { cwd });
}

export function buildFeatureSummary(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): FeatureMemorySummary {
  const payload = readFeatureMemory(feature, { cwd });
  const globalPayload = readGlobalMemory({ cwd });
  const execution = readExecution(feature, { cwd }) ?? ({ stages: {} } as ExecutionState);
  const agents: Array<{ name: string; stage: number }> = [];

  for (const [stageId, stage] of Object.entries(execution.stages ?? {})) {
    for (const agentName of Object.keys(stage.agents ?? {})) {
      agents.push({ name: agentName, stage: Number(stageId) });
    }
  }

  const combined = [...(payload.records ?? []), ...(globalPayload.records ?? [])];
  const summary: FeatureMemorySummary = {
    feature,
    generatedAt: new Date().toISOString(),
    startupSummary: buildStartupSummary(combined),
    agentSections: {
      ...buildAgentSections(combined, agents),
      conversation: buildConversationSummary(combined),
    },
    conversationSummary: buildConversationSummary(combined),
  };

  saveFeatureSummary(feature, summary, { cwd });
  return summary;
}

export function rebuildGlobalMemory({ cwd = process.cwd() }: { cwd?: string } = {}): {
  records: PersistedMemoryRecord[];
} {
  const bossRoot = path.join(cwd, '.boss');
  const features = fs.existsSync(bossRoot)
    ? fs
        .readdirSync(bossRoot)
        .filter(
          (name: string) =>
            !name.startsWith('.') && fs.existsSync(paths.featureMemoryPath(cwd, name)),
        )
    : [];

  const grouped = new Map<string, PersistedMemoryRecord[]>();
  for (const feature of features) {
    const payload = readFeatureMemory(feature, { cwd });
    for (const record of payload.records ?? []) {
      const key = [
        record.category,
        record.stage ?? '',
        record.agent ?? '',
        ...(record.tags ?? []),
      ].join(':');
      const bucket = grouped.get(key) ?? [];
      bucket.push(record);
      grouped.set(key, bucket);
    }
  }

  const promoted: PersistedMemoryRecord[] = [];
  for (const [key, bucket] of grouped.entries()) {
    if (bucket.length < 2) {
      continue;
    }
    const latest = bucket[bucket.length - 1] as PersistedMemoryRecord;
    promoted.push({
      ...latest,
      id: `global-${key}`,
      scope: 'global',
      feature: null,
      summary: latest.summary,
    });
  }

  const memory = saveGlobalMemory(promoted, { cwd });
  const summary: GlobalMemorySummary = {
    generatedAt: new Date().toISOString(),
    startupSummary: buildStartupSummary(memory.records ?? []),
    agentSections: {},
  };
  saveGlobalSummary(summary, { cwd });
  return memory;
}

export function queryAgentSection(
  feature: string,
  {
    cwd = process.cwd(),
    agent,
    stage,
    limit = 3,
  }: {
    cwd?: string;
    agent?: string;
    stage?: number;
    limit?: number;
  } = {},
): MemorySummaryEntry[] {
  const summary = readFeatureSummary(feature, { cwd });
  const summarySection =
    summary.agentSections && agent && summary.agentSections[agent]
      ? summary.agentSections[agent]
      : [];
  if (summarySection.length > 0) {
    return summarySection.slice(0, limit);
  }

  const payload = readFeatureMemory(feature, { cwd });
  const globalPayload = readGlobalMemory({ cwd });
  return queryAgentMemories([...(payload.records ?? []), ...(globalPayload.records ?? [])], {
    agent,
    stage,
    limit,
  }).map((record) => ({
    category: record.category,
    summary: record.summary,
    scope: record.scope,
  }));
}
