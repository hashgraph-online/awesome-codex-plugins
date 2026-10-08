import { isAbsolute, normalize, join, dirname } from 'node:path';
import { readFile, mkdir, open } from 'node:fs/promises';
import { canonicalJSON, digest, prepareResources, LIMITS } from '../workflow-revisions.mjs';
import { requireValue, noSymlinks } from '../workflow-paths.mjs';

export function skillPathKey(path) {
  requireValue(typeof path === 'string' && isAbsolute(path), 'SKILL_PATH', 'Skill identity requires an absolute path');
  const key = normalize(path); return process.platform === 'win32' ? key.toLowerCase() : key;
}
export function skillInventory(result, cwd) {
  requireValue(Array.isArray(result?.data) && result.data.length === 1, 'SKILL_INVENTORY_SCHEMA', 'Expected one actual execution-profile inventory');
  const entry = result.data[0];
  requireValue(skillPathKey(entry.cwd) === skillPathKey(cwd) && Array.isArray(entry.errors) && !entry.errors.length && Array.isArray(entry.skills), 'SKILL_DISCOVERY_FAILED', 'Skill discovery errors or cwd mismatch invalidate Strict');
  const seen = new Set();
  return entry.skills.map(skill => {
    const key = skillPathKey(skill.path);
    requireValue(typeof skill.name === 'string' && ['repo', 'user', 'admin', 'system'].includes(skill.scope) && typeof skill.enabled === 'boolean' && !seen.has(key), 'SKILL_INVENTORY_SCHEMA', 'Unknown Skill scope/identity schema');
    seen.add(key); return { name: skill.name, path: skill.path, scope: skill.scope, enabled: skill.enabled };
  }).sort((a, b) => skillPathKey(a.path).localeCompare(skillPathKey(b.path), 'en'));
}

