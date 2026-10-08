import * as fs from 'node:fs';
import * as path from 'node:path';
import { appendLineSync, readJsonlTolerant } from '../../infrastructure/fs.mts';
import { EVENT_TYPE_VALUES, type EventType } from '../domain/event-types.mts';
import type { ExecutionState, RuntimeEvent } from '../projectors/materialize-state.mts';
import { buildFeatureSummary, rebuildFeatureMemory, rebuildGlobalMemory } from './memory.mts';
import type { PipelinePackStateParameters } from './packs.mts';

export interface PipelineParameters extends Record<string, unknown>, PipelinePackStateParameters {
  skipUI: boolean;
  skipDeploy: boolean;
  quick: boolean;
  hitlLevel: string;
  roles: unknown;
  skipFrontend?: boolean;
  skipReview?: boolean;
  artifactDag?: unknown;
  workflowPlanPath?: string;
  workflowHash?: string;
  packHash?: string;
  artifactDagHash?: string;
  runId?: string;
}

export interface PipelineExecutionState extends Omit<ExecutionState, 'parameters'> {
  parameters: PipelineParameters;
}

export interface ArtifactDefinition {
  inputs?: string[];
  /** 显式声明该产物写入的路径集合；用于并行安全组分组。缺省回退到产物名。 */
  writes?: string[];
  agent?: string | string[] | null;
  stage?: number;
  optional?: boolean;
  description?: string;
  type?: string;
  script?: string;
}

export interface ArtifactDag {
  version?: string;
  description?: string;
  artifacts?: Record<string, ArtifactDefinition>;
}

export function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
}

export function writeJson(filePath: string, data: unknown): void {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

export function ensureDir(dirPath: string): void {
  fs.mkdirSync(dirPath, { recursive: true });
}

export function ensureFeatureName(feature: string): void {
  if (!feature) throw new Error('缺少 feature 参数');
}

export function readExecutionView(cwd: string, feature: string): PipelineExecutionState {
  const execJsonPath = path.join(cwd, '.boss', feature, '.meta', 'execution.json');
  if (!fs.existsSync(execJsonPath)) {
    throw new Error(`未找到执行文件: ${path.relative(cwd, execJsonPath)}`);
  }
  return readJson<PipelineExecutionState>(execJsonPath);
}

export function ensureEventsFile(cwd: string, feature: string): string {
  const metaDir = path.join(cwd, '.boss', feature, '.meta');
  const eventsFile = path.join(metaDir, 'events.jsonl');
  if (!fs.existsSync(eventsFile)) {
    throw new Error(`未找到事件文件: ${path.relative(cwd, eventsFile)}`);
  }
  return eventsFile;
}

export function appendEvent(eventsFile: string, event: Omit<RuntimeEvent, 'id'>): RuntimeEvent {
  let id = 1;
  if (fs.existsSync(eventsFile)) {
    // 只数能被解析的行：崩溃残留的损坏尾行不计入 id，避免 id 被虚增后与后续冲突。
    const { records } = readJsonlTolerant(eventsFile);
    id = records.length + 1;
  }
  const payload = { ...event, id };
  appendLineSync(eventsFile, JSON.stringify(payload));
  return payload;
}

export function appendRuntimeEvent(
  cwd: string,
  feature: string,
  eventType: EventType,
  data: Record<string, unknown> = {},
): RuntimeEvent {
  if (!EVENT_TYPE_VALUES.includes(eventType)) {
    throw new Error(`无效事件类型: ${eventType}`);
  }
  const eventsFile = ensureEventsFile(cwd, feature);
  return appendEvent(eventsFile, {
    type: eventType,
    timestamp: new Date().toISOString(),
    data,
  });
}

export function refreshMemory(feature: string, cwd: string): void {
  try {
    rebuildFeatureMemory(feature, { cwd });
    rebuildGlobalMemory({ cwd });
    buildFeatureSummary(feature, { cwd });
  } catch (err) {
    const message = (err as Error).message;
    process.stderr.write(`[boss-skill] memory refresh skipped: ${message}\n`);
  }
}
