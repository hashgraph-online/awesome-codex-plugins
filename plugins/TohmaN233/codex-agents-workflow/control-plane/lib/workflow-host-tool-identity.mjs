import { authoringHostToolContracts } from './execution/authoring-host-tools.mjs';
import { workflowResourceProgramIdentity } from './execution/workflow-resource-program.mjs';
import { canonicalJSON, revisionHash } from './workflow-revisions.mjs';
import { requireValue } from './workflow-paths.mjs';
import { certificateForPublishedWorkflow } from './skill-import/conversion-certificate.mjs';
import { exportWorkflowPackage, validateWorkflowPackage } from './workflow-package.mjs';

// Exact identities shipped before source newline canonicalization, in LF and
// CRLF checkout form. These are migration evidence, never execution grants.
const previous = new Map([
  ['workflow-resource-program', { version: '1', hashes: [
    '38c9435bfec1e03827a2279ee0829a1bb6cb821b455a635ee637c00da38f97a0',
    'b185499be50c3f6a12c1fc1f2ba533bec45c7ce47a4ca1a76698790bbf6b6f81'] }],
  ['authoring-graph-assembly', { version: '1.0.0', hashes: [
    '36767b11957d25aec4c24172c067378a5747f6a61e81f8d76383e747b46df49c',
    'ed08752e38a08d205284f3fbaedcf0fa9c8e85ea434c02ce2fd672a5d5bfb62f'] }],
  ['authoring-execution-binding', { version: '1.0.0', hashes: [
    'cb7042b94a55f68645c3f71be741c67e20deeeb4ed2fa703b334cf112b688af5',
    '91156e90995abb6d86783a7725125fd0ed5f88f44602b50d1e983a847cdacd86'] }],
  ['authoring-deterministic-validation', { version: '1.0.0', hashes: [
    '885511b02f8f1f1108b502c5905b8e3080e570e35e0369a17355f6481c3ec39f',
    '827f5c334209a2937e42000223b827a7af7c9ba5acba4f024308d4c07f318553'] }],
]);

export function rebindBuiltinHostToolIdentities(workflow) {
  const current = new Map([workflowResourceProgramIdentity(), ...authoringHostToolContracts().map(tool => tool.identity)]
    .map(identity => [identity.name, identity]));
  const next = structuredClone(workflow), changes = [];
  for (const contract of next.host_tools ?? []) {
    const identity = contract.identity, target = current.get(identity?.name);
    if (!target || canonicalJSON(identity) === canonicalJSON(target)) continue;
    const known = previous.get(identity.name);
    requireValue(Object.keys(identity).length === 3 && identity.version === known.version && known.hashes.includes(identity.sha256),
      'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED', `Unknown prior built-in Host implementation: ${identity.name}`, { host_tool_id: contract.id, identity });
    changes.push({ host_tool_id: contract.id, from: structuredClone(identity), to: structuredClone(target) });
    contract.identity = structuredClone(target);
  }
  return { workflow: next, changes };
}

export async function migrateStoredWorkflowHostToolIdentities(store) {
  const migrations = [];
  for (const pack of await store.list()) {
    let rebound;
    try { rebound = rebindBuiltinHostToolIdentities(pack.workflow); }
    catch (error) {
      if (error.code !== 'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED') throw error;
      // An unavailable implementation fences only this Workflow. Preserve its
      // head and report the exact refusal; execution still validates its pin.
      migrations.push({ status: 'blocked', workflow_id: pack.workflow.id, revision_hash: pack.revision_hash,
        code: error.code, message: error.message, host_tool_id: error.host_tool_id, identity: structuredClone(error.identity) });
      continue;
    }
    const { workflow, changes } = rebound;
    if (!changes.length) continue;
    const provenance = { ...pack.provenance, host_tool_identity_migration: { kind: 'builtin_host_tool_identity', changes } };
    const saved = await store.save(pack.workflow.id, workflow, { expected_revision: pack.revision_hash, provenance,
      import_report: certificateForPublishedWorkflow({ ...pack, workflow }) });
    migrations.push({ workflow_id: pack.workflow.id, from_revision: pack.revision_hash, to_revision: saved.revision_hash, changes });
  }
  return migrations;
}

export function rebindWorkflowPackageHostToolIdentities(bundle) {
  const checked = validateWorkflowPackage(bundle);
  const { workflow, changes } = rebindBuiltinHostToolIdentities(checked.snapshot.workflow);
  if (!changes.length) return { bundle: structuredClone(bundle), changes };
  workflow.revision++;
  const { revision_hash: oldRevision, ...snapshot } = checked.snapshot;
  snapshot.workflow = workflow;
  snapshot.provenance = { ...snapshot.provenance, host_tool_identity_migration: { kind: 'builtin_host_tool_identity', changes,
    from_revision: oldRevision, from_package: checked.package_sha256 } };
  snapshot.import_report = certificateForPublishedWorkflow(snapshot);
  const rebound = exportWorkflowPackage({ ...snapshot, revision_hash: revisionHash(snapshot) }, checked.resources,
    { packageVersion: checked.package.version });
  validateWorkflowPackage(rebound);
  return { bundle: rebound, changes };
}
