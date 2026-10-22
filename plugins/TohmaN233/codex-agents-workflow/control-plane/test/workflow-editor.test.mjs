import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { WorkflowStore } from '../lib/workflow-store.mjs';
import { packDirectory } from '../lib/workflow-paths.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { readEditorResource, writeEditorResource, publishEditorWorkflow } from '../lib/workflow-editor.mjs';
import { canvasIssues, toCanvas, moveNode, connectNodes, removeElements, layoutGraph, renameLoopId } from '../web-src/graph-adapter.mjs';
import { validateWorkflowGraph } from '../lib/workflow-validator.mjs';
import { agent, edge } from './fixtures/workflow-fixtures.mjs';
import { DEFAULT_CONFIG_PATH, startConsole, stopConsole } from '../server.mjs';
import { skillSourceStatus } from '../lib/skill-import/source-status.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'workflow-editor-'));
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const store = await new WorkflowStore(join(root, 'packs')).initialize();
  const workflow = { ...createDraft('editor', 'Editor fixture'), skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, { id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' }, prompt_template: 'Review actual evidence', access: 'read_only', approval: { required: false }, retry: { max_attempts: 1 }, resources: ['instructions/task.md'] }, { id: 'end', type: 'end' }],
    edges: [{ id: 'a', source: 'start', target: 'final' }, { id: 'b', source: 'final', target: 'end' }] };
  const pack = await store.create(workflow, { resources: { 'instructions/task.md': 'Original\n', 'binary.bin': Buffer.from([255,0,1]) } });
  return { root, store, pack };
}
test('resource edits create CAS Draft revisions, retain binary bytes and old resources, and block dangling Ready publication', async t => {
  const { store, pack } = await fixture(t); const ref = { workflow_id: 'editor', expected_revision: pack.revision_hash, resource_path: 'instructions/task.md' };
  assert.equal((await readEditorResource(store, { workflow_id: 'editor', resource_path: 'binary.bin' })).editable, false);
  const changed = await writeEditorResource(store, { ...ref, text: 'Edited\n' });
  assert.equal(changed.workflow.status, 'draft'); assert.equal((await store.resources('editor', pack.revision_hash))['instructions/task.md'].toString(), 'Original\n');
  assert.deepEqual((await store.resources('editor', changed.revision_hash))['binary.bin'], Buffer.from([255,0,1]));
  await assert.rejects(writeEditorResource(store, { ...ref, text: 'Stale' }), { code: 'REVISION_CONFLICT' });
  await assert.rejects(writeEditorResource(store, { ...ref, resource_path: '../escape', text: 'x' }));
  const ready = await publishEditorWorkflow(store, { workflow_id: 'editor', expected_revision: changed.revision_hash }); assert.equal(ready.workflow.status, 'ready');
  const removed = await writeEditorResource(store, { ...ref, expected_revision: ready.revision_hash, remove: true });
  await assert.rejects(publishEditorWorkflow(store, { workflow_id: 'editor', expected_revision: removed.revision_hash }), { code: 'WORKFLOW_RESOURCE_MISSING' });
  const history = await store.revisions('editor'); assert.deepEqual(history.map(item => item.revision), [4,3,2,1]);
  await writeFile(join(packDirectory(store.root, 'editor'), 'revisions', pack.revision_hash + '.json'), '{}');
  await assert.rejects(store.revisions('editor'));
});
test('canvas view and explicit layout preserve opaque domain metadata without persisting React Flow transient state', () => {
  const workflow = { ...createDraft('roundtrip','Round trip'), extension: { retain: [1,2] }, nodes: [{ id: 'a', type: 'start', opaque: { x: true }, ui: { custom: 'preserve' } }, { id: 'b', type: 'end' }], edges: [{ id: 'ab', source: 'a', target: 'b', custom: { keep: true } }] };
  const before = structuredClone(workflow); const canvas = toCanvas(workflow); canvas.nodes[0].selected = true; canvas.nodes[0].measured = { width: 200 }; canvas.nodes[0].data.definition.opaque.x = false;
  assert.deepEqual(workflow, before); const moved = moveNode(workflow, 'a', { x: 180, y: 30 });
  assert.deepEqual(moved.nodes[0], { ...before.nodes[0], ui: { custom: 'preserve', position: { x: 180, y: 30 } } });
  assert.deepEqual(layoutGraph(moved).extension, before.extension); assert.equal(JSON.stringify(moved).includes('measured'), false);
  const connected = connectNodes(moved, 'b', 'a', 'ba'); assert.deepEqual(connected.edges[0], before.edges[0]);
  const removed = removeElements(connected, ['a']); assert.deepEqual(removed.nodes, [before.nodes[1]]); assert.deepEqual(removed.edges, []);
});
test('canvas displays a bounded loop region and round state without adding a graph back edge', () => {
  const workflow = { nodes: [
    { id: 'start', type: 'start', ui: { position: { x: 0, y: 0 } } },
    { id: 'review', type: 'agent', name: 'Review', ui: { position: { x: 100, y: 120 } } },
    { id: 'repair', type: 'agent', name: 'Repair', ui: { position: { x: 410, y: 220 } } },
    { id: 'end', type: 'end', ui: { position: { x: 720, y: 0 } } },
  ], edges: [
    { id: 'a', source: 'start', target: 'review' },
    { id: 'b', source: 'review', target: 'repair' },
    { id: 'c', source: 'repair', target: 'end' },
  ], loops: [{ id: 'review-repair', entry_node: 'review', exit_node: 'repair', node_ids: ['review', 'repair'], max_rounds: 4,
    until: { op: 'eq', args: [{ path: '/loops/review-repair/all_accepted' }, { value: true }] } }] };
  const before = structuredClone(workflow);
  const canvas = toCanvas(workflow, { nodes: { review: { status: 'succeeded' } }, loops: { 'review-repair': { round: 2, status: 'running' } } });
  const region = canvas.nodes.find(node => node.type === 'loopRegion');
  const review = canvas.nodes.find(node => node.id === 'review');
  assert.equal(canvas.edges.length, workflow.edges.length);
  assert.equal(region.data.definition.id, 'review-repair');
  assert.equal(region.data.runtime.round, 2);
  assert.equal(region.data.runtime.status, 'running');
  assert.equal(region.draggable, false); assert.equal(region.connectable, false);
  assert(region.style.width > 500); assert(region.style.height > 200);
  assert.equal(review.data.loopMembership[0].round, 2);
  assert.equal(review.data.loopMembership[0].max_rounds, 4);
  assert.deepEqual(workflow, before);
});
test('canvas reports malformed loop region references instead of crashing during rendering', () => {
  const base = { nodes: [{ id: 'review', type: 'agent' }], edges: [] };
  assert(canvasIssues({ ...base, loops: {} }).length > 0);
  const workflow = { ...base, loops: [{ id: 'bad', node_ids: ['missing'] }] };
  assert(canvasIssues(workflow).length > 0);
  assert.throws(() => toCanvas(workflow));
});
test('loop rename rewrites only exact loop JSON Pointer tokens in binding and expression fields', () => {
  const workflow = {
    nodes: [{ id: 'worker', type: 'agent', input_bindings: {
      direct: '/loops/repair-loop/review_items/0',
      selected: { path: '/loops/repair-loop/feedback/findings', coalesce: ['/inputs/fallback', '/loops/repair-loop/all_accepted'], zip: '/loops/repair-loop/repair_items' },
      literal: { path: '/inputs/value', default: '/loops/repair-loop/all_accepted' },
    }, cases: [{ when: { op: 'and', args: [{ path: '/loops/repair-loop/round' }, { op: 'not', args: [{ path: '/loops/repair-loop/all_accepted' }] }, { value: { path: '/loops/repair-loop/all_accepted' } }] } }],
    prompt_template: 'Keep this prose: /loops/repair-loop/all_accepted and /loops/repair-loop-extra/all_accepted.' }],
    loops: [{ id: 'repair-loop', node_ids: ['worker'], until: { op: 'eq', args: [{ path: '/loops/repair-loop/all_accepted' }, { value: true }] },
      feedback_bindings: { prior: '/loops/repair-loop/review_items' }, item_scope: { items: '/loops/repair-loop/repair_items', verdicts: { path: '/loops/repair-loop/feedback/findings' }, paths_field: 'files' } },
    { id: 'repair-loop-extra', node_ids: ['worker'], until: { op: 'eq', args: [{ value: true }, { value: true }] } }],
    output_bindings: { accepted: '/loops/repair-loop/all_accepted', nested: '/loops/repair-loop-extra/all_accepted' },
  };
  const before = structuredClone(workflow);
  const renamed = renameLoopId(workflow, 'repair-loop', 'review-loop');
  assert.equal(renamed.nodes[0].input_bindings.direct, '/loops/review-loop/review_items/0');
  assert.deepEqual(renamed.nodes[0].input_bindings.selected, { path: '/loops/review-loop/feedback/findings', coalesce: ['/inputs/fallback', '/loops/review-loop/all_accepted'], zip: '/loops/review-loop/repair_items' });
  assert.equal(renamed.nodes[0].input_bindings.literal.default, '/loops/repair-loop/all_accepted');
  assert.deepEqual(renamed.nodes[0].cases[0].when.args, [{ path: '/loops/review-loop/round' }, { op: 'not', args: [{ path: '/loops/review-loop/all_accepted' }] }, { value: { path: '/loops/repair-loop/all_accepted' } }]);
  assert.equal(renamed.nodes[0].prompt_template, before.nodes[0].prompt_template);
  assert.equal(renamed.loops[0].feedback_bindings.prior, '/loops/review-loop/review_items');
  assert.equal(renamed.loops[0].item_scope.items, '/loops/review-loop/repair_items');
  assert.equal(renamed.loops[0].item_scope.verdicts.path, '/loops/review-loop/feedback/findings');
  assert.equal(renamed.loops[1].id, 'repair-loop-extra');
  assert.equal(renamed.output_bindings.accepted, '/loops/review-loop/all_accepted');
  assert.equal(renamed.output_bindings.nested, '/loops/repair-loop-extra/all_accepted');
  assert.deepEqual(workflow, before);
});
test('renaming a compiled item repair loop leaves every Workflow binding valid', () => {
  const workflow = { ...createDraft('loop-rename', 'Loop rename fixture'), status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    finalization: { required: true, node_id: 'final' }, requirements: { providers: ['implementer', 'reviewer'], tools: [], mcp_servers: [], executables: [] },
    inputs_schema: { type: 'object', required: ['items'], properties: { items: { type: 'array', minItems: 1, items: { type: 'object', required: ['files', 'dependencies'], properties: { files: { type: 'array', items: { type: 'string' } }, dependencies: { type: 'array', items: { type: 'string' } } } } } } } };
  const route = { id: 'route', type: 'condition', cases: [{ label: 'repair', when: { op: 'ne', args: [{ path: '/loops/repair-loop/repair_items' }, { value: [] }] } }], default_label: 'review' };
  const repair = { ...agent('repair'), role: 'implementer', executor: { kind: 'provider', provider_id: 'implementer' }, access: 'bounded_write', path_scope: { binding: 'run.allowed_paths' }, input_bindings: { items: '/loops/repair-loop/repair_items' } };
  const verdicts = { type: 'array', minItems: 1, items: { type: 'object', required: ['accepted', 'findings'], additionalProperties: false, properties: { accepted: { type: 'boolean' }, findings: { type: 'string' } } } };
  const review = { ...agent('review'), role: 'reviewer', executor: { kind: 'provider', provider_id: 'reviewer' }, input_bindings: { items: '/loops/repair-loop/review_items' }, outputs_schema: { type: 'object', required: ['verdicts'], additionalProperties: false, properties: { verdicts } } };
  const final = { ...agent('final'), role: 'finalizer', input_bindings: { feedback: '/loops/repair-loop/feedback/findings', sibling: '/loops/repair-loop-extra/all_accepted' } };
  workflow.nodes = [{ id: 'start', type: 'start' }, route, repair, review, final, { id: 'end', type: 'end' }];
  workflow.edges = [edge('start', 'route'), edge('route', 'repair', 'repair'), edge('route', 'review', 'review'), edge('repair', 'review'), edge('review', 'final'), edge('final', 'end')];
  workflow.loops = [
    { id: 'repair-loop', entry_node: 'route', exit_node: 'review', node_ids: ['route', 'repair', 'review'], max_rounds: 4,
      until: { op: 'eq', args: [{ path: '/loops/repair-loop/all_accepted' }, { value: true }] },
      feedback_bindings: { findings: '/nodes/review/output/verdicts' },
      item_scope: { items: '/inputs/items', verdicts: '/nodes/review/output/verdicts', paths_field: 'files', dependencies_field: 'dependencies' } },
    { id: 'repair-loop-extra', entry_node: 'review', exit_node: 'review', node_ids: ['review'], max_rounds: 1, until: { op: 'eq', args: [{ value: true }, { value: true }] } },
  ];
  const context = { providers: [
    { id: 'implementer', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'implementer' } },
    { id: 'reviewer', kind: 'native_agent', enabled: true, capabilities: { read: true, write: true }, config: { role: 'reviewer' } },
  ] };
  const original = validateWorkflowGraph(workflow, context);
  assert.equal(original.valid, true, JSON.stringify(original.errors));
  const renamed = renameLoopId(workflow, 'repair-loop', 'review-loop');
  assert.equal(renamed.loops[0].id, 'review-loop');
  const validation = validateWorkflowGraph(renamed, context);
  assert.equal(validation.valid, true, JSON.stringify(validation.errors));
  assert.equal(renamed.nodes.find(node => node.id === 'route').cases[0].when.args[0].path, '/loops/review-loop/repair_items');
  assert.equal(renamed.nodes.find(node => node.id === 'final').input_bindings.feedback, '/loops/review-loop/feedback/findings');
  assert.equal(renamed.nodes.find(node => node.id === 'final').input_bindings.sibling, '/loops/repair-loop-extra/all_accepted');
  assert.equal(renamed.loops[1].id, 'repair-loop-extra');
});
test('source update status is explicit and leaves saved revisions and pinned resources intact', async t => {
  const { root, store, pack } = await fixture(t); const path = join(root, 'SKILL.md'); await writeFile(path, 'source version one');
  const source = { ...pack, provenance: { ...pack.provenance, source_path: path, source_hash: digest('source version one') } };
  assert.equal((await skillSourceStatus(source)).entries[0].status, 'unchanged');
  await writeFile(path, 'source version two'); const changed = await skillSourceStatus(source);
  assert.equal(changed.entries[0].status, 'update_available'); assert.equal(changed.workflow_changed, false);
  assert.deepEqual(await store.snapshot('editor', pack.revision_hash), pack);
  assert.equal((await store.resources('editor', pack.revision_hash))['instructions/task.md'].toString(), 'Original\n');
  await rm(path); const missing = await skillSourceStatus(source); assert.equal(missing.entries[0].status, 'unavailable'); assert.equal(missing.entries[0].error.code, 'ENOENT');
});
test('malformed Draft canvas reports null, duplicate, missing endpoint and invalid position without altering recoverable IR', () => {
  const workflow = { nodes: [null, { id: 'a', type: 'agent', ui: { position: { x: 'invalid', y: 0 } } }, { id: 'a', type: 'end' }], edges: [null, { id: 'bad', source: 'a', target: 'missing' }] };
  const before = structuredClone(workflow); assert.equal(canvasIssues(workflow).length, 5);
  assert.throws(() => toCanvas(workflow), /nodes\[0\]/); assert.deepEqual(workflow, before);
});
test('graph console serves bundled assets with bounded CSP and keeps human publication separate from model tools', async t => {
  const { root } = await fixture(t); const consoleState = await startConsole({ configPath: join(root, 'control-plane.json'), defaultConfigPath: DEFAULT_CONFIG_PATH, open: false, port: 0 }); t.after(stopConsole);
  const base = `http://127.0.0.1:${consoleState.port}`;
  const html = await fetch(base + '/workflows'); assert.equal(html.status, 200); assert.match(html.headers.get('content-security-policy'), /script-src 'self'/); assert.match(html.headers.get('content-security-policy'), /style-src-attr 'unsafe-inline'/);
  for (const asset of ['/workflows.js','/workflows.css']) { const response = await fetch(base + asset); assert.equal(response.status, 200); const source=await response.text(); assert(source.length > 1000); if(asset==='/workflows.js'){assert.match(source,/customize_role/);assert.match(source,/New role/);} }
  assert.equal((await fetch(base + '/web-src/main.tsx')).status, 404);
  assert.equal((await fetch(base + '/api/workflow/publish', { method: 'POST', body: '{}' })).status, 401);
});
