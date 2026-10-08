import * as fs from 'node:fs';
import * as path from 'node:path';

import { normalizeCommands, type StructuredCommand } from '../domain/structured-wave.mts';

export type EvidenceWaveStatus = 'pending' | 'running' | 'completed' | 'blocked' | 'failed';

export interface EvidenceWave {
  id: string;
  title: string;
  scope: string;
  writeSet: string[];
  redTests: StructuredCommand[];
  greenGates: StructuredCommand[];
  contractRows: string[];
  rollbackRisk: string;
  pausePolicy: string;
  status: EvidenceWaveStatus;
}

const WAVE_STATUSES: ReadonlySet<string> = new Set<string>([
  'pending',
  'running',
  'completed',
  'blocked',
  'failed',
]);

function normalizeStatus(value: unknown): EvidenceWaveStatus {
  return typeof value === 'string' && WAVE_STATUSES.has(value)
    ? (value as EvidenceWaveStatus)
    : 'pending';
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string' && item.length > 0);
}

function splitMarkdownRow(line: string): string[] {
  const cells: string[] = [];
  let current = '';
  let inCodeSpan = false;
  const trimmed = line.trim();

  for (let index = 0; index < trimmed.length; index += 1) {
    const char = trimmed[index]!;
    const previous = trimmed[index - 1];
    if (char === '`' && previous !== '\\') {
      inCodeSpan = !inCodeSpan;
      current += char;
      continue;
    }
    if (char === '|' && previous !== '\\' && !inCodeSpan) {
      cells.push(current.trim());
      current = '';
      continue;
    }
    if (char === '|' && previous === '\\') {
      current = `${current.slice(0, -1)}|`;
      continue;
    }
    current += char;
  }
  cells.push(current.trim());

  if (cells[0] === '') cells.shift();
  if (cells[cells.length - 1] === '') cells.pop();
  return cells;
}

function isSeparatorRow(cells: string[]): boolean {
  return cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function cleanCell(value: string): string {
  return value
    .trim()
    .replace(/^`+|`+$/g, '')
    .trim();
}

function splitListCell(value: string): string[] {
  return value
    .split(/<br\s*\/?>|,|，/i)
    .map(cleanCell)
    .filter(Boolean);
}

function slugify(value: string): string {
  return value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function uniqueWaveId(title: string, index: number, usedIds: Map<string, number>): string {
  const base = slugify(title) || `wave-${index + 1}`;
  const seen = usedIds.get(base) ?? 0;
  usedIds.set(base, seen + 1);
  return seen === 0 ? base : `${base}-${seen + 1}`;
}

function parseTitleAndStatus(rawTitle: string): { title: string; status: EvidenceWaveStatus } {
  const marker = rawTitle.match(/^\[(pending|running|completed|blocked|failed)\]\s*/i);
  if (!marker) {
    return { title: rawTitle, status: 'pending' };
  }
  return {
    title: rawTitle.slice(marker[0].length).trim(),
    status: marker[1]!.toLowerCase() as EvidenceWaveStatus,
  };
}

/** 结构化真相源：`.boss/<feature>/waves.json`。 */
export function wavesPath(feature: string, cwd: string): string {
  return path.join(cwd, '.boss', feature, 'waves.json');
}

function readStructuredWaves(feature: string, cwd: string): EvidenceWave[] | null {
  const filePath = wavesPath(feature, cwd);
  if (!fs.existsSync(filePath)) return null;

  let parsed: unknown;
  try {
    if (!fs.statSync(filePath).isFile()) return null;
    parsed = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    throw new Error(`waves.json 解析失败: ${(err as Error).message}`);
  }

  const rawWaves = Array.isArray(parsed)
    ? parsed
    : Array.isArray((parsed as Record<string, unknown>)?.waves)
      ? ((parsed as Record<string, unknown>).waves as unknown[])
      : null;
  if (!rawWaves) {
    throw new Error('waves.json 必须是数组或包含 waves 数组的对象');
  }

  const usedIds = new Map<string, number>();
  return rawWaves.map((entry, index) => {
    const record = (entry ?? {}) as Record<string, unknown>;
    const title = typeof record.title === 'string' ? record.title : '';
    const explicitId = typeof record.id === 'string' && record.id.length > 0 ? record.id : '';
    return {
      id: explicitId || uniqueWaveId(title, index, usedIds),
      title,
      scope: typeof record.scope === 'string' ? record.scope : '',
      writeSet: normalizeStringList(record.writeSet),
      redTests: normalizeCommands(record.redTests, `waves[${index}].redTests`),
      greenGates: normalizeCommands(record.greenGates, `waves[${index}].greenGates`),
      contractRows: normalizeStringList(record.contractRows),
      rollbackRisk: typeof record.stopCondition === 'string' ? record.stopCondition : '',
      pausePolicy: typeof record.stopCondition === 'string' ? record.stopCondition : '',
      status: normalizeStatus(record.status),
    };
  });
}

/**
 * 从 Markdown 表格读取 wave 的*非命令*字段。
 *
 * 命令刻意不从 Markdown 读取：表格单元格曾被直接交给 shell 执行，
 * 任何能写 tasks.md 的人即可任意执行命令。验证命令一律改由
 * waves.json 提供 argv 数组。
 */
function readMarkdownWaves(feature: string, cwd: string): EvidenceWave[] {
  const tasksPath = path.join(cwd, '.boss', feature, 'tasks.md');
  if (!fs.existsSync(tasksPath)) {
    return [];
  }

  let lines: string[];
  try {
    if (!fs.statSync(tasksPath).isFile()) {
      return [];
    }
    lines = fs.readFileSync(tasksPath, 'utf8').split(/\r?\n/);
  } catch {
    return [];
  }
  const headerIndex = lines.findIndex((line) => {
    if (!line.trim().startsWith('|')) return false;
    const cells = splitMarkdownRow(line);
    return cells[0] === 'Evidence Wave' && cells.includes('Stop Condition');
  });

  if (headerIndex === -1) {
    return [];
  }

  const rows: EvidenceWave[] = [];
  const usedIds = new Map<string, number>();
  for (const line of lines.slice(headerIndex + 1)) {
    if (!line.trim().startsWith('|')) break;

    const cells = splitMarkdownRow(line);
    if (isSeparatorRow(cells)) continue;
    if (cells.length < 7) continue;

    const [title, scope, ownerFiles, , , contractRows, stopCondition] = cells;
    const parsedTitle = parseTitleAndStatus(cleanCell(title ?? ''));
    const cleanedTitle = parsedTitle.title;
    if (!cleanedTitle) continue;
    const cleanedStopCondition = cleanCell(stopCondition ?? '');

    rows.push({
      id: uniqueWaveId(cleanedTitle, rows.length, usedIds),
      title: cleanedTitle,
      scope: cleanCell(scope ?? ''),
      writeSet: splitListCell(ownerFiles ?? ''),
      // Markdown 不再作为命令来源
      redTests: [],
      greenGates: [],
      contractRows: splitListCell(contractRows ?? ''),
      rollbackRisk: cleanedStopCondition,
      pausePolicy: cleanedStopCondition,
      status: parsedTitle.status,
    });
  }

  return rows;
}

/**
 * 读取 wave 列表。waves.json 存在时以其为准；否则退回 Markdown，
 * 但退回路径不携带任何可执行命令。
 */
export function readWaves(
  feature: string,
  { cwd = process.cwd() }: { cwd?: string } = {},
): EvidenceWave[] {
  return readStructuredWaves(feature, cwd) ?? readMarkdownWaves(feature, cwd);
}
