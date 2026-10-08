import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdtemp, mkdir, rm, writeFile, readFile, readdir, chmod, stat } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join, resolve } from 'node:path';
import { buildCodexProfile, cleanupCodexProfile, isolatedEnvironment, pinObservedModel, profileSettings } from '../lib/execution/codex-profile-builder.mjs';
import { createSkillPolicy, skillPathKey } from '../lib/execution/codex-skill-policy.mjs';
import { createCodexSession as createCodexSessionImpl, createStrictSession } from '../lib/execution/codex-session.mjs';
import { createManagedNativeSession as createManagedNativeSessionImpl } from '../lib/execution/managed-native-session.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { processIdentity } from '../lib/execution/codex-process-ownership.mjs';

const testMetadata=async({model})=>({slug:model,tool_mode:'code_mode_only',base_instructions:'Unchanged normal instructions',input_modalities:['text','image'],supports_parallel_tool_calls:true});
const createCodexSession=options=>createCodexSessionImpl({...options,dynamicToolFormat:'untagged_function',modelMetadataReader:testMetadata});
const createManagedNativeSession=options=>createManagedNativeSessionImpl({...options,dynamicToolFormat:'untagged_function',modelMetadataReader:testMetadata});

const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };

test('normal and managed nodes retain user Codex configuration, native items and exact history receipts', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-codex-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-codex'), cwd = join(root, 'workspace');
  await writeFile(binary, 'fixture'); await mkdir(userHome); await mkdir(cwd);
  const skill = join(root, 'skill', 'SKILL.md'); await mkdir(join(root, 'skill'));
  const skillText = '---\nname: relevant\n---\nRelevant instructions'; await writeFile(skill, skillText);
  for (const factory of [createCodexSession, createManagedNativeSession]) {
    const ambient = factory === createManagedNativeSession;
    let launch, closed = 0; const metadata = [];
    const client = {
      events: [], initialized() {}, async close() { closed++; },
      async call(method, params) {
        if (method === 'initialize') return {};
        if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
        if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
        if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: [
          { name: 'relevant', path: skill, enabled: true },
          { name: 'unrelated', path: join(root, 'unrelated', 'SKILL.md'), enabled: true },
        ] }] };
        if (method === 'thread/start') {
          assert.equal(params.cwd, cwd); assert.equal(params.model, 'fixture-model');
          assert.equal(params.config.tool_output_token_limit,64000);
          const catalog=JSON.parse(await readFile(params.config.model_catalog_json,'utf8'));
          assert.equal(catalog.models[0].tool_mode,'direct');
          assert.deepEqual(catalog.models[0].input_modalities,['text','image']);
          assert.equal(catalog.models[0].base_instructions,'Unchanged normal instructions');
          assert.equal(params.modelProvider, 'openai');
          assert.equal(params.sandbox, 'workspace-write'); assert.equal(params.approvalPolicy, undefined);
          assert.equal(params.baseInstructions, undefined); assert.equal(params.environments, undefined);
          assert.deepEqual(params.config.skills.config, [
            { path: skill, enabled: false }, { path: join(root, 'unrelated', 'SKILL.md'), enabled: false },
          ]); assert.equal(params.ephemeral, false);
          assert.deepEqual(params.dynamicTools.map(tool => tool.name), ['read_workflow_resource', 'run_workspace_command', 'continue_workspace_command']);
          return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'workspaceWrite' },
            thread: { id: 'thread-1' }, instructionSources: [{ kind: 'project' }] };
        }
        if (method === 'turn/start') {
          assert.equal(params.effort, 'high');
          assert.deepEqual(params.input[0], { type: 'text', text: 'Do the node' });
          assert.equal(params.input[1].type, 'skill'); assert.equal(params.input[1].name, 'relevant');
          assert.notEqual(params.input[1].path, skill);
          assert.equal(await readFile(params.input[1].path, 'utf8'), skillText);
          assert.equal(await readFile(join(resolve(params.input[1].path, '..'), 'references', 'detail.txt'), 'utf8'), 'PINNED_REFERENCE');
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'agentMessage', phase: 'commentary', text: 'Working' } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'other-turn', item: { type: 'agentMessage', phase: 'final_answer', text: 'wrong turn' } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'commandExecution', status: 'completed', exitCode: 0, command: 'pwd', cwd, aggregatedOutput: cwd } } });
          this.events.push({ method: 'item/completed', params: { threadId: 'thread-1', turnId: 'turn-1', item: { type: 'agentMessage', phase: 'final_answer', text: '{"ok":true}' } } });
          return { turn: { id: 'turn-1' } };
        }
        assert.fail(`Unexpected call ${method}`);
      },
      async waitFor() { return { method: 'turn/completed', params: { threadId: 'thread-1', turn: { id: 'turn-1', status: 'completed' } } }; },
    };
    const session = await factory({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
      cwd, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome, PATH: 'fixture' },
      hostAuth: {}, skillPolicy: { implicit: 'deny', ambient_allow: ambient ? [skill] : [], shadowed_skill_paths: [] },
      owner: { run_id: 'run-1', node_id: 'node-1', attempt_id: 'attempt-1' },
      allowedSkills: [{ source_path: skill, source_hash: digest(skillText), name: 'relevant',
        files: { 'SKILL.md': skillText, 'references/detail.txt': 'PINNED_REFERENCE' } }],
      toolBroker: { tools: () => [{ name: 'read_workflow_resource' }], call() { assert.fail('No tool call expected'); }, revoke() {}, quiesce: async () => ({ quiescent: true }) },
      clientFactory: (_binary, options) => { launch = options; return client; }, onEvent: event => metadata.push(event) });
    assert.equal(launch.home, userHome); assert.deepEqual(launch.overrides, []);
    assert.equal(launch.env.CODEX_HOME, userHome);
    if (ambient) await writeFile(skill, 'Changed source after Run pinning');
    else await rm(skill);
    const result = await session.turn('Do the node', { explicit_sources: ambient ? [] : [skill] });
    assert.equal(result.output, '{"ok":true}'); assert.deepEqual(result.item_types, ['agentMessage', 'commandExecution', 'agentMessage']);
    assert.equal(result.command_audit[0].command, 'pwd'); assert.equal(result.audit.instruction_source_count, 1);
    await session.close(); assert.equal(closed, 2);
    assert(launch.overrides.some(value=>value.startsWith('model_catalog_json=')));
    const receipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
    assert.deepEqual(receipt.owner, { run_id: 'run-1', node_id: 'node-1', attempt_id: 'attempt-1' });
    assert.equal(receipt.user_codex_home, userHome); assert.deepEqual(receipt.thread_ids, ['thread-1']);
    assert.deepEqual(receipt.turn_ids, ['turn-1']); assert.equal(typeof receipt.closed_at, 'string');
    if (ambient) assert.equal(await readFile(skill, 'utf8'), 'Changed source after Run pinning');
    assert.equal((await stat(userHome)).isDirectory(), true);
  }
});

