import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

export function dirnameFromImportMeta(importMetaUrl: string): string {
  return path.dirname(fileURLToPath(importMetaUrl));
}

/**
 * 定位 skill 根目录（含 SKILL.md 的目录）。
 *
 * CLI 产物随 skill 分发，存在两种布局：
 * - 安装副本：<skill>/cli/...（marketplace / skills.sh 安装，SKILL.md 在祖先链上）
 * - 仓库开发：skill/cli/...（SKILL.md 在 <repo>/skill/）
 * 两种布局都通过「向上找到第一个含 SKILL.md 的目录」解析，安装位置变化时无需改代码。
 */
export function findSkillRoot(startDir: string): string {
  let dir = path.resolve(startDir);
  for (;;) {
    for (const candidate of [path.join(dir, 'SKILL.md'), path.join(dir, 'skill', 'SKILL.md')]) {
      if (fs.existsSync(candidate)) return path.dirname(candidate);
    }
    const parent = path.dirname(dir);
    if (parent === dir) {
      throw new Error(`Boss skill root not found from ${startDir} (no SKILL.md in ancestors)`);
    }
    dir = parent;
  }
}

export function skillRootFromImportMeta(importMetaUrl: string): string {
  return findSkillRoot(dirnameFromImportMeta(importMetaUrl));
}

/**
 * 读取 SKILL.md frontmatter 的 version —— 版本真相源随 skill 分发，
 * 不依赖 npm 包里的 package.json（安装副本里不存在）。
 */
export function readSkillVersion(skillRoot: string): string {
  const skillMd = path.join(skillRoot, 'SKILL.md');
  try {
    const match = fs.readFileSync(skillMd, 'utf8').match(/^version:\s*(.+)$/m);
    if (match?.[1]) return match[1].trim();
  } catch {
    // 落到 dev 占位版本
  }
  return '0.0.0-dev';
}

export function packageRootFromImportMeta(importMetaUrl: string, ancestorLevels: number): string {
  if (!Number.isInteger(ancestorLevels) || ancestorLevels < 0) {
    throw new Error(`Invalid package root depth: ${ancestorLevels}`);
  }
  return path.resolve(
    dirnameFromImportMeta(importMetaUrl),
    ...Array.from({ length: ancestorLevels }, () => '..'),
  );
}

export function resolvePackagePath(
  importMetaUrl: string,
  ancestorLevels: number,
  ...segments: string[]
): string {
  return path.join(packageRootFromImportMeta(importMetaUrl, ancestorLevels), ...segments);
}

export function resolveInside(baseDir: string, inputPath: string): string {
  return path.isAbsolute(inputPath) ? inputPath : path.resolve(baseDir, inputPath);
}