export async function createSkillPolicy({ home, cwd, skillPolicy, allowed = [], hostExecutionOnly = false }) {
  requireValue(skillPolicy?.mode === 'strict' && skillPolicy.implicit === 'deny' && Array.isArray(skillPolicy.shadowed_skill_paths) && Array.isArray(skillPolicy.ambient_allow), 'SKILL_POLICY', 'Strict requires an explicit deny policy and path allow/shadow sets');
  const shadows = new Set(skillPolicy.shadowed_skill_paths.map(skillPathKey));
  requireValue(allowed.length <= 64, 'SKILL_ALLOW_LIMIT', 'Too many explicitly allowed Skills');
  if (hostExecutionOnly) {
    requireValue(allowed.length === 0 && skillPolicy.ambient_allow.length === 0, 'SKILL_ISOLATION_FAILED', 'Host-only execution cannot import Skills');
    let applied = false;
    const audit = { discovered_skills: [], allowed_skills: [], shadowed_skills: [...shadows], disabled_skills: [], uncontrolled_system_skills: [], inventory_hash: digest(canonicalJSON([])), catalog_mode: 'disabled_by_profile' };
    return {
      async apply() { applied = true; return structuredClone(audit); },
      async verify() { requireValue(applied, 'SKILL_POLICY_NOT_APPLIED', 'Apply Skill policy before creating any thread'); },
      explicitInputs(sourcePaths) {
        requireValue(Array.isArray(sourcePaths) && sourcePaths.length === 0, 'SKILL_INJECTION_DENIED', 'Host-only execution cannot inject Skills');
        return [];
      },
      tools() { return []; },
      read() { requireValue(false, 'SKILL_READ_DENIED', 'Host-only execution cannot read Skills'); },
      audit: () => applied ? structuredClone(audit) : null,
    };
  }
  const pins = new Map(); const sources = new Set(); const files = [];
  for (const skill of allowed) {
    const source = skillPathKey(skill.source_path);
    requireValue(!sources.has(source) && !shadows.has(source), 'SKILL_SHADOWED', 'Duplicate or shadowed Skill cannot be injected'); sources.add(source);
    requireValue(typeof skill.name === 'string' && skill.name && /^[a-f0-9]{64}$/.test(skill.source_hash), 'SKILL_PIN', 'Allowed Skill needs name and content pin');
    const prepared = prepareResources(skill.files);
    const main = prepared.manifest.find(file => file.path === 'SKILL.md');
    requireValue(main?.sha256 === skill.source_hash, 'SKILL_PIN_CHANGED', 'Skill instructions differ from their pinned source');
    const directory = join(home, 'skills', digest(source + '\0' + skill.source_hash)); await noSymlinks(home); await mkdir(directory);
    for (const file of prepared.manifest) {
      const path = join(directory, ...file.path.split('/')); await mkdir(dirname(path), { recursive: true }); await noSymlinks(dirname(path));
      const handle = await open(path, 'wx', 0o400);
      try { await handle.writeFile(prepared.blobs.get(file.sha256)); await handle.sync(); } finally { await handle.close(); }
      files.push({ path, sha256: file.sha256 });
    }
    const path = join(directory, 'SKILL.md');
    pins.set(skillPathKey(path), { name: skill.name, path, source_path: skill.source_path, source_hash: skill.source_hash, text: prepared.blobs.get(main.sha256).toString('utf8') });
  }
  // Every declared ambient source must have an explicit immutable materialization.
  for (const path of skillPolicy.ambient_allow) requireValue(sources.has(skillPathKey(path)), 'SKILL_ALLOW_UNPINNED', 'Ambient allow has no pinned Skill content');
  let baseline = null;
  let audit = null;
  async function verifyFiles() {
    for (const file of files) { await noSymlinks(file.path); const bytes = await readFile(file.path); requireValue(bytes.length <= LIMITS.resource && digest(bytes) === file.sha256, 'SKILL_PIN_CHANGED', 'Owned Skill materialization was modified'); }
  }
  async function list(client) { return skillInventory(await client.call('skills/list', { cwds: [cwd], forceReload: true }), cwd); }
  function validateAllowed(skills) {
    const enabled = skills.filter(skill => skill.enabled).map(skill => skillPathKey(skill.path)).sort();
    requireValue(canonicalJSON(enabled) === canonicalJSON([...pins.keys()].sort()), 'SKILL_ISOLATION_FAILED', 'Actual enabled catalog differs from the exact pinned allow set');
  }
  return {
    async apply(client) {
      const discovered = await list(client);
      requireValue(!discovered.some(skill => skill.scope === 'admin'), 'SKILL_SCOPE_UNQUALIFIED', 'Administrative Skill scope requires separate executor qualification');
      for (const skill of discovered) await client.call('skills/config/write', { path: skill.path, enabled: pins.has(skillPathKey(skill.path)) });
      const after = await list(client); validateAllowed(after); await verifyFiles();
      baseline = canonicalJSON(after);
      audit = { discovered_skills: discovered, allowed_skills: [...pins.values()].map(({ text, ...pin }) => pin), shadowed_skills: [...shadows], disabled_skills: after.filter(skill => !skill.enabled).map(skill => skill.path), uncontrolled_system_skills: [], inventory_hash: digest(baseline) };
      return structuredClone(audit);
    },
    async verify(client) {
      requireValue(baseline !== null, 'SKILL_POLICY_NOT_APPLIED', 'Apply Skill policy before creating any thread');
      const current = await list(client); validateAllowed(current);
      requireValue(canonicalJSON(current) === baseline, 'SKILL_DISCOVERY_CHANGED', 'Skill catalog changed after preparation'); await verifyFiles();
    },
    explicitInputs(sourcePaths) {
      return sourcePaths.map(sourcePath => {
        const source = skillPathKey(sourcePath); const pin = [...pins.values()].find(item => skillPathKey(item.source_path) === source);
        requireValue(pin && !shadows.has(source), 'SKILL_INJECTION_DENIED', 'Explicit input is outside this node Skill policy');
        return { type: 'skill', name: pin.name, path: pin.path };
      });
    },
    tools() { return pins.size ? [{ name: 'read_allowed_skill', description: 'Read the immutable instructions of an explicitly allowed Skill. No other path can be read.', inputSchema: { type: 'object', properties: { path: { type: 'string', enum: [...pins.values()].map(pin => pin.path) } }, required: ['path'], additionalProperties: false } }] : []; },
    read(args) {
      requireValue(args && Object.keys(args).length === 1 && typeof args.path === 'string', 'SKILL_READ_ARGS', 'Skill read requires one exact path');
      const pin = pins.get(skillPathKey(args.path)); requireValue(pin, 'SKILL_READ_DENIED', 'Skill read path is outside the pinned allow set');
      return { success: true, contentItems: [{ type: 'inputText', text: pin.text }] };
    },
    audit: () => structuredClone(audit),
  };
}