test('normal session exposes shutdown failure and permits an exact owned close retry', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-close-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  let closes = 0;
  const client = { events: [], initialized() {},
    async close() { if (++closes === 1) throw Object.assign(new Error('owned child still active'), { code: 'CHILD_ACTIVE' }); },
    async call(method) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'read_only', env: { CODEX_HOME: userHome }, clientFactory: () => client });
  await assert.rejects(session.close(), { code: 'CHILD_ACTIVE' });
  const firstReceipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.equal(firstReceipt.closed_at, undefined);
  await session.close();
  const finalReceipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.equal(closes, 2); assert.equal(typeof finalReceipt.closed_at, 'string');
  assert.equal((await stat(userHome)).isDirectory(), true);
});

test('normal correction continues the same thread with short input and the exact output schema', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-continuation-')); t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), home = join(root, 'home'), cwd = join(root, 'workspace');
  await writeFile(binary, 'fixture'); await mkdir(home); await mkdir(cwd);
  const schema = { type: 'object', properties: { answer: { type: 'string' } }, required: ['answer'], additionalProperties: false };
  let threadStarts = 0, turns = 0;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, args) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: [] }] };
      if (method === 'thread/start') { threadStarts++; return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'readOnly' }, thread: { id: 'same-thread' }, instructionSources: [] }; }
      if (method === 'turn/start') {
        turns++; assert.equal(args.threadId, 'same-thread'); assert.deepEqual(args.outputSchema, schema);
        assert.deepEqual(args.input, [{ type: 'text', text: turns === 1 ? 'Original node task' : 'Correct locations[12]' }]);
        const id = `turn-${turns}`;
        this.events.push({ method: 'item/completed', params: { threadId: 'same-thread', turnId: id,
          item: { type: 'agentMessage', phase: 'final_answer', text: JSON.stringify({ answer: id }) } } });
        return { turn: { id } };
      }
      assert.fail(`Unexpected call ${method}`);
    },
    async waitFor() { return { method: 'turn/completed', params: { threadId: 'same-thread', turn: { id: `turn-${turns}`, status: 'completed' } } }; },
  };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd, model: 'fixture-model', effort: 'high', access: 'read_only', maxTurns: 2,
    env: { CODEX_HOME: home }, clientFactory: () => client,
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] } });
  assert.equal((await session.turn('Original node task', { output_schema: schema })).thread_id, 'same-thread');
  assert.equal((await session.continueTurn('Correct locations[12]', { output_schema: schema })).output, '{"answer":"turn-2"}');
  assert.equal(threadStarts, 1); assert.equal(turns, 2);
  await assert.rejects(session.continueTurn('Third correction', { output_schema: schema }), { code: 'CODEX_SESSION_BUSY' });
  await session.close();
  const receipt = JSON.parse(await readFile(join(session.profile.receipt_home, 'attempt.json'), 'utf8'));
  assert.deepEqual(receipt.thread_ids, ['same-thread']); assert.deepEqual(receipt.turn_ids, ['turn-1', 'turn-2']);
});

