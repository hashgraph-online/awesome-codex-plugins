import * as fs from 'node:fs';
import * as path from 'node:path';

import { copyDirectory } from '../infrastructure/fs.mts';
import type { DiscoveredSkill } from './discover.mts';
import { parseSkillFrontmatter } from './discover.mts';

export interface InstallOutcome {
  agent: string;
  skill: string;
  path: string;
  status: 'installed' | 'failed' | 'skipped';
  error?: string;
}

/** Version recorded in an installed skill's SKILL.md frontmatter, if any. */
export function readInstalledVersion(destDir: string): string | undefined {
  const skillMd = path.join(destDir, 'SKILL.md');
  if (!fs.existsSync(skillMd)) return undefined;
  try {
    return parseSkillFrontmatter(fs.readFileSync(skillMd, 'utf8')).version;
  } catch {
    return undefined;
  }
}

export function installSkillToPath(
  skill: DiscoveredSkill,
  agentId: string,
  dest: string,
): InstallOutcome {
  try {
    if (fs.existsSync(dest)) {
      fs.rmSync(dest, { recursive: true });
    }
    copyDirectory(skill.dir, dest, ['.git']);
    return { agent: agentId, skill: skill.name, path: dest, status: 'installed' };
  } catch (error) {
    return {
      agent: agentId,
      skill: skill.name,
      path: dest,
      status: 'failed',
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
