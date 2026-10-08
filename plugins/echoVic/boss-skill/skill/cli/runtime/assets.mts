import * as fs from 'node:fs';
import * as path from 'node:path';
import { skillRootFromImportMeta } from '../infrastructure/paths.mts';

const ASSETS_ROOT = path.join(skillRootFromImportMeta(import.meta.url), 'assets');

export interface AssetOptions {
  cwd?: string;
}

export interface NamedAssetPath {
  name: string;
  path: string;
  source: 'project' | 'builtin';
}

function readJsonObject(filePath: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8')) as unknown;
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

function requireExistingPath(filePath: string, label: string): string {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing Boss CLI built-in asset: ${label} (${filePath})`);
  }
  return filePath;
}

function listManifestPaths(
  root: string,
  fileName: string,
  source: NamedAssetPath['source'],
  required = false,
): NamedAssetPath[] {
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    if (required) {
      throw new Error(`Missing Boss CLI built-in asset directory: ${root}`);
    }
    return [];
  }
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const manifestPath = path.join(root, entry.name, fileName);
      const manifest = fs.existsSync(manifestPath) ? readJsonObject(manifestPath) : null;
      return {
        name:
          typeof manifest?.name === 'string' && manifest.name.length > 0
            ? manifest.name
            : entry.name,
        path: manifestPath,
        source,
      };
    })
    .filter((item) => fs.existsSync(item.path))
    .sort((left, right) => left.name.localeCompare(right.name));
}

function mergeByName(builtin: NamedAssetPath[], project: NamedAssetPath[]): NamedAssetPath[] {
  const byName = new Map<string, NamedAssetPath>();
  for (const item of builtin) byName.set(item.name, item);
  for (const item of project) byName.set(item.name, item);
  return [...byName.values()].sort((left, right) => left.name.localeCompare(right.name));
}

export function resolveBuiltInAssetPath(...segments: string[]): string {
  return path.join(ASSETS_ROOT, ...segments);
}

export function resolveProjectBossPath(
  { cwd = process.cwd() }: AssetOptions = {},
  ...segments: string[]
): string {
  return path.join(cwd, '.boss', ...segments);
}

export function resolvePluginSchemaPath(): string {
  return requireExistingPath(resolveBuiltInAssetPath('plugin-schema.json'), 'plugin-schema.json');
}

export function resolveArtifactDagPath({
  cwd = process.cwd(),
  packDagPath,
}: AssetOptions & { packDagPath?: string } = {}): string {
  const projectDag = resolveProjectBossPath({ cwd }, 'artifact-dag.json');
  if (fs.existsSync(projectDag)) return projectDag;
  if (packDagPath) {
    const resolvedPackDag = path.isAbsolute(packDagPath)
      ? packDagPath
      : path.resolve(cwd, packDagPath);
    if (fs.existsSync(resolvedPackDag)) return resolvedPackDag;
  }
  return requireExistingPath(resolveBuiltInAssetPath('artifact-dag.json'), 'artifact-dag.json');
}

export function listPipelinePackManifestPaths({
  cwd = process.cwd(),
}: AssetOptions = {}): NamedAssetPath[] {
  const builtin = listManifestPaths(
    resolveBuiltInAssetPath('pipeline-packs'),
    'pipeline.json',
    'builtin',
    true,
  );
  const project = listManifestPaths(
    resolveProjectBossPath({ cwd }, 'pipeline-packs'),
    'pipeline.json',
    'project',
  );
  return mergeByName(builtin, project);
}

export function listPluginManifestPaths({
  cwd = process.cwd(),
}: AssetOptions = {}): NamedAssetPath[] {
  const builtin = listManifestPaths(
    resolveBuiltInAssetPath('plugins'),
    'plugin.json',
    'builtin',
    true,
  );
  const project = listManifestPaths(
    resolveProjectBossPath({ cwd }, 'plugins'),
    'plugin.json',
    'project',
  );
  return mergeByName(builtin, project);
}