test('environment API-key mode selects an env-key provider without changing shared account login', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-api-key-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  const calls = []; let launch;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      calls.push(method);
      if (method === 'initialize') return {};
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: [] }] };
      if (method === 'thread/start') {
        assert.equal(params.modelProvider, 'workflow_environment_api_key');
        return { model: 'fixture-model', modelProvider: params.modelProvider, sandbox: { type: 'workspaceWrite' }, thread: { id: 'thread-key' } };
      }
      if (method === 'turn/start') {
        this.events.push({ method: 'item/completed', params: { threadId: 'thread-key', turnId: 'turn-key', item: { type: 'agentMessage', phase: 'final_answer', text: 'done' } } });
        return { turn: { id: 'turn-key' } };
      }
      assert.fail(`Unexpected call ${method}`);
    },
    async waitFor() { return { params: { turn: { id: 'turn-key', status: 'completed' } } }; } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome, TASK_API_KEY: 'example-fixture-secret-never-log' },
    authentication: { mode: 'environment_api_key', api_key_env: 'TASK_API_KEY' },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    clientFactory: (_binary, options) => { launch = options; return client; } });
  assert.equal(launch.home, userHome); assert(launch.overrides.some(value => value.includes('env_key="TASK_API_KEY"')));
  assert.equal(launch.overrides.some(value => value.includes('fixture-secret')), false);
  assert.deepEqual(await session.login({ apiKeyEnv: 'TASK_API_KEY' }), { authenticated: true, type: 'environment_api_key' });
  const result = await session.turn('Use configured API provider'); assert.equal(result.output, 'done');
  assert.equal(calls.includes('account/login/start'), false); assert.equal(calls.includes('account/read'), false);
  await session.close(); assert.equal((await stat(userHome)).isDirectory(), true);
});

test('implicit allow retains enabled Skills except shadowed sources', async t => {
  const root = await mkdtemp(join(tmpdir(), 'normal-skills-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  const paths = ['related', 'other', 'shadowed'].map(name => join(root, name, 'SKILL.md'));
  const marker = new Error('thread/start observed');
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: paths.map((path, index) => ({ name: `skill-${index}`, path, enabled: true })) }] };
      if (method === 'thread/start') {
        assert.equal(params.sandbox, 'read-only'); assert.equal(params.approvalPolicy, undefined);
        assert.deepEqual(params.config.skills.config, paths.map((path, index) => ({ path, enabled: index !== 2 })));
        throw marker;
      }
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'read_only', env: { CODEX_HOME: userHome },
    skillPolicy: { implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [paths[2]] }, clientFactory: () => client });
  await assert.rejects(session.turn('Read relevant task context'), error => error === marker);
  await session.close();
});

