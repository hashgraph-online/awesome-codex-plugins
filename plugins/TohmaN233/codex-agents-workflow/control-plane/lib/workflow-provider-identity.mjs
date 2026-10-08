import { canonicalNativeProviderId } from './native-provider-identity.mjs';
import { certificateForPublishedWorkflow } from './skill-import/conversion-certificate.mjs';

function replaceProvider(holder, key, path, changes) {
  const before = holder?.[key];
  if (typeof before !== 'string') return;
  const after = canonicalNativeProviderId(before);
  if (after === before) return;
  holder[key] = after;
  changes.push({ path, from: before, to: after });
}

export function canonicalizeWorkflowProviderIds(workflow) {
  const migrated = structuredClone(workflow);
  const changes = [];
  if (Array.isArray(migrated.requirements?.providers)) {
    migrated.requirements.providers = [...new Set(migrated.requirements.providers.map((providerId, index) => {
      const canonical = canonicalNativeProviderId(providerId);
      if (canonical !== providerId) changes.push({ path: `requirements.providers[${index}]`, from: providerId, to: canonical });
      return canonical;
    }))];
  }
  for (const node of migrated.nodes ?? []) {
    replaceProvider(node.executor, 'provider_id', `nodes.${node.id}.executor.provider_id`, changes);
    replaceProvider(node, 'authoring_reviewer_provider_id', `nodes.${node.id}.authoring_reviewer_provider_id`, changes);
  }
  replaceProvider(migrated.authoring, 'planner_provider_id', 'authoring.planner_provider_id', changes);
  replaceProvider(migrated.authoring, 'review_provider_id', 'authoring.review_provider_id', changes);
  return { workflow: migrated, changes };
}

export async function migrateStoredWorkflowProviderIds(store) {
  const migrations = [];
  for (const pack of await store.list()) {
    const migrated = canonicalizeWorkflowProviderIds(pack.workflow);
    if (!migrated.changes.length) continue;
    const importReport = certificateForPublishedWorkflow({ ...pack, workflow: migrated.workflow });
    const saved = await store.save(pack.workflow.id, migrated.workflow, {
      expected_revision: pack.revision_hash,
      import_report: importReport,
    });
    migrations.push({
      workflow_id: pack.workflow.id,
      from_revision: pack.revision_hash,
      to_revision: saved.revision_hash,
      changes: migrated.changes,
    });
  }
  return migrations;
}
