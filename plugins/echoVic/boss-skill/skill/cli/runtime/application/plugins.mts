import { spawnSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { appendLineSync, readJsonlTolerant } from '../../infrastructure/fs.mts';
import { skillRootFromImportMeta } from '../../infrastructure/paths.mts';
import { listPluginManifestPaths, resolveBuiltInAssetPath } from '../assets.mts';
import { EVENT_TYPES } from '../domain/event-types.mts';
import {
  type ExecutionState,
  materializeState,
  type PluginSummary,
} from '../projectors/materialize-state.mts';

const SKILL_ROOT = skillRootFromImportMeta(import.meta.url);
const PLUGIN_TYPES = new Set(['gate', 'agent', 'pipeline-pack', 'reporter']);
const PLUGIN_NAME_PATTERN = /^[a-z][a-z0-9-]*$/;
const PLUGIN_VERSION_PATTERN = /^\d+\.\d+\.\d+(-[a-z0-9.]+)?$/;

export interface DiscoveredPlugin extends PluginSummary {
  description: string;
  dependencies: string[];
  stages: number[];
  hooks: Record<string, string>;
  manifestPath: string;
  pluginDir: string;
}

export interface PluginDiscoveryResult {
  pluginRoot: string;
  plugins: DiscoveredPlugin[];
  errors: string[];
}

export interface PluginValidationResult extends PluginDiscoveryResult {
  valid: boolean;
}

export interface RunHookResultItem {
  plugin: PluginSummary;
  hook: string;
  stage: number | null;
  exitCode: number;
  passed: boolean;
  stdout: string;
  stderr: string;
}

export interface RunHookResult {
  hook: string;
  feature: string;
  stage: number | null;
  results: RunHookResultItem[];
  execution: ExecutionState;
}

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, 'utf8')) as T;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function ensureFeatureMeta(cwd: string, feature: string): string {
  if (!feature) throw new Error('缺少 feature 参数');
  const metaDir = path.join(cwd, '.boss', feature, '.meta');
  const eventsFile = path.join(metaDir, 'events.jsonl');
  if (!fs.existsSync(eventsFile)) {
    throw new Error(`未找到事件文件: ${path.relative(cwd, eventsFile)}`);
  }
  return eventsFile;
}

export function resolvePluginRoot({
  cwd = process.cwd(),
  repoRoot = SKILL_ROOT,
}: {
  cwd?: string;
  repoRoot?: string;
} = {}): string {
  void repoRoot;
  const projectRoot = path.join(cwd, '.boss', 'plugins');
  return fs.existsSync(projectRoot) ? projectRoot : resolveBuiltInAssetPath('plugins');
}

function resolvePluginDirFromManifest(manifestPath: string): string {
  return path.dirname(manifestPath);
}

function resolvePluginRootForRelativeManifest(manifestPath: string): string {
  return path.dirname(path.dirname(manifestPath));
}

function listProjectPluginManifestPaths(cwd: string): string[] {
  const projectRoot = path.join(cwd, '.boss', 'plugins');
  if (!fs.existsSync(projectRoot) || !fs.statSync(projectRoot).isDirectory()) {
    return [];
  }
  return fs
    .readdirSync(projectRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(projectRoot, entry.name, 'plugin.json'))
    .filter((manifestPath) => fs.existsSync(manifestPath))
    .sort((left, right) => left.localeCompare(right));
}

function collectProjectDuplicateNameErrors(cwd: string): string[] {
  const errors: string[] = [];
  const seenNames = new Map<string, string>();
  const projectRoot = path.join(cwd, '.boss', 'plugins');
  for (const manifestPath of listProjectPluginManifestPaths(cwd)) {
    let manifest: Record<string, unknown>;
    try {
      manifest = readJson<Record<string, unknown>>(manifestPath);
    } catch {
      continue;
    }
    if (typeof manifest.name !== 'string' || manifest.name.length === 0) {
      continue;
    }
    const relativePath = path.relative(projectRoot, manifestPath);
    if (seenNames.has(manifest.name)) {
      errors.push(
        `重复插件名: ${manifest.name} (${seenNames.get(manifest.name)} 与 ${relativePath})`,
      );
      continue;
    }
    seenNames.set(manifest.name, relativePath);
  }
  return errors;
}