test('normal session fails before a model turn if App Server substitutes its authorized sandbox', async t => {
  await assert.rejects(createCodexSession({ access: undefined }), { code: 'CODEX_ACCESS_MODE' });
  const root = await mkdtemp(join(tmpdir(), 'normal-sandbox-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const binary = join(root, 'binary'), userHome = join(root, 'user-home');
  await writeFile(binary, 'fixture'); await mkdir(userHome);
  let turnStarted = false;
  const client = { events: [], initialized() {}, async close() {},
    async call(method, params) {
      if (method === 'initialize') return {};
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model: 'fixture-model', supportedReasoningEfforts: [{ reasoningEffort: 'high' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: root, errors: [], skills: [] }] };
      if (method === 'thread/start') {
        assert.equal(params.sandbox, 'workspace-write'); assert.equal(params.approvalPolicy, undefined);
        return { model: 'fixture-model', modelProvider: 'openai', sandbox: { type: 'readOnly' }, thread: { id: 'wrong-sandbox' } };
      }
      if (method === 'turn/start') turnStarted = true;
      assert.fail(`Unexpected call ${method}`);
    } };
  const session = await createCodexSession({ parent: root, binary, expectedBinaryHash: digest(await readFile(binary)),
    cwd: root, model: 'fixture-model', effort: 'high', access: 'bounded_write', allowedPaths:['.'], env: { CODEX_HOME: userHome },
    skillPolicy: { implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] }, clientFactory: () => client });
  await assert.rejects(session.turn('Write within the assigned workspace'), { code: 'CODEX_SANDBOX_UNCONTROLLED' });
  assert.equal(turnStarted, false);
  await session.close();
});

test('isolated Workflow profile keeps host dynamic-tool transport enabled without ambient code mode', () => {
  const settings = profileSettings({ home: 'C:/fixture', model: 'fixture-model' });
  assert.equal(settings['features.code_mode_host'], true);
  assert.equal(settings['features.code_mode'], false);
  assert.equal(settings['features.shell_tool'], false);
});

async function fixture(t, { profile = true, modelMetadata = true } = {}) {
  const root = await mkdtemp(join(tmpdir(), 'strict-execution-')); const binary = join(root, 'fixture-binary'); await writeFile(binary, 'Synthetic never-executed binary');
  t.after(async () => { assert(resolve(root).startsWith(resolve(tmpdir()))); await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 }); });
  const options = { parent: root, binary, expectedBinaryHash: digest(await readFile(binary)), model: 'synthetic-model', effort: 'low',
    processIdentityImpl: async pid => ({ pid, executable: process.execPath, started: 'deterministic-fixture-parent' }),
    ...(modelMetadata ? { modelMetadata: { slug: 'synthetic-model', supported_reasoning_levels: [{ effort: 'low' }] } } : {}) };
  if (!profile) {
    const home = join(root, 'catalog-fixture'); await mkdir(join(home, 'skills'), { recursive: true });
    return { root, options, profile: { home } };
  }
  return { root, options, profile: await buildCodexProfile(options) };
}

