import { opendir, lstat } from 'node:fs/promises';
import { join, resolve, isAbsolute } from 'node:path';
import { homedir } from 'node:os';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';

// Import discovery only. This never claims the executor has enabled these Skills.
export async function discoverFolderSkills(folder, {env = process.env} = {}) {
  const home = env.CODEX_HOME || join(homedir(), '.codex');
  requireValue(!folder || (typeof folder === 'string' && isAbsolute(folder)), 'SKILL_DISCOVERY_FOLDER', 'Custom folder must be an absolute path');
  requireValue(isAbsolute(home), 'SKILL_DISCOVERY_HOME', 'CODEX_HOME must be absolute');
  const roots = folder ? [resolve(folder)] : [join(home,'skills'),join(home,'plugins','cache')];
  const skills = [], errors = []; let count = 0;
  async function walk(path, depth) {
    requireValue(count <= 20000 && depth <= 16 && skills.length < 4096, 'SKILL_DISCOVERY_LIMIT', 'Skill folder scan exceeded its bounded limit; choose a narrower folder');
    await noSymlinks(path);
    const entries = await opendir(path);
    for await (const entry of entries) {
      requireValue(++count <= 20000, 'SKILL_DISCOVERY_LIMIT', 'Skill folder scan exceeded 20000 entries; choose a narrower folder');
      if (['node_modules','.git','.trash'].includes(entry.name)) continue;
      const target = join(path,entry.name);
      if (entry.isSymbolicLink()) { errors.push({code:'SKILL_SOURCE_LINK_SKIPPED',path:target}); continue; }
      if (entry.isFile() && entry.name === 'SKILL.md') skills.push({path:target,scope:'folder',enabled:false});
      else if (entry.isDirectory()) await walk(target,depth+1);
    }
  }
  for (const root of roots) {
    try { const stat = await lstat(root); requireValue(stat.isDirectory(), 'SKILL_DISCOVERY_FOLDER', 'Scan root must be a directory'); await walk(root,0); }
    catch (error) { errors.push({code:error.code ?? 'SKILL_DISCOVERY_FAILED',path:root,message:error.message}); }
  }
  skills.sort((a,b)=>a.path.localeCompare(b.path));
  return {skills,errors,discovered_by:'bounded-folder-scan',profile_scope:roots.join('; '),model_invocations:0};
}