export function validatePluginManifest(manifest: unknown, pluginDir: string): string[] {
  const errors: string[] = [];

  if (!isObject(manifest)) {
    return ['plugin.json 必须是对象'];
  }

  if (typeof manifest.name !== 'string' || !PLUGIN_NAME_PATTERN.test(manifest.name)) {
    errors.push('缺少或无效的 name');
  }

  if (typeof manifest.version !== 'string' || !PLUGIN_VERSION_PATTERN.test(manifest.version)) {
    errors.push('缺少或无效的 version');
  }

  if (typeof manifest.type !== 'string' || !PLUGIN_TYPES.has(manifest.type)) {
    errors.push('缺少或无效的 type');
  }

  if (manifest.enabled !== undefined && typeof manifest.enabled !== 'boolean') {
    errors.push('enabled 必须是布尔值');
  }

  if (manifest.dependencies !== undefined) {
    if (
      !Array.isArray(manifest.dependencies) ||
      manifest.dependencies.some((dep) => typeof dep !== 'string' || dep.length === 0)
    ) {
      errors.push('dependencies 必须是字符串数组');
    }
  }

  const hooks = manifest.hooks;
  if (hooks !== undefined && !isObject(hooks)) {
    errors.push('hooks 必须是对象');
  }

  const hookMap = isObject(hooks) ? hooks : {};
  for (const [hookName, hookPath] of Object.entries(hookMap)) {
    if (typeof hookPath !== 'string' || hookPath.length === 0) {
      errors.push(`hooks.${hookName} 必须是非空字符串`);
      continue;
    }
    const fullPath = path.join(pluginDir, hookPath);
    if (!fs.existsSync(fullPath)) {
      errors.push(`hooks.${hookName} 指向不存在文件: ${hookPath}`);
    }
  }

  if (manifest.type === 'gate' && (typeof hookMap.gate !== 'string' || hookMap.gate.length === 0)) {
    errors.push('type=gate 时必须定义 hooks.gate');
  }
  if (
    manifest.type === 'reporter' &&
    (typeof hookMap.report !== 'string' || hookMap.report.length === 0)
  ) {
    errors.push('type=reporter 时必须定义 hooks.report');
  }

  return errors;
}

function stableUniqueStrings(values: unknown): string[] {
  const result: string[] = [];
  const seen = new Set<string>();
  for (const value of Array.isArray(values) ? values : []) {
    if (typeof value !== 'string' || seen.has(value)) continue;
    seen.add(value);
    result.push(value);
  }
  return result;
}

function normalizePlugin(
  manifest: Record<string, unknown>,
  pluginDir: string,
  pluginRoot: string,
): DiscoveredPlugin {
  return {
    name: String(manifest.name),
    version: String(manifest.version),
    type: String(manifest.type),
    description: typeof manifest.description === 'string' ? manifest.description : '',
    dependencies: stableUniqueStrings(manifest.dependencies),
    stages: Array.isArray(manifest.stages)
      ? manifest.stages.map((value) => Number(value)).filter((value) => Number.isInteger(value))
      : [],
    hooks: isObject(manifest.hooks)
      ? Object.fromEntries(
          Object.entries(manifest.hooks).filter(
            (entry): entry is [string, string] => typeof entry[1] === 'string',
          ),
        )
      : {},
    manifestPath: path.relative(pluginRoot, path.join(pluginDir, 'plugin.json')),
    pluginDir,
  };
}

export function sortPluginsByDependencies(
  plugins: DiscoveredPlugin[],
  { externalDependencyNames = new Set<string>() }: { externalDependencyNames?: Set<string> } = {},
): DiscoveredPlugin[] {
  const byName = new Map<string, DiscoveredPlugin>();
  for (const plugin of plugins) {
    byName.set(plugin.name, plugin);
  }

  const dependencyErrors: string[] = [];
  for (const plugin of plugins) {
    for (const dep of plugin.dependencies ?? []) {
      if (!byName.has(dep) && !externalDependencyNames.has(dep)) {
        dependencyErrors.push(`${plugin.name}: 依赖不存在: ${dep}`);
      }
    }
  }
  if (dependencyErrors.length > 0) {
    throw new Error(dependencyErrors.join('\n'));
  }

  const indegree = new Map<string, number>();
  const outgoing = new Map<string, string[]>();
  for (const plugin of plugins) {
    indegree.set(plugin.name, 0);
    outgoing.set(plugin.name, []);
  }

  for (const plugin of plugins) {
    for (const dep of plugin.dependencies ?? []) {
      if (!byName.has(dep)) continue;
      outgoing.get(dep)!.push(plugin.name);
      indegree.set(plugin.name, (indegree.get(plugin.name) ?? 0) + 1);
    }
  }

  const queue = [
    ...plugins.map((plugin) => plugin.name).filter((name) => indegree.get(name) === 0),
  ].sort();
  const order: string[] = [];

  while (queue.length > 0) {
    const name = queue.shift() as string;
    order.push(name);
    const nextList = (outgoing.get(name) ?? []).slice().sort();
    for (const next of nextList) {
      indegree.set(next, (indegree.get(next) ?? 0) - 1);
      if (indegree.get(next) === 0) {
        queue.push(next);
      }
    }
    queue.sort();
  }

  if (order.length !== plugins.length) {
    throw new Error('插件依赖存在循环');
  }

  return order.map((name) => byName.get(name) as DiscoveredPlugin);
}

