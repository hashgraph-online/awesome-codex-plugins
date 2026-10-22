import { requireValue } from './workflow-paths.mjs';
import { skillPathKey } from './execution/codex-skill-policy.mjs';

const sha = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
export function effectiveSkillPolicy(parent, requested = parent) {
  requireValue(parent && requested && ['strict', 'cooperative'].includes(parent.mode) && ['strict', 'cooperative'].includes(requested.mode) &&
    ['allow', 'deny'].includes(parent.implicit) && ['allow', 'deny'].includes(requested.implicit) && !(parent.implicit === 'deny' && requested.implicit !== 'deny') &&
    !(parent.mode === 'strict' && requested.mode !== 'strict') && (requested.mode !== 'strict' || requested.implicit === 'deny'), 'SKILL_POLICY_ESCALATION', 'A node or child cannot weaken its parent Skill isolation');
  requireValue(Array.isArray(parent.ambient_allow) && Array.isArray(parent.shadowed_skill_paths) && Array.isArray(requested.ambient_allow) && Array.isArray(requested.shadowed_skill_paths), 'SKILL_POLICY', 'Skill policy requires explicit path sets');
  const ceiling = new Set(parent.ambient_allow.map(skillPathKey));
  requireValue(requested.ambient_allow.every(path => ceiling.has(skillPathKey(path))), 'SKILL_POLICY_ESCALATION', 'A node or child cannot expand its parent ambient Skill allowance');
  const shadows = new Map([...parent.shadowed_skill_paths, ...requested.shadowed_skill_paths].map(path => [skillPathKey(path), path]));
  requireValue(requested.ambient_allow.every(path => !shadows.has(skillPathKey(path))), 'SKILL_POLICY_CONFLICT', 'A Skill cannot be both allowed and shadowed');
  return { mode: requested.mode, implicit: requested.implicit, ambient_allow: [...requested.ambient_allow], shadowed_skill_paths: [...shadows.values()] };
}

export function validateSkillReference(reference) {
  requireValue(reference && typeof reference === 'object' && !Array.isArray(reference), 'SKILL_REFERENCE', 'SkillRef requires a complete source pin');
  skillPathKey(reference.path);
  requireValue(typeof reference.name === 'string' && reference.name && reference.name.length <= 256 && sha(reference.source_hash) &&
    (reference.expected_version === undefined || typeof reference.expected_version === 'string') &&
    Array.isArray(reference.allowed_nested_skills) && reference.allowed_nested_skills.length <= 32, 'SKILL_REFERENCE', 'SkillRef requires name/hash/version and explicit nested Skill pins');
  const seen = new Set([skillPathKey(reference.path)]);
  for (const child of reference.allowed_nested_skills) {
    requireValue(child && typeof child === 'object' && !Array.isArray(child) && typeof child.name === 'string' && child.name && sha(child.source_hash) &&
      (child.expected_version === undefined || typeof child.expected_version === 'string') && !child.allowed_nested_skills, 'SKILL_NESTED_REFERENCE', 'Nested Skills need explicit flat path/name/hash/version pins');
    const key = skillPathKey(child.path); requireValue(!seen.has(key), 'SKILL_NESTED_REFERENCE', 'Nested Skill paths cannot duplicate the root or another allowance'); seen.add(key);
  }
  return reference;
}
