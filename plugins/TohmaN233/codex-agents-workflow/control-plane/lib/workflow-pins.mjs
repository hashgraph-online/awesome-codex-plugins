import { readFile, lstat } from 'node:fs/promises';
import { join } from 'node:path';
import { WorkflowStore } from './workflow-store.mjs';
import { requireValue, noSymlinks } from './workflow-paths.mjs';
import { digest, canonicalJSON, prepareResources } from './workflow-revisions.mjs';
import { skillPathKey } from './execution/codex-skill-policy.mjs';
import { readSkillSnapshot } from './skill-import/skill-reader.mjs';
import { analyzeSkillDependencies } from './skill-import/dependency-reader.mjs';
import { validateSkillReference } from './workflow-reference-schema.mjs';
export { validateSkillReference } from './workflow-reference-schema.mjs';

const sha = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);

// Resolve the entire immutable closure before publishing a Run. Linked sources
// are consulted only here; resumed execution must consume these content pins.
export async function resolveWorkflowPins(store, root, { rootResources } = {}) {
  requireValue(store instanceof WorkflowStore, 'WORKFLOW_PIN_STORE', 'Pin resolution requires the authoritative Workflow store');
  const children = Object.create(null); const skills = new Map(); const blobs = new Map(); const packs = [root];
  const workflowContext = Object.create(null); const dependencyObservations = [];
  const sourceChecks = [];
  let total = 0;
  function addBlob(hash, bytes) {
    if (blobs.has(hash)) return;
    total += bytes.length; requireValue(total <= 256 * 1024 * 1024 && blobs.size < 2048 && digest(bytes) === hash, 'RUN_CLOSURE_LIMIT', 'Workflow closure resources exceed limits or differ from their pins'); blobs.set(hash, bytes);
  }
  async function pinSkill(path, expected) {
    const key = skillPathKey(path);
    if (!skills.has(key)) {
      requireValue(skills.size < 128, 'RUN_SKILL_LIMIT', 'Workflow closure contains too many Skills');
      const snapshot = await readSkillSnapshot(path, { expectedSourceHash: expected?.source_hash });
      sourceChecks.push({ path: snapshot.source_path, hash: snapshot.source_hash });
      for (const resource of snapshot.inventory) sourceChecks.push({ path: join(snapshot.root, ...resource.path.split('/')), hash: resource.source_sha256 });
      requireValue(snapshot.problems.length === 0 && digest(snapshot.files['source/SKILL.md']) === snapshot.source_hash, 'SKILL_PIN_INCOMPLETE', 'Linked Skill cannot execute a redacted, omitted or partial snapshot', { path, problems: snapshot.problems });
      const files = Object.fromEntries(Object.entries(snapshot.files).map(([path, bytes]) => [path.slice('source/'.length), bytes]));
      const prepared = prepareResources(files); for (const [hash, bytes] of prepared.blobs) addBlob(hash, bytes);
      const dependencies = analyzeSkillDependencies(snapshot);
      const pin = { path: snapshot.source_path, name: snapshot.metadata.name, source_hash: snapshot.source_hash, version: snapshot.metadata.version ?? null,
        resources: prepared.manifest, requirements: dependencies.requirements, observations: dependencies.unresolved };
      skills.set(key, pin); dependencyObservations.push({ path: pin.path, requirements: pin.requirements, observations: pin.observations });
    }
    const pin = skills.get(key);
    if (expected) requireValue(pin.source_hash === expected.source_hash && pin.name === expected.name && (expected.expected_version === undefined || pin.version === expected.expected_version), 'SKILL_STALE', 'Linked Skill name/content/version differs from its saved pin', { path });
    return pin;
  }
  async function visit(pack, ancestry) {
    requireValue(ancestry.length <= 32 && packs.length <= 128, 'SUBWORKFLOW_DEPTH', 'Workflow closure exceeds nesting or pack count limits');
    const resources = pack === root && rootResources !== undefined ? rootResources : await store.resources(pack.workflow.id, pack.revision_hash);
    for (const resource of pack.resources) addBlob(resource.sha256, resources[resource.path]);
    for (const path of pack.workflow.skill_policy.ambient_allow) await pinSkill(path);
    for (const node of pack.workflow.nodes) {
      if (node.type === 'skill_ref') {
        validateSkillReference(node.skill_ref); await pinSkill(node.skill_ref.path, node.skill_ref);
        for (const nested of node.skill_ref.allowed_nested_skills) await pinSkill(nested.path, nested);
      }
      if (node.type !== 'subworkflow') continue;
      const reference = node.subworkflow;
      requireValue(reference?.workflow_id && sha(reference.revision_pin), 'SUBWORKFLOW_REFERENCE', 'SubWorkflow needs an exact revision');
      requireValue(!ancestry.includes(reference.workflow_id), 'SUBWORKFLOW_CYCLE', 'Workflow closure contains recursive references');
      const id = reference.workflow_id + '@' + reference.revision_pin;
      if (Object.hasOwn(children, id)) continue;
      const child = await store.snapshot(reference.workflow_id, reference.revision_pin);
      children[id] = child; workflowContext[id] = child.workflow; packs.push(child);
      await visit(child, [...ancestry, reference.workflow_id]);
    }
  }
  await visit(root, [root.workflow.id]);
  // Reused immutable children still need ancestry checks at every call site.
  // A different revision of an ancestor is recursive by Workflow identity too.
  const checkedContexts = new Set();
  function checkAncestry(pack, ancestry) {
    const contextKey = pack.revision_hash + canonicalJSON([...ancestry].sort());
    if (checkedContexts.has(contextKey)) return;
    requireValue(ancestry.length <= 32 && checkedContexts.size < 4096, 'SUBWORKFLOW_CONTEXT_LIMIT', 'Workflow ancestry validation exceeds its bounded context count');
    checkedContexts.add(contextKey);
    for (const node of pack.workflow.nodes.filter(node => node.type === 'subworkflow')) {
      const reference = node.subworkflow;
      requireValue(!ancestry.includes(reference.workflow_id), 'SUBWORKFLOW_CYCLE', 'Reused child references an ancestor Workflow identity');
      checkAncestry(children[reference.workflow_id + '@' + reference.revision_pin], [...ancestry, reference.workflow_id]);
    }
  }
  checkAncestry(root, [root.workflow.id]);
  // Hash verification at the end rejects a source changed during closure loading.
  for (const check of sourceChecks) {
    await noSymlinks(check.path); const stat = await lstat(check.path);
    requireValue(stat.isFile() && stat.nlink === 1 && stat.size <= 8 * 1024 * 1024 && digest(await readFile(check.path)) === check.hash, 'SKILL_SOURCE_CHANGED', 'Skill resource changed while preparing the Workflow closure', { path: check.path });
  }
  const orderedSkills = [...skills.values()].sort((a, b) => skillPathKey(a.path).localeCompare(skillPathKey(b.path), 'en'));
  const providerIds = new Set(packs.flatMap(pack => pack.workflow.nodes.filter(node => ['provider', 'thread'].includes(node.executor?.kind)).map(node => node.executor.provider_id)));
  const resourcePins = [...blobs].map(([sha256, bytes]) => ({ sha256, bytes: bytes.length })).sort((a, b) => a.sha256.localeCompare(b.sha256, 'en'));
  requireValue(Buffer.byteLength(canonicalJSON({ root, children, skills: orderedSkills })) <= 16 * 1024 * 1024, 'RUN_PINS_LIMIT', 'Workflow closure metadata exceeds the Run limit');
  return { children, skills: orderedSkills, resources: resourcePins, blobs, provider_ids: [...providerIds], packs, dependency_observations: dependencyObservations,
    context: { workflows: workflowContext, skills: orderedSkills.map(pin => ({ path: pin.path, name: pin.name, source_hash: pin.source_hash, version: pin.version })) } };
}