export function discoverPlugins({
  cwd = process.cwd(),
  repoRoot = SKILL_ROOT,
  type,
  strict = true,
  externalDependencyNames = new Set<string>(),
}: {
  cwd?: string;
  repoRoot?: string;
  type?: string;
  strict?: boolean;
  externalDependencyNames?: Set<string>;
} = {}): PluginDiscoveryResult {
  void repoRoot;
  const pluginRoot = resolvePluginRoot({ cwd });
  const manifestItems = listPluginManifestPaths({ cwd });
  const errors: string[] = collectProjectDuplicateNameErrors(cwd);
  const candidates: DiscoveredPlugin[] = [];
  const seenNames = new Map<string, string>();

  for (const item of manifestItems) {
    const manifestPath = item.path;
    const pluginDir = resolvePluginDirFromManifest(manifestPath);
    const relativeRoot = resolvePluginRootForRelativeManifest(manifestPath);
    let manifest: Record<string, unknown>;
    try {
      manifest = readJson<Record<string, unknown>>(manifestPath);
    } catch (err) {
      errors.push(
        `${path.relative(relativeRoot, manifestPath)}: JSON 解析失败 (${(err as Error).message})`,
      );
      continue;
    }

    if (manifest.enabled === false) {
      continue;
    }
    if (type && manifest.type !== type) {
      continue;
    }

    const validationErrors = validatePluginManifest(manifest, pluginDir);
    if (validationErrors.length > 0) {
      for (const reason of validationErrors) {
        errors.push(`${path.relative(relativeRoot, manifestPath)}: ${reason}`);
      }
      continue;
    }

    const normalized = normalizePlugin(manifest, pluginDir, relativeRoot);
    if (seenNames.has(normalized.name)) {
      errors.push(
        `重复插件名: ${normalized.name} (${seenNames.get(normalized.name)} 与 ${normalized.manifestPath})`,
      );
      continue;
    }
    seenNames.set(normalized.name, normalized.manifestPath);
    candidates.push(normalized);
  }

  let orderedPlugins: DiscoveredPlugin[] = [];
  if (errors.length === 0 || !strict) {
    try {
      orderedPlugins = sortPluginsByDependencies(candidates, { externalDependencyNames });
    } catch (err) {
      errors.push((err as Error).message);
    }
  }

  if (strict && errors.length > 0) {
    throw new Error(errors.join('\n'));
  }

  return {
    pluginRoot,
    plugins: orderedPlugins,
    errors,
  };
}

export function validatePlugins(
  options: Parameters<typeof discoverPlugins>[0] = {},
): PluginValidationResult {
  const result = discoverPlugins({ ...options, strict: false });
  return {
    ...result,
    valid: result.errors.length === 0,
  };
}

function appendEvent(
  eventsFile: string,
  event: { type: string; timestamp: string; data: Record<string, unknown> },
): { id: number; type: string; timestamp: string; data: Record<string, unknown> } {
  let id = 1;
  if (fs.existsSync(eventsFile)) {
    // 只数可解析行，忽略崩溃残留的损坏尾行（与 state.appendEvent 同口径）
    id = readJsonlTolerant(eventsFile).records.length + 1;
  }
  const payload = { ...event, id };
  appendLineSync(eventsFile, JSON.stringify(payload));
  return payload;
}

function summarizePlugin(
  plugin: Pick<DiscoveredPlugin, 'name' | 'version' | 'type' | 'manifestPath' | 'dependencies'>,
): PluginSummary {
  const summary: PluginSummary = {
    name: plugin.name,
    version: plugin.version,
    type: plugin.type,
    manifestPath: plugin.manifestPath,
  };
  if (Array.isArray(plugin.dependencies) && plugin.dependencies.length > 0) {
    summary.dependencies = plugin.dependencies;
  }
  return summary;
}

function parseStage(stage: string | number | null | undefined): number | null {
  if (stage === undefined || stage === null || stage === '') {
    return null;
  }
  const parsed = Number(stage);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error('stage 必须是正整数');
  }
  return parsed;
}

function resolveHookScriptPath(plugin: DiscoveredPlugin, hook: string): string {
  const hookPath = plugin.hooks[hook] ?? '';
  if (typeof hookPath !== 'string' || hookPath.length === 0) {
    return '';
  }
  return path.join(plugin.pluginDir, hookPath);
}

