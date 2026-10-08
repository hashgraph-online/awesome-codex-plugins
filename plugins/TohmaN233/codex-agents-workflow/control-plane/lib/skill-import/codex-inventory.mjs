import { readFile, lstat } from 'node:fs/promises';
import { join, isAbsolute, resolve } from 'node:path';
import { homedir } from 'node:os';
import { createCodexClient } from '../execution/codex-app-server-client.mjs';
import { qualifiedCodexBinary, validateStrictConfig, codexQualification } from '../execution/strict-config.mjs';
import { skillPathKey } from '../execution/codex-skill-policy.mjs';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';
import { digest } from '../workflow-revisions.mjs';

// This sidecar enumerates the actual configured Codex profile. It never starts a
// thread/turn, logs in, writes configuration or injects a discovery-root guess.
// Codex itself may refresh ordinary metadata/system caches in that profile.
export async function discoverCodexSkills(workspace, { config, env = process.env, clientFactory = createCodexClient, qualify = qualifiedCodexBinary } = {}) {
  requireValue(typeof workspace === 'string' && isAbsolute(workspace), 'SKILL_DISCOVERY_WORKSPACE', 'Discovery requires an absolute workspace');
  await noSymlinks(workspace); requireValue((await lstat(workspace)).isDirectory(), 'SKILL_DISCOVERY_WORKSPACE', 'Discovery workspace must exist');
  const settings = validateStrictConfig(config.strict_executor); await qualify(settings, { env, scope: 'discovery' });
  const home = env.CODEX_HOME || join(homedir(), '.codex');
  requireValue(isAbsolute(home), 'SKILL_DISCOVERY_HOME', 'Configured CODEX_HOME must be absolute'); await noSymlinks(home);
  const configPath = join(home, 'config.toml');
  async function configHash() {
    try {
      await noSymlinks(configPath); const stat = await lstat(configPath);
      requireValue(stat.isFile() && stat.size <= 4 * 1024 * 1024, 'SKILL_DISCOVERY_CONFIG', 'Host config is not a bounded regular file');
      const bytes = await readFile(configPath); requireValue(bytes.length <= 4 * 1024 * 1024, 'SKILL_DISCOVERY_CONFIG', 'Host config grew beyond limit'); return digest(bytes);
    } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  }
  const before = await configHash(); let client; let result; const errors = [];
  try {
    client = clientFactory(settings.codex_binary, { home: resolve(home), cwd: workspace, env });
    await client.call('initialize', { clientInfo: { name: 'codex_agents_workflow_skill_inventory', version: '0.1.0' }, capabilities: {} }); client.initialized();
    const response = await client.call('skills/list', { cwds: [workspace], forceReload: true });
    requireValue(Array.isArray(response?.data) && response.data.length === 1 && skillPathKey(response.data[0].cwd) === skillPathKey(workspace), 'SKILL_DISCOVERY_SCHEMA', 'Codex returned another workspace or unsupported inventory schema');
    const entry = response.data[0];
    requireValue(Array.isArray(entry.skills) && entry.skills.length <= 4096 && Array.isArray(entry.errors) && entry.errors.length <= 4096, 'SKILL_DISCOVERY_SCHEMA', 'Codex inventory exceeds the bounded schema');
    const skills = entry.skills.map(skill => {
      skillPathKey(skill.path);
      requireValue(['user', 'repo', 'admin', 'system'].includes(skill.scope) && typeof skill.enabled === 'boolean', 'SKILL_DISCOVERY_SCHEMA', 'Codex returned an unsupported Skill scope or enabled state');
      return { path: skill.path, scope: skill.scope, enabled: skill.enabled };
    });
    result = { skills, errors: entry.errors.map(error => ({ code: 'CODEX_SKILL_DISCOVERY_ERROR', path: typeof error.path === 'string' ? error.path : null })),
      discovered_by: 'selected-codex-app-server-configured-profile', qualification: codexQualification(settings),
      profile_scope: 'configured-CODEX_HOME-and-workspace', model_invocations: 0 };
  } catch (error) { errors.push(error); }
  finally {
    if (client) try { await client.close(); } catch (error) { errors.push(error); }
    try { requireValue(await configHash() === before, 'SKILL_DISCOVERY_CONFIG_CHANGED', 'Host config changed during discovery; refresh without reverting the edit'); } catch (error) { errors.push(error); }
  }
  if (errors.length > 1) throw Object.assign(new AggregateError(errors, 'Codex discovery and shutdown/integrity checks failed'), { code: 'SKILL_DISCOVERY_INCOMPLETE' });
  if (errors.length) throw errors[0];
  return result;
}