test('Strict profile records deterministic parent evidence and refuses unavailable ownership before creating a profile', async t => {
  const f = await fixture(t);
  const owner = JSON.parse(await readFile(join(f.profile.home, 'owner.json'), 'utf8'));
  assert.deepEqual(owner.parent_identity, await f.options.processIdentityImpl(process.pid));
  await cleanupCodexProfile(f.profile);
  let observedPid;
  await assert.rejects(buildCodexProfile({ ...f.options, processIdentityImpl: async pid => {
    observedPid = pid;
    throw Object.assign(new Error('unqualified platform'), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  } }), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
  assert.equal(observedPid, process.pid);
  assert.deepEqual(await readdir(f.root), ['fixture-binary']);
});

test('real platform process ownership returns stable OS evidence or explicitly refuses unsupported inspection', async () => {
  if (!['win32', 'linux'].includes(process.platform)) {
    await assert.rejects(processIdentity(process.pid), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
    return;
  }
  const first = await processIdentity(process.pid), second = await processIdentity(process.pid);
  assert.deepEqual(first, second);
  assert.equal(first.pid, process.pid);
  assert.equal(first.executable, resolve(process.execPath));
  assert(first.started.length > 0);
});

test('unqualified platform ownership inspection refuses profile creation before effects', async t => {
  const f = await fixture(t, { profile: false });
  // Exercise the production refusal branch even on a qualified test host.
  const script = `Object.defineProperty(process, 'platform', { value: 'darwin' });
    const assert = (await import('node:assert/strict')).default;
    const { processIdentity } = await import(process.argv[1]);
    const { buildCodexProfile } = await import(process.argv[2]);
    const options = JSON.parse(process.argv[3]);
    await assert.rejects(processIdentity(process.pid), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });
    await assert.rejects(buildCodexProfile(options), { code: 'PROCESS_IDENTITY_UNSUPPORTED' });`;
  await promisify(execFile)(process.execPath, ['--input-type=module', '--eval', script,
    new URL('../lib/execution/codex-process-ownership.mjs', import.meta.url).href,
    new URL('../lib/execution/codex-profile-builder.mjs', import.meta.url).href,
    JSON.stringify(f.options)], { windowsHide: true, timeout: 10000 });
  assert.deepEqual((await readdir(f.root)).sort(), ['catalog-fixture', 'fixture-binary']);
});
const strict = { mode: 'strict', implicit: 'deny', shadowed_skill_paths: [], ambient_allow: [] };
const skillText = '---\nname: allowed\ndescription: Synthetic fixture\n---\nALLOWED_SENTINEL';
function metadataClient(cwd, skills) {
  return { async call(method, args) {
    if (method === 'skills/list') return { data: [{ cwd, errors: [], skills: structuredClone(skills) }] };
    assert.equal(method, 'skills/config/write'); const found = skills.find(skill => skillPathKey(skill.path) === skillPathKey(args.path)); assert(found); found.enabled = args.enabled; return {};
  } };
}

test('Strict profile rejects changed binary and owner token and strips inherited overrides', async t => {
  const f = await fixture(t); const env = isolatedEnvironment({ PATH: 'fixture-path', USERPROFILE: 'fixture-user', CODEX_HOME: 'shared', CODEX_CONFIG: 'untrusted', OPENAI_API_KEY: 'example-sensitive', SOL_CONTROL_DISABLED: '1' }, f.profile.home);
  assert.equal(env.CODEX_HOME, f.profile.home); assert.equal(env.CODEX_CONFIG, undefined); assert.equal(env.OPENAI_API_KEY, undefined); assert.equal(env.PATH, 'fixture-path');
  await writeFile(f.options.binary, 'Changed binary'); await assert.rejects(buildCodexProfile(f.options), { code: 'CODEX_BINARY_CHANGED' });
  await assert.rejects(cleanupCodexProfile({ ...f.profile, owner_token: 'wrong' }), { code: 'PROFILE_OWNER' });
  await cleanupCodexProfile(f.profile);
});

test('isolated profile pins only the authenticated observed model window',async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models:[
    {slug:'synthetic-model',context_window:272000,max_context_window:872000,base_instructions:'private cache text'},
    {slug:'other-model',context_window:42000},
  ]}));
  await pinObservedModel(f.profile,{model:'synthetic-model',displayName:'Synthetic',description:'Fixture model',defaultReasoningEffort:'low',inputModalities:['text'],supportedReasoningEfforts:[{reasoningEffort:'low',description:'Fixture effort'}]});
  const pinned=JSON.parse(await readFile(join(f.profile.home,'models.json'),'utf8')).models[0];
  assert.equal(pinned.context_window,272000);
  assert.equal(pinned.max_context_window,872000);
  assert.equal(JSON.stringify(pinned).includes('private cache text'),false);
  await cleanupCodexProfile(f.profile);
});

