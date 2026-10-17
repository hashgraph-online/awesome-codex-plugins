import { readFile, lstat } from 'node:fs/promises';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';
import { digest, LIMITS } from '../workflow-revisions.mjs';
import { skillPathKey } from '../execution/codex-skill-policy.mjs';
import { parseSkill, redactKnownCredentials } from './skill-reader.mjs';

// Discovery is injected by the actual Codex host. A filesystem guess is never
// presented as the executor's complete Skill inventory.
export class SkillInventory {
  constructor(discover) {
    requireValue(typeof discover === 'function', 'SKILL_DISCOVERY_UNAVAILABLE', 'An actual host Skill discovery adapter is required'); this.discover = discover;
  }
  async list(workspace) {
    const result = await this.discover(workspace);
    requireValue(Array.isArray(result?.skills) && Array.isArray(result.errors) && result.skills.length <= 4096, 'SKILL_DISCOVERY_SCHEMA', 'Host discovery returned an unsupported inventory');
    const errors = result.errors.map(item => ({ code: item.code ?? 'SKILL_DISCOVERY_ERROR', path: item.path ?? null, ...(item.message ? {message:item.message} : {}) }));
    const entries = []; const seen = new Set();
    for (const skill of result.skills) {
      try {
        const identity = skillPathKey(skill.path); requireValue(!seen.has(identity), 'SKILL_INVENTORY_DUPLICATE', 'Host returned duplicate Skill paths'); seen.add(identity);
        await noSymlinks(skill.path); const stat = await lstat(skill.path);
        requireValue(stat.isFile() && stat.nlink === 1 && stat.size <= LIMITS.definition, 'SKILL_SOURCE', 'Invalid Skill source file');
        const bytes = await readFile(skill.path); requireValue(bytes.length <= LIMITS.definition, 'SKILL_SIZE', 'Skill source grew during inventory');
        const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); const sourceHash = digest(bytes);
        const parsed = parseSkill(redactKnownCredentials(text).text);
        entries.push({ id: digest(identity + '\0' + sourceHash), path: skill.path, source_hash: sourceHash, name: parsed.metadata.name,
          description: parsed.metadata.description, version: parsed.metadata.version ?? null, scope: skill.scope, enabled: skill.enabled, importable: true });
      } catch (error) { errors.push({ code: error.code ?? 'SKILL_READ_FAILED', path: skill.path ?? null }); }
    }
    return { entries, errors, complete: errors.length === 0, discovered_by: result.discovered_by ?? 'host', profile_scope: result.profile_scope ?? null, model_invocations: result.model_invocations ?? null };
  }
  async select(workspace, id) {
    const inventory = await this.list(workspace); const match = inventory.entries.find(entry => entry.id === id);
    requireValue(match, 'SKILL_SELECTION_STALE', 'Selected Skill is absent or changed; refresh the inventory'); return match;
  }
}
