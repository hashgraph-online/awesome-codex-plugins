import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { loadConfig } from '../lib/config.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { ManagedNativeManager } from '../lib/execution/managed-native-manager.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

test('Host-owned provider journals valid items, repairs one in the same session, and reaches logical Main', { timeout: 15000 }, async t => {
  const root = await mkdtemp(join(tmpdir(), 'owned-native-integration-'));
  const workspace = join(root, 'workspace'); await mkdir(workspace);
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const configPath = join(root, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const provider = config.providers.find(item => item.id === 'native-luna');
  assert(provider?.enabled);
  let runtime, runId;
  const sessions = [], prompts = [], inputHashes = [], observed = [];
  const manager = new ManagedNativeManager({ configPath, env: {}, getConfig: async () => config,
    qualify: async () => ({ binary_sha256: 'b'.repeat(64), codex_binary: 'unused', authentication: { mode: 'environment_api_key' } }),
    sessionFactory: async settings => {
      sessions.push(settings);
      let turn = 0;
      const respond = async (prompt, repair = false) => {
        turn++; prompts.push(prompt);
        const inputHash = digest(canonicalJSON([{ type: 'text', text: prompt }])); inputHashes.push(inputHash);
        if (!repair) {
          const refs = JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)?.[1] ?? '{}');
          assert.match(prompt, /Implement the assigned jobs/);
          assert(refs.jobs.path.startsWith(join(workspace, 'work', '.workflow-runtime', 'managed-native')));
          assert.deepEqual(JSON.parse(await readFile(refs.jobs.path, 'utf8')), ['card-0', 'card-1']);
          assert.deepEqual(JSON.parse(await readFile(refs.plan.path, 'utf8')), { decision: 'Use the approved source locations' });
          assert.doesNotMatch(prompt, /approved source locations/);
          observed.push({ refs, cwd: settings.cwd, model: settings.model, effort: settings.effort });
        } else {
          const record = await runtime.runs.read(runId);
          const attempt = record.state.nodes.jobs.attempts[0];
          assert.equal(attempt.native_item_results[0].result, 'done-0');
          assert.equal(attempt.native_item_results[1], undefined);
          assert.doesNotMatch(prompt, /Host-selected unresolved positions/);
          assert.match(prompt, /Host already retained every accepted sibling result and file/);
          assert.doesNotMatch(prompt,/"item_index"/);
          assert.doesNotMatch(prompt, /Use the approved source locations/);
          const refs = JSON.parse(prompt.match(/\nInputs:\n([^\n]+)/)?.[1] ?? '{}');
          assert.deepEqual(JSON.parse(await readFile(refs.repair_items.path,'utf8')),['card-1']);
        }
        const items = repair
          ? [{ outcome: 'completed', result: 'done-1' }]
          : [{ outcome: 'completed', result: 'done-0' }, { outcome: 'blocked', block_reason: 'Needs one correction' }];
        return { output: JSON.stringify({ items }), thread_id: 'thread-owned', turn_id: `turn-${turn}`,
          usage: { unknown: true, input_tokens: 2, output_tokens: 1 }, audit: { input_sha256: inputHash },
          item_types: ['agentMessage'], command_audit: [] };
      };
      return { turn: prompt => respond(prompt), continueTurn: prompt => respond(prompt, true),
        async close() { settings.toolBroker.revoke(); }, async interrupt() {} };
    } });
  t.after(() => manager.close());
  const service = new WorkflowService({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    capabilities: { managedNativeManager: manager, nativeAgentObserver: null, nativeParentVerifier: async () => {} } });
  await service.call('migrate_v6', {}, { human: true });
  const workflow = { ...createDraft('owned-native-items', 'Owned native items'), status: 'ready', context_projection_version: 2,
    skill_policy: { mode: 'cooperative', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: { type: 'object', properties: { task: { type: 'string' }, jobs: { type: 'array', items: { type: 'string' } },
      plan: { type: 'object', properties: { decision: { type: 'string' } }, required: ['decision'], additionalProperties: false } },
      required: ['task', 'jobs', 'plan'], additionalProperties: false },
    finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' },
      { id: 'jobs', type: 'agent', role: 'implementer', executor: { kind: 'provider', provider_id: provider.id },
        access: 'read_only', approval: { required: false },
        retry: { max_attempts: 3 }, subagent_count: 'auto',
        fanout: { input: 'jobs', item_name: 'card', distribution: 'partition', batch_size: 10,
          scheduling: 'parallel', max_concurrency: 2, join: 'all_required', result_output: 'results', result_mode: 'per_item' },
        input_bindings: { task: '/inputs/task', jobs: '/inputs/jobs', plan: '/inputs/plan' }, prompt_template: 'Implement {{task}}.',
        outputs_schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'string' } } }, required: ['results'], additionalProperties: false } },
      { id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' }, access: 'read_only',
        approval: { required: false }, retry: { max_attempts: 1 }, input_bindings: { results: '/nodes/jobs/output/results' },
        prompt_template: 'Review the completed results.', outputs_schema: { type: 'object', properties: {}, required: [], additionalProperties: false } },
      { id: 'end', type: 'end' }],
    edges: [{ id: 'start-jobs', source: 'start', target: 'jobs' }, { id: 'jobs-final', source: 'jobs', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }] };
  const created = await service.call('create', { workflow }, { human: true });
  const run = await service.call('start', { workflow_id: workflow.id, revision_hash: created.revision_hash,
    workspace, access: 'bounded_write', allowed_paths: ['.'], main_actor: 'root',
    inputs: { task: 'Implement the assigned jobs', jobs: ['card-0', 'card-1'], plan: { decision: 'Use the approved source locations' } } });
  runId = run.run_id;
  ({ runtime } = await service.open());
  const { drive } = await service.open();
  const handoff = await drive.advanceToMain(runId, { control_token: run.control_token, owner: 'root', managedProviders: true });
  const record = await runtime.runs.read(runId);
  assert.equal(handoff.stop_reason, 'main_node', JSON.stringify({run_error:record.state.error,job:record.state.nodes.jobs.error}));
  assert.equal(handoff.host_binding.node_id, 'final');
  assert.deepEqual(record.state.nodes.jobs.output.results, ['done-0', 'done-1']);
  assert.equal(record.state.nodes.jobs.attempts.length, 1);
  assert.equal(record.state.nodes.jobs.attempts[0].native_item_results[0].result, 'done-0');
  assert.equal(record.state.nodes.jobs.attempts[0].native_rejected_turns[0].count, 1);
  assert.equal(sessions.length, 1);
  assert.equal(sessions[0].maxTurns, 3);
  assert.equal(prompts.length, 2);
  assert.equal(observed[0].cwd, workspace);
  assert.equal(observed[0].model, provider.config.model);
  const deliveries = record.state.nodes.jobs.attempts[0].executor_events.filter(item => item.kind === 'native_prompt_delivery');
  assert.deepEqual(deliveries.map(item => item.metadata.input_sha256), inputHashes);
});
