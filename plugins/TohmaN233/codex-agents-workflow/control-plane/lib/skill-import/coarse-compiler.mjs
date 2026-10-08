import { createDraft } from '../workflow-schema.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { digest, canonicalJSON, prepareResources } from '../workflow-revisions.mjs';
import { readSkillSnapshot } from './skill-reader.mjs';
import { analyzeSkillDependencies } from './dependency-reader.mjs';

export const COARSE_FINAL_PROMPT = 'Review the node result against the pinned source Skill and the user task {{task}}. Verify evidence and explicitly accept or reject the complete Workflow. Only the main controller can grant final acceptance.';

export function compileCoarseSkill(snapshot, { id, name = snapshot.metadata.name, providerId, role = 'advisor' } = {}) {
  const analysis = analyzeSkillDependencies(snapshot); const workflow = createDraft(id, name);
  workflow.skill_policy.mode = 'cooperative'; workflow.skill_policy.implicit = 'allow';
  workflow.description = snapshot.metadata.description.slice(0, 4000);
  workflow.skill_policy.shadowed_skill_paths = [snapshot.source_path];
  workflow.requirements = analysis.requirements;
  if (providerId) workflow.requirements.providers = [providerId];
  workflow.import_status = { mode: 'coarse', source_hash: snapshot.source_hash, classification: analysis.classification,
    unresolved: analysis.unresolved, source_independent: false, relocation_evidence: null };
  const shared = { access: 'read_only', approval: { required: false }, retry: { max_attempts: 3 }, input_bindings: { task: '/inputs/task' } };
  workflow.nodes = [
    { id: 'start', type: 'start' },
    { ...shared, access: 'bounded_write', path_scope:{binding:'run.allowed_paths'}, id: 'instructions', type: 'agent', role, executor: providerId ? { kind: 'provider', provider_id: providerId } : { kind: 'main' },
      prompt_template: 'Read the pinned Workflow resource source/SKILL.md using read_workflow_resource and apply its complete instructions to this task: {{task}}. Resolve its local references within the pinned source/ resources. Report unmet requirements instead of inventing tools or accessing the original Skill.',
      resources: Object.keys(snapshot.files).sort(), origin: { kind: 'source', source_span: { resource: 'source/SKILL.md', start_line: snapshot.instructions_start_line, end_line: snapshot.files['source/SKILL.md'].toString().split('\n').length } } },
    { ...shared, id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' }, input_bindings: { task: '/inputs/task', instruction_result: '/nodes/instructions/output' },
      prompt_template: COARSE_FINAL_PROMPT, resources: Object.keys(snapshot.files).sort() },
    { id: 'end', type: 'end' },
  ];
  workflow.edges = [['start', 'instructions'], ['instructions', 'final'], ['final', 'end']].map(([source, target]) => ({ id: source + '-' + target, source, target }));
  workflow.finalization.node_id = 'final';
  return { workflow, resources: snapshot.files,
    provenance: { kind: 'skill_import', compiler_version: 4, source_path: snapshot.source_path, source_hash: snapshot.source_hash,
      source_license: snapshot.metadata.license ?? null, source_metadata: snapshot.metadata, metadata_files: snapshot.metadata_files },
    import_report: { mode: 'coarse', calls_to_models: 0, scripts_executed: 0, ...analysis, resource_inventory: snapshot.inventory, problems: snapshot.problems,
      notes: ['Credential screening detects known forms only; it is not proof that arbitrary assets contain no sensitive data.', 'Static dependency observations do not prove script behavior or portability.'] },
  };
}

export async function importCoarseSkill(store, sourcePath, options) {
  const snapshot = await readSkillSnapshot(sourcePath, options);
  const compiled = compileCoarseSkill(snapshot, options);
  return store.create(compiled.workflow, compiled);
}

// Relocation checks read only immutable Pack bytes. The source directory is not
// consulted and no imported program runs. Only a dependency-free text Pack can
// earn this narrowly defined resource/instruction independence claim.
export function verifyCoarseRelocation(pack, resources) {
  requireValue(pack.workflow.import_status?.mode === 'coarse', 'IMPORT_KIND', 'Relocation verification requires a coarse import');
  requireValue(!pack.workflow.import_status.unresolved.length, 'IMPORT_UNRESOLVED', 'Resolve every import observation before claiming source independence');
  requireValue(!(pack.import_report?.references ?? []).some(r=>r.kind==='external') && !(pack.import_report?.observed_dependencies ?? []).length && !pack.workflow.requirements.executables.length && !(pack.workflow.requirements.environment ?? []).length && !pack.workflow.requirements.mcp_servers.length && pack.workflow.requirements.tools.every(tool => tool === 'read_workflow_resource'), 'IMPORT_EXTERNAL_REQUIREMENTS', 'External requirements or unresolved dependency observations prevent a self-contained claim');
  const prepared = prepareResources(resources);
  requireValue(canonicalJSON(prepared.manifest) === canonicalJSON(pack.resources), 'IMPORT_RESOURCE_CHANGED', 'Relocated resources differ from the pinned Pack');
  requireValue(resources['source/SKILL.md'], 'IMPORT_SOURCE_MISSING', 'Pinned source instructions are missing');
  return { kind: 'coarse-resource-relocation', source_revision: pack.revision_hash, manifest_sha256: digest(canonicalJSON(prepared.manifest)),
    files_verified: prepared.manifest.length, original_source_read: false, scripts_executed: 0, source_independent: true,
    scope: 'pinned_resource_access', functional_execution_proven: false };
}
