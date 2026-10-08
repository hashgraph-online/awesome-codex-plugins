import { requireValue, resourcePath } from './workflow-paths.mjs';
import { digest } from './workflow-revisions.mjs';
import { certificateForPublishedWorkflow, conversionResourceHash, conversionWorkflowHash } from './skill-import/conversion-certificate.mjs';

export async function readEditorResource(store, { workflow_id, revision_hash, resource_path }) {
  resourcePath(resource_path); const pack = await store.snapshot(workflow_id, revision_hash);
  const resource = pack.resources.find(item => item.path === resource_path); requireValue(resource, 'RESOURCE_MISSING', 'Resource does not exist in this revision');
  const bytes = (await store.resources(workflow_id, pack.revision_hash))[resource_path];
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { return { ...resource, encoding: 'base64', content: bytes.toString('base64'), editable: false }; }
  return { ...resource, encoding: 'utf8', content: text, editable: bytes.length <= 1024 * 1024 };
}

export async function writeEditorResource(store, { workflow_id, expected_revision, resource_path, text, remove = false }) {
  resourcePath(resource_path); requireValue(typeof remove === 'boolean' && (remove || typeof text === 'string' && Buffer.byteLength(text) <= 1024 * 1024), 'RESOURCE_EDIT_SCHEMA', 'Resource edits require bounded UTF-8 text or explicit removal');
  const pack = await store.snapshot(workflow_id, expected_revision); const resources = await store.resources(workflow_id, pack.revision_hash);
  if (remove) requireValue(Object.hasOwn(resources, resource_path), 'RESOURCE_MISSING', 'Only an existing resource can be removed');
  const before = resources[resource_path] ? digest(resources[resource_path]) : null;
  if (remove) delete resources[resource_path]; else resources[resource_path] = Buffer.from(text);
  const workflow = structuredClone(pack.workflow); workflow.status = 'draft';
  const after = remove ? null : digest(resources[resource_path]);
  return store.save(workflow_id, workflow, { expected_revision, resources,
    provenance: { ...pack.provenance, last_resource_edit: { source_revision: expected_revision, path: resource_path, before_sha256: before, after_sha256: after } } });
}

export function publishableEditorWorkflow(workflow) {
  const publishable=structuredClone(workflow);
  // Old Drafts may carry this former review-only resource observation.
  if(publishable.import_status)publishable.import_status.unresolved=publishable.import_status.unresolved.filter(item=>item.code!=='RESOURCE_EDIT_REQUIRES_REVIEW');
  return publishable;
}

export async function publishEditorWorkflow(store, { workflow_id, expected_revision }) {
  const pack = await store.snapshot(workflow_id, expected_revision);
  const workflow=publishableEditorWorkflow(pack.workflow);
  const import_report=certificateForPublishedWorkflow({...pack,workflow});
  const provenance={...pack.provenance};
  delete provenance.host_binding_renewal;
  provenance.publication={kind:'direct_editor_publication',actor:'workflow_controller',draft_revision:expected_revision,
    workflow_hash:conversionWorkflowHash(workflow),resources_hash:conversionResourceHash(pack.resources),at:new Date().toISOString()};
  return store.save(workflow_id, { ...workflow, status: 'ready' }, { expected_revision,
    import_report,provenance });
}
