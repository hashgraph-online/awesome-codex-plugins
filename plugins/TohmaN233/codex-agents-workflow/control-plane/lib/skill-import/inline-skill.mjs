import { validateSkillReference } from '../workflow-reference-schema.mjs';
import { skillPathKey } from '../execution/codex-skill-policy.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { readSkillSnapshot } from './skill-reader.mjs';
import { analyzeSkillDependencies } from './dependency-reader.mjs';
import { normalizeImportedExecutableRequirements } from './metadata-reader.mjs';

// Inline is a reversible definition/resource edit. It never executes Skill code
// and always creates a Draft requiring explicit review of the conversion.
export async function inlineSkillReference(store, workflowId, { node_id, expected_revision }) {
  const pack = await store.snapshot(workflowId, expected_revision); const workflow = structuredClone(pack.workflow);
  const node = workflow.nodes.find(item => item.id === node_id);
  requireValue(node?.type === 'skill_ref' && workflow.skill_policy.mode === 'strict', 'INLINE_SKILL_NODE', 'Select one Strict SkillRef node');
  const reference = validateSkillReference(node.skill_ref);
  const resources = await store.resources(workflowId, pack.revision_hash); const paths = []; const sources = []; const observations = [];
  const declarations = { tools: [], mcp_servers: [], executables: [], environment: [] };
  for (const [index, pin] of [reference, ...reference.allowed_nested_skills].entries()) {
    const snapshot = await readSkillSnapshot(pin.path, { expectedSourceHash: pin.source_hash });
    requireValue(snapshot.metadata.name === pin.name && (pin.expected_version === undefined || snapshot.metadata.version === pin.expected_version), 'SKILL_STALE', 'Inline source name/version differs from its pin');
    const prefix = `inline/${node_id}/${index === 0 ? 'root' : 'nested-' + index}/`;
    for (const [path, bytes] of Object.entries(snapshot.files)) {
      const target = prefix + path.slice('source/'.length);
      requireValue(!Object.hasOwn(resources, target), 'INLINE_RESOURCE_CONFLICT', 'Inline resources would replace an existing resource'); resources[target] = bytes; paths.push(target);
    }
    const analysis = analyzeSkillDependencies(snapshot);
    for (const kind of Object.keys(declarations)) declarations[kind].push(...analysis.requirements[kind]);
    observations.push(...analysis.unresolved.map(issue => ({ ...issue, inline_node_id: node_id, inline_source: pin.path })));
    sources.push({ path: pin.path, name: pin.name, source_hash: pin.source_hash, resource_prefix: prefix });
  }
  const mapPath = `inline/${node_id}/map.json`;
  requireValue(!Object.hasOwn(resources, mapPath), 'INLINE_RESOURCE_CONFLICT', 'Inline source map would replace an existing resource');
  resources[mapPath] = canonicalJSON(sources.map(({ path, ...item }) => item)); paths.push(mapPath);
  node.type = 'agent'; delete node.skill_ref;
  node.resources = [...new Set([...(node.resources ?? []), ...paths])];
  node.prompt_template = `Read the complete pinned instructions at inline/${node_id}/root/SKILL.md with read_workflow_resource and apply them to {{task}}. Resolve relative files within that resource prefix. Read inline/${node_id}/map.json for any explicitly included nested Skill resources; do not read original Skill paths.`;
  node.origin = { kind: 'inlined_skill', sources, reviewed: false };
  node.skill_policy = { mode: 'strict', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: sources.map(source => source.path) };
  const usedElsewhere = new Set(workflow.nodes.filter(item => item.type === 'skill_ref').flatMap(item => [item.skill_ref.path, ...item.skill_ref.allowed_nested_skills.map(pin => pin.path)]).map(skillPathKey));
  const converted = new Set(sources.map(source => skillPathKey(source.path)));
  if (!workflow.nodes.some(item => item.type === 'subworkflow')) workflow.skill_policy.ambient_allow = workflow.skill_policy.ambient_allow.filter(path => !converted.has(skillPathKey(path)) || usedElsewhere.has(skillPathKey(path)));
  for (const source of sources) if (!usedElsewhere.has(skillPathKey(source.path)) && !workflow.skill_policy.ambient_allow.some(path => skillPathKey(path) === skillPathKey(source.path))) workflow.skill_policy.shadowed_skill_paths.push(source.path);
  workflow.skill_policy.shadowed_skill_paths = [...new Map(workflow.skill_policy.shadowed_skill_paths.map(path => [skillPathKey(path), path])).values()];
  for (const [kind, names] of Object.entries(declarations)) workflow.requirements[kind] = kind === 'executables'
    ? normalizeImportedExecutableRequirements([...(workflow.requirements[kind] ?? []), ...names])
    : [...new Set([...(workflow.requirements[kind] ?? []), ...names])].sort();
  workflow.import_status ??= { mode: 'coarse', source_hash: reference.source_hash, classification: 'self_contained_candidate', source_independent: false, relocation_evidence: null, unresolved: [] };
  workflow.import_status.unresolved.push(...observations, { code: 'INLINE_SKILL_REQUIRES_REVIEW', node_id, origin: 'observed' });
  if (observations.some(issue => issue.code === 'SOURCE_LINKED_PATH')) workflow.import_status.classification = 'source_linked';
  else if (workflow.import_status.classification !== 'source_linked' && (observations.length || Object.entries(declarations).some(([kind, names]) => names.some(name => kind !== 'tools' || name !== 'read_workflow_resource')))) workflow.import_status.classification = 'external_requirements';
  workflow.import_status.source_independent = false; workflow.import_status.relocation_evidence = null; workflow.status = 'draft';
  return store.save(workflowId, workflow, { expected_revision, resources, import_report: { ...pack.import_report,
    inline_history: [...(pack.import_report?.inline_history ?? []), { node_id, source_revision: pack.revision_hash, sources, scripts_executed: 0 }] } });
}