const observedFixtureModel={model:'synthetic-model',displayName:'Synthetic',description:'Fixture model',defaultReasoningEffort:'low',inputModalities:['text'],supportedReasoningEfforts:[{reasoningEffort:'low',description:'Fixture effort'}]};

test('isolated catalog treats nullable maximum as absent without inventing a window',async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models:[{slug:'synthetic-model',context_window:272000,max_context_window:null}]}));
  await pinObservedModel(f.profile,observedFixtureModel);
  const pinned=JSON.parse(await readFile(join(f.profile.home,'models.json'),'utf8')).models[0];
  assert.equal(pinned.context_window,272000);
  assert.equal(Object.hasOwn(pinned,'max_context_window'),false);
  await cleanupCodexProfile(f.profile);
});

for(const [name,models] of [
  ['missing model', [{slug:'other-model',context_window:272000}]],
  ['duplicate model', [{slug:'synthetic-model',context_window:272000},{slug:'synthetic-model',context_window:272000}]],
  ['missing window', [{slug:'synthetic-model'}]],
  ['null window', [{slug:'synthetic-model',context_window:null}]],
  ['invalid window', [{slug:'synthetic-model',context_window:'272000'}]],
  ['invalid maximum', [{slug:'synthetic-model',context_window:272000,max_context_window:32000}]],
]) test(`isolated catalog rejects ${name}`,async t=>{
  const f=await fixture(t,{modelMetadata:false});
  await writeFile(join(f.profile.home,'models_cache.json'),JSON.stringify({models}));
  await assert.rejects(pinObservedModel(f.profile,observedFixtureModel),{code:'CODEX_MODEL_CONTEXT'});
  await cleanupCodexProfile(f.profile);
});

test('Strict catalog enforcement is by path, explicit injection is separate, and policy changes invalidate launch', async t => {
  const f = await fixture(t, { profile: false }); const source = join(f.root, 'source', 'SKILL.md'); const cwd = join(f.root, 'workspace'); await mkdir(cwd);
  const policy = await createSkillPolicy({ home: f.profile.home, cwd, skillPolicy: strict, allowed: [{ source_path: source, source_hash: digest(skillText), name: 'allowed', files: { 'SKILL.md': skillText, 'references/example.txt': 'Owned resource' } }] });
  const input = policy.explicitInputs([source])[0];
  const disallowed = join(cwd, '.agents', 'skills', 'same-name', 'SKILL.md');
  const skills = [{ name: 'allowed', path: disallowed, scope: 'repo', enabled: true }, { name: 'allowed', path: input.path, scope: 'user', enabled: true }];
  const client = metadataClient(cwd, skills); const audit = await policy.apply(client); assert.deepEqual(audit.disabled_skills, [disallowed]);
  assert.equal(policy.read({ path: input.path }).contentItems[0].text, skillText);
  assert.throws(() => policy.read({ path: disallowed }), { code: 'SKILL_READ_DENIED' });
  assert.throws(() => policy.explicitInputs([disallowed]), { code: 'SKILL_INJECTION_DENIED' });
  skills.push({ name: 'new', path: join(cwd, 'new', 'SKILL.md'), scope: 'repo', enabled: true });
  await assert.rejects(policy.verify(client), { code: 'SKILL_ISOLATION_FAILED' }); skills.pop();
  await chmod(input.path, 0o600); await writeFile(input.path, 'Changed owned snapshot'); await assert.rejects(policy.verify(client), { code: 'SKILL_PIN_CHANGED' });
});

test('unqualified administrative scope, shadowed source and unpinned ambient grant fail closed', async t => {
  const f = await fixture(t, { profile: false }); const source = join(f.root, 'SKILL.md');
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, shadowed_skill_paths: [source] }, allowed: [{ source_path: source, source_hash: digest(skillText), name: 'allowed', files: { 'SKILL.md': skillText } }] }), { code: 'SKILL_SHADOWED' });
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, ambient_allow: [source] } }), { code: 'SKILL_ALLOW_UNPINNED' });
  const policy = await createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: strict });
  await assert.rejects(policy.apply(metadataClient(f.root, [{ name: 'admin', path: source, scope: 'admin', enabled: true }])), { code: 'SKILL_SCOPE_UNQUALIFIED' });
  assert.deepEqual(policy.tools(), []);
});

