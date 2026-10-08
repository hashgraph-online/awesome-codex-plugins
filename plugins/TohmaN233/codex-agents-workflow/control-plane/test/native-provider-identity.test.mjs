import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';
import { tmpdir } from './physical-tempdir.mjs';

import { canonicalizeRoutingProviderIds } from '../lib/native-provider-identity.mjs';
import { canonicalizeWorkflowProviderIds, migrateStoredWorkflowProviderIds } from '../lib/workflow-provider-identity.mjs';
import { loadRoutingSettings } from '../lib/skill-import/routing-settings.mjs';

const legacyRules = () => ({
  version: 1,
  instructions: 'Use the configured routes.',
  selection_mode: 'automatic',
  routes: {
    implementation: { provider_id: 'native-luna', role: 'implementer' },
    complex_implementation: { provider_id: 'native-terra', role: 'implementer' },
    review: { provider_id: 'native-reviewer-low', role: 'reviewer' },
    planning: { provider_id: 'native-authoring-astra-low', role: 'implementer' },
  },
  generation: {
    planner_provider_id: 'native-authoring-astra-low',
    review_provider_id: 'native-reviewer-low',
    max_rounds: 3,
  },
});

test('routing Provider identity migration is exact and does not mutate its input', () => {
  const input = legacyRules();
  const migrated = canonicalizeRoutingProviderIds(input);
  assert.equal(input.routes.complex_implementation.provider_id, 'native-terra');
  assert.deepEqual({
    complex: migrated.routes.complex_implementation.provider_id,
    review: migrated.routes.review.provider_id,
    planning: migrated.routes.planning.provider_id,
    planner: migrated.generation.planner_provider_id,
    generationReview: migrated.generation.review_provider_id,
  }, {
    complex: 'native-sol',
    review: 'native-sol',
    planning: 'native-astra',
    planner: 'native-astra',
    generationReview: 'native-sol',
  });
});

test('persisted routing settings expose only canonical Provider IDs', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'routing-provider-migration-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  await writeFile(join(directory, 'skill2workflow-rules.json'), JSON.stringify(legacyRules()), 'utf8');
  const loaded = await loadRoutingSettings(directory, []);
  assert.equal(JSON.stringify(loaded).includes('native-terra'), false);
  assert.equal(JSON.stringify(loaded).includes('native-reviewer-low'), false);
  assert.equal(JSON.stringify(loaded).includes('native-authoring-astra-low'), false);
});

test('stored Workflow bindings collapse retired purpose aliases without mutating the source', async () => {
  const source = {
    id: 'provider-migration-fixture',
    requirements: { providers: ['native-luna-complex', 'native-luna-planner', 'native-generation-reviewer'] },
    authoring: { planner_provider_id: 'native-luna-planner', review_provider_id: 'native-generation-reviewer' },
    nodes: [
      { id: 'plan', executor: { kind: 'provider', provider_id: 'native-luna-planner' } },
      { id: 'work', executor: { kind: 'thread', provider_id: 'native-luna-complex' } },
      { id: 'final', executor: { kind: 'main' }, authoring_reviewer_provider_id: 'native-generation-reviewer' },
    ],
  };
  const migrated = canonicalizeWorkflowProviderIds(source);
  assert.deepEqual(source.requirements.providers, ['native-luna-complex', 'native-luna-planner', 'native-generation-reviewer']);
  assert.deepEqual(migrated.workflow.requirements.providers, ['native-sol', 'native-astra']);
  assert.equal(migrated.workflow.nodes[0].executor.provider_id, 'native-astra');
  assert.equal(migrated.workflow.nodes[1].executor.provider_id, 'native-sol');
  assert.equal(migrated.workflow.nodes[2].authoring_reviewer_provider_id, 'native-sol');
  assert.equal(migrated.workflow.authoring.planner_provider_id, 'native-astra');
  assert.equal(migrated.workflow.authoring.review_provider_id, 'native-sol');
  assert.equal(migrated.changes.length, 8);

  const saves = [];
  const pack = { workflow: source, revision_hash: 'a'.repeat(64), resources: [], provenance: {}, import_report: {} };
  const store = {
    list: async () => [pack, { ...pack, workflow: migrated.workflow, revision_hash: 'b'.repeat(64) }],
    save: async (id, workflow, options) => {
      saves.push({ id, workflow, options });
      return { revision_hash: 'c'.repeat(64) };
    },
  };
  const persisted = await migrateStoredWorkflowProviderIds(store);
  assert.equal(saves.length, 1);
  assert.equal(saves[0].id, source.id);
  assert.equal(saves[0].options.expected_revision, pack.revision_hash);
  assert.deepEqual(saves[0].workflow.requirements.providers, ['native-sol', 'native-astra']);
  assert.equal(persisted[0].to_revision, 'c'.repeat(64));
});