function mergePluginSets(existing: PluginSummary[], incoming: DiscoveredPlugin[]): PluginSummary[] {
  const merged: PluginSummary[] = [];
  const byName = new Map<string, PluginSummary>();

  for (const plugin of existing ?? []) {
    if (!plugin || typeof plugin.name !== 'string' || byName.has(plugin.name)) continue;
    const normalized = summarizePlugin({
      name: plugin.name,
      version: plugin.version,
      type: plugin.type,
      manifestPath: plugin.manifestPath ?? '',
      dependencies: plugin.dependencies ?? [],
    });
    byName.set(normalized.name, normalized);
    merged.push(normalized);
  }

  for (const plugin of incoming ?? []) {
    const normalized = summarizePlugin(plugin);
    if (byName.has(normalized.name)) {
      const index = merged.findIndex((item) => item.name === normalized.name);
      if (index >= 0) merged[index] = normalized;
      byName.set(normalized.name, normalized);
      continue;
    }
    byName.set(normalized.name, normalized);
    merged.push(normalized);
  }

  return merged;
}

export function registerPlugins(
  feature: string,
  {
    cwd = process.cwd(),
    repoRoot = SKILL_ROOT,
    type,
  }: { cwd?: string; repoRoot?: string; type?: string } = {},
): { plugins: PluginSummary[]; execution: ExecutionState } {
  const eventsFile = ensureFeatureMeta(cwd, feature);
  const currentState = materializeState(feature, cwd).state;
  const existingNames = new Set(
    (Array.isArray(currentState.plugins) ? currentState.plugins : [])
      .map((plugin) => plugin?.name)
      .filter((name): name is string => typeof name === 'string' && name.length > 0),
  );
  const discovery = discoverPlugins({
    cwd,
    repoRoot,
    type,
    strict: true,
    externalDependencyNames: existingNames,
  });
  const now = new Date().toISOString();

  for (const plugin of discovery.plugins) {
    appendEvent(eventsFile, {
      type: EVENT_TYPES.PLUGIN_DISCOVERED,
      timestamp: now,
      data: { plugin: summarizePlugin(plugin) },
    });
    appendEvent(eventsFile, {
      type: EVENT_TYPES.PLUGIN_ACTIVATED,
      timestamp: now,
      data: { plugin: summarizePlugin(plugin) },
    });
  }

  const mergedPlugins = mergePluginSets(currentState.plugins ?? [], discovery.plugins);
  appendEvent(eventsFile, {
    type: EVENT_TYPES.PLUGINS_REGISTERED,
    timestamp: now,
    data: { plugins: mergedPlugins },
  });

  const { state } = materializeState(feature, cwd);
  return {
    plugins: mergedPlugins,
    execution: state,
  };
}

export function runHook(
  hook: string,
  feature: string,
  {
    cwd = process.cwd(),
    repoRoot = SKILL_ROOT,
    stage,
  }: { cwd?: string; repoRoot?: string; stage?: string | number | null } = {},
): RunHookResult {
  if (!hook) throw new Error('缺少 hook 参数');
  const eventsFile = ensureFeatureMeta(cwd, feature);
  const stageNumber = parseStage(stage);
  const discovery = discoverPlugins({ cwd, repoRoot, strict: true });
  const now = new Date().toISOString();
  const results: RunHookResultItem[] = [];

  for (const plugin of discovery.plugins) {
    const fullPath = resolveHookScriptPath(plugin, hook);
    if (!fullPath) continue;
    if (
      stageNumber != null &&
      Array.isArray(plugin.stages) &&
      plugin.stages.length > 0 &&
      !plugin.stages.includes(stageNumber)
    ) {
      continue;
    }

    const args = [feature];
    if (stageNumber != null) {
      args.push(String(stageNumber));
    }

    const command = fullPath.endsWith('.sh') ? 'bash' : fullPath;
    const commandArgs = fullPath.endsWith('.sh') ? [fullPath, ...args] : args;
    const execution = spawnSync(command, commandArgs, {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    if (execution.error) {
      throw execution.error;
    }

    const summary = summarizePlugin(plugin);
    const exitCode =
      Number.isInteger(execution.status) && Number(execution.status) >= 0
        ? Number(execution.status)
        : 1;
    const passed = exitCode === 0;

    appendEvent(eventsFile, {
      type: passed ? EVENT_TYPES.PLUGIN_HOOK_EXECUTED : EVENT_TYPES.PLUGIN_HOOK_FAILED,
      timestamp: now,
      data: {
        plugin: summary,
        hook,
        stage: stageNumber == null ? undefined : stageNumber,
        exitCode,
      },
    });

    results.push({
      plugin: summary,
      hook,
      stage: stageNumber,
      exitCode,
      passed,
      stdout: execution.stdout || '',
      stderr: execution.stderr || '',
    });
  }

  const { state } = materializeState(feature, cwd);
  return {
    hook,
    feature,
    stage: stageNumber,
    results,
    execution: state,
  };
}