test('Host-only policy does not mutate the Skill catalog and rejects Skill injection', async t => {
  const f = await fixture(t, { profile: false });
  const policy = await createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: strict, hostExecutionOnly: true });
  const client = { call() { assert.fail('Host-only policy must not call the Skill catalog'); } };
  assert.equal((await policy.apply(client)).catalog_mode, 'disabled_by_profile');
  await policy.verify(client);
  assert.deepEqual(policy.tools(), []);
  assert.deepEqual(policy.explicitInputs([]), []);
  assert.throws(() => policy.explicitInputs([join(f.root, 'SKILL.md')]), { code: 'SKILL_INJECTION_DENIED' });
  assert.throws(() => policy.read({ path: join(f.root, 'SKILL.md') }), { code: 'SKILL_READ_DENIED' });
  await assert.rejects(createSkillPolicy({ home: f.profile.home, cwd: f.root, skillPolicy: { ...strict, ambient_allow: [join(f.root, 'SKILL.md')] }, hostExecutionOnly: true }), { code: 'SKILL_ISOLATION_FAILED' });
});

function lifecycleClient(cwd, model, effort, hooks = {}) {
  return {
    pid: hooks.pid ?? 100, events: [], initialized() {},
    async close() { await hooks.close?.(); },
    async call(method, args = {}) {
      if (method === 'initialize') { await hooks.initialize?.(); return {}; }
      if (method === 'account/read') return { account: { type: 'chatgpt' }, requiresOpenaiAuth: true };
      if (method === 'model/list') return { data: [{ model, displayName: model, description: 'fixture', defaultReasoningEffort: effort, inputModalities:['text'],
        contextWindow:272000,supportedReasoningEfforts: [{ reasoningEffort: effort, description: 'fixture' }] }] };
      if (method === 'skills/list') return { data: [{ cwd: args.cwds?.[0] ?? cwd, errors: [], skills: [] }] };
      if (method === 'skills/config/write') return {};
      assert.fail(`Unexpected lifecycle client call: ${method}`);
    },
  };
}

async function lifecycleSessionFixture(t, clientFactory, extraOptions = {}) {
  const f = await fixture(t, { profile: false }); const cwd = join(f.root, 'workspace'); await mkdir(cwd);
  const options = { ...f.options, cwd, modelMetadata: undefined, skillPolicy: strict, allowedSkills: [],
    clientFactory, recordProfileChildImpl: async () => {}, cleanupCodexProfileImpl: async () => {}, ...extraOptions };
  return createStrictSession(options);
}

test('Host-only session reaches a source-free thread without any Skill RPC', async t => {
  const marker = new Error('thread/start intercepted');
  let skillCalls = 0;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method.startsWith('skills/')) skillCalls++;
      if (method === 'thread/start') { assert.deepEqual(args.dynamicTools, []); assert.equal(args.ephemeral,false); throw marker; }
      return originalCall(method, args);
    };
    return client;
  }, { hostExecutionOnly: true });
  await assert.rejects(session.turn('fixture'), error => error === marker);
  assert.equal(skillCalls, 0);
});

test('Strict close prevents an internal replacement launch after the current client starts closing', async t => {
  const closeEntered = deferred(); const releaseClose = deferred(); const clients = [];
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low', clients.length === 0 ? {
      close: async () => { closeEntered.resolve(); await releaseClose.promise; },
    } : {}); clients.push(client); return client;
  });
  const turn = session.turn('fixture'); await closeEntered.promise;
  const closing = session.close(); releaseClose.resolve();
  await assert.rejects(turn, { code: 'CODEX_SESSION_CLOSED' }); await closing;
  assert.equal(clients.length, 1, 'closing the first client must fence creation of a replacement client');
});

test('Strict close owns a replacement client that was registered before initialization completed', async t => {
  const initializeEntered = deferred(); const releaseInitialize = deferred(); const clients = []; const closeCalls = [];
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const index = clients.length;
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low', {
      pid: 100 + index,
      initialize: index === 1 ? async () => { initializeEntered.resolve(); await releaseInitialize.promise; } : undefined,
      close: async () => { closeCalls[index] = (closeCalls[index] ?? 0) + 1; },
    }); clients.push(client); return client;
  });
  const turn = session.turn('fixture'); await initializeEntered.promise;
  const closing = session.close(); await closing; releaseInitialize.resolve();
  await assert.rejects(turn, { code: 'CODEX_SESSION_CLOSED' });
  assert.equal(clients.length, 2, 'closing during replacement initialization must not create another client');
  assert.equal(closeCalls[1], 1, 'close must target the registered replacement client, not reuse the prior client state');
});

test('Strict session forwards the host-owned output schema to turn/start', async t => {
  const schema = { type: 'object', properties: { decision: { type: 'string' } }, required: ['decision'], additionalProperties: false };
  const marker = new Error('turn/start intercepted');
  let observed;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') return { instructionSources: [], model: 'synthetic-model', thread: { id: 'fixture-thread' } };
      if (method === 'turn/start') { observed = args; throw marker; }
      return originalCall(method, args);
    };
    return client;
  });
  await assert.rejects(session.turn('fixture', { output_schema: schema }), error => error === marker);
  assert.deepEqual(observed.outputSchema, schema);
});

test('Strict session preserves the app-server image response shape at its tool boundary', async t => {
  const marker = new Error('image response inspected'), response = { success: true,
    contentItems: [{ type: 'inputImage', imageUrl: 'data:image/png;base64,aW1hZ2U=' }] };
  const toolBroker = { tools: () => [{ name: 'view_workspace_image', description: 'fixture', inputSchema: { type: 'object' } }],
    call: async (name, args, callId) => {
      assert.equal(name, 'view_workspace_image'); assert.deepEqual(args, { path: 'card.png' }); assert.equal(callId, 'image-call');
      return response;
    }, revoke() {}, quiesce: async () => ({ quiescent: true, error: null }) };
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') { assert(args.dynamicTools.some(tool => tool.name === 'view_workspace_image'));
        return { instructionSources: [], model: 'synthetic-model', thread: { id: 'image-thread' } }; }
      if (method === 'turn/start') {
        assert.strictEqual(await options.onToolCall({ threadId: 'image-thread', tool: 'view_workspace_image',
          arguments: { path: 'card.png' }, callId: 'image-call' }), response);
        throw marker;
      }
      return originalCall(method, args);
    };
    return client;
  }, { hostExecutionOnly: true, toolBroker });
  await assert.rejects(session.turn('fixture'), error => error === marker);
});

test('Host-owned correction may use two fresh threads in one node profile, never a third', async t => {
  let started = 0;
  const session = await lifecycleSessionFixture(t, (_binary, options) => {
    const client = lifecycleClient(options.cwd, 'synthetic-model', 'low');
    const originalCall = client.call.bind(client);
    client.call = async (method, args) => {
      if (method === 'thread/start') {
        started++; return { instructionSources: [], model: 'synthetic-model', thread: { id: `thread-${started}` } };
      }
      if (method === 'turn/start') {
        const id = `turn-${started}`;
        client.events.push({ method: 'item/completed', params: { threadId: args.threadId, turnId: id, item: { type: 'agentMessage', text: '{"decision":"candidate_ready"}' } } });
        client.events.push({ method: 'turn/completed', params: { threadId: args.threadId, turn: { id, status: 'completed' } } });
        return { turn: { id } };
      }
      return originalCall(method, args);
    };
    client.waitFor = async matches => client.events.find(matches);
    return client;
  }, { hostExecutionOnly: true, maxTurns: 2 });
  assert.equal((await session.turn('first')).thread_id, 'thread-1');
  assert.equal((await session.turn('correction')).thread_id, 'thread-2');
  await assert.rejects(session.turn('third'), { code: 'CODEX_SESSION_BUSY' });
  await session.close();
});
