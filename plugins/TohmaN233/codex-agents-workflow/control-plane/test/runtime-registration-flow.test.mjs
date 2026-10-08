import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, chmod, writeFile } from 'node:fs/promises';
import { delimiter, join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';
import { canonicalJSON, digest } from '../lib/workflow-revisions.mjs';

const executableName = 'workflow-fixture-tool';
const requirement = { name: executableName, version: '>=1,<2' };

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'runtime-registration-flow-'));
  const workspace = join(root, 'workspace');
  const home = join(root, 'home');
  const firstDirectory = join(root, 'first-tools');
  const secondDirectory = join(root, 'second-tools');
  await Promise.all([mkdir(workspace), mkdir(home), mkdir(firstDirectory), mkdir(secondDirectory)]);
  const configPath = join(root, 'control-plane.json');
  const service = new WorkflowService({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: {
      USERPROFILE: home,
      HOME: home,
      PATH: [firstDirectory, secondDirectory].join(delimiter),
    },
    capabilities: { nativeAgentObserver: null, nativeParentVerifier: async () => {} },
  });
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  await service.call('migrate_v6', {}, { human: true });
  return { root, workspace, firstDirectory, secondDirectory, configPath, service };
}

async function writeVersionTool(directory, version) {
  await mkdir(directory, { recursive: true });
  const path = join(directory, executableName + (process.platform === 'win32' ? '.cmd' : ''));
  const content = process.platform === 'win32'
    ? `@echo off\r\necho ${executableName} ${version}\r\n`
    : `#!/bin/sh\necho ${executableName} ${version}\n`;
  await writeFile(path, content);
  if (process.platform !== 'win32') await chmod(path, 0o755);
  return path;
}

function testWorkflow() {
  const workflow = {
    ...createDraft('runtime-registration-flow', 'Runtime registration flow'),
    status: 'ready',
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    inputs_schema: { type: 'object', properties: { task: { type: 'string' } }, required: ['task'], additionalProperties: false },
    requirements: { providers: [], tools: [], mcp_servers: [], executables: [requirement] },
    finalization: { required: true, node_id: 'final' },
  };
  const agent = (id, role = 'implementer') => ({
    id, type: 'agent', executor: { kind: 'main' }, role, access: 'read_only',
    prompt_template: '{{task}}', approval: { required: false }, retry: { max_attempts: 1 },
    input_bindings: { task: '/inputs/task' },
  });
  workflow.nodes = [
    { id: 'start', type: 'start' },
    agent('first'),
    agent('second'),
    agent('final', 'finalizer'),
    { id: 'end', type: 'end' },
  ];
  workflow.edges = [
    ['start', 'first'], ['first', 'second'], ['second', 'final'], ['final', 'end'],
  ].map(([source, target]) => ({ id: `${source}-${target}`, source, target }));
  return workflow;
}

async function completeMain(runtime, run, envelope) {
  const args = {
    node_id: envelope.node_id,
    attempt_id: envelope.attempt_id,
    lease_token: envelope.lease_token,
    control_token: run.control_token,
  };
  const request_id = `fixture-main-${envelope.attempt_id}`;
  await runtime.recordHostMainDispatchIntent(run.run_id, {
    ...args, request_id, envelope_hash: digest(canonicalJSON(envelope)),
  });
  await runtime.recordHostMainDispatchReceipt(run.run_id, {
    ...args,
    request_id,
    receipt: {
      invocation_id: request_id,
      executor: 'codex-app-server-host-main',
      executable_sha256: 'a'.repeat(64),
      model: 'fixture-main',
      effort: 'medium',
      main_actor: 'root',
      session_id: `fixture-session-${run.run_id}`,
      call_chain_id: `fixture-run-${run.run_id}`,
    },
  });
  const completion = {
    status: 'succeeded', summary: 'Synthetic integration result', structured_output: {},
    artifacts: [], evidence: [{ check: 'fixture', passed: true }], changed_paths: [], outside_paths: [],
  };
  const saved = await runtime.runs.saveExecutorResult(run.run_id, envelope.attempt_id, completion);
  await runtime.recordExecutorEvent(run.run_id, {
    ...args, event: { kind: 'result_proposed', metadata: { ...saved, final_acceptance_required: true } },
  });
  return runtime.completeHostMainResult(run.run_id, args);
}

function assertWorkerEnvironmentContainsOnlyUsableLocations(envelope) {
  const environment = envelope.constraints.runtime_environment;
  assert.deepEqual(Object.keys(environment).sort(), ['status', 'tools']);
  const tools = environment.tools;
  assert.equal(tools.length, 1);
  assert.deepEqual(Object.keys(tools[0]).sort(), ['name', 'path', 'status']);
  assert.equal(tools[0].name, executableName);
  assert.equal(tools[0].status, 'found');
  assert.equal(Object.hasOwn(envelope.constraints, 'runtime_requirements'), false);
  const serialized = JSON.stringify(envelope);
  for (const field of ['requirement_key', 'searched_directories', 'probe_kind', 'host-runtime-registry.json'])
    assert.equal(serialized.includes(field), false, `worker envelope contains host evidence field ${field}`);
}

test('start discovers a task-local environment and registers it before creating a Run',async t=>{
  const f=await fixture(t);
  const executable=await writeVersionTool(join(f.workspace,'.venv',process.platform==='win32'?'Scripts':'bin'),'1.0.0');
  const created=await f.service.call('create',{workflow:testWorkflow()},{human:true});
  const run=await f.service.call('start',{workflow_id:created.workflow.id,revision_hash:created.revision_hash,workspace:f.workspace,access:'read_only',main_actor:'root',inputs:{task:'Discover project environment'}});
  assert.equal(run.constraints.runtime_environment.tools[0].path,executable);
  const registry=await f.service.call('runtime_dependencies');
  assert.equal(Object.values(registry.candidates)[0].path,executable);
  assert.equal(run.nodes.first.attempts.length,0);
});

test('registration recovery journals attention, rebinds before the next claim, and resumes the same Run', async t => {
  const f = await fixture(t);
  const firstPath = await writeVersionTool(f.firstDirectory, '1.0.0');
  const beforeDiscovery = await f.service.call('runtime_dependencies');
  assert.equal(beforeDiscovery.generation, 0);
  assert.deepEqual(beforeDiscovery.candidates, {});

  const discovered = await f.service.call('discover_runtime_dependencies', {
    executables: [requirement], environment_directories: [f.firstDirectory],
  }, { human: true });
  assert.equal(discovered.status, 'ready');
  assert.equal(discovered.tools[0].path, firstPath);
  const discoveredRegistry = await f.service.call('runtime_dependencies');
  assert.equal(discoveredRegistry.generation, 1);
  assert.equal(Object.values(discoveredRegistry.candidates)[0].path, firstPath);

  const created = await f.service.call('create', { workflow: testWorkflow() }, { human: true });
  const run = await f.service.call('start', {
    workflow_id: created.workflow.id,
    revision_hash: created.revision_hash,
    workspace: f.workspace,
    access: 'read_only',
    main_actor: 'root',
    inputs: { task: 'Synthetic dependency lifecycle' },
  });
  const opened = await f.service.open();
  const runtime = opened.runtime;
  const initialRecord = await runtime.runs.read(run.run_id);
  const initialConstraints = structuredClone(initialRecord.state.constraints);
  const initialPinsHash = initialRecord.state.pins_hash;

  // Authentication and sequence checks must finish before dependency probes or writes.
  let verificationCalls = 0;
  let discoveryCalls = 0;
  const verify = runtime.environmentVerifier;
  const discover = runtime.environmentResolver;
  runtime.environmentVerifier = async () => { verificationCalls++; return []; };
  runtime.environmentResolver = async () => { discoveryCalls++; throw new Error('must not discover'); };
  await assert.rejects(runtime.ensureRuntimeEnvironment(run.run_id, { control_token: 'example-wrong-controller' }), { code: 'RUN_AUTHORITY' });
  await assert.rejects(runtime.ensureRuntimeEnvironment(run.run_id, {
    control_token: run.control_token, expected_sequence: initialRecord.sequence + 1,
  }), { code: 'RUN_SEQUENCE_CONFLICT' });
  assert.equal(verificationCalls, 0);
  assert.equal(discoveryCalls, 0);
  assert.equal((await runtime.runs.read(run.run_id)).sequence, initialRecord.sequence);
  runtime.environmentVerifier = verify;
  runtime.environmentResolver = discover;

  await assert.rejects(f.service.call('recheck_runtime_environment', {
    run_id: run.run_id, control_token: 'example-wrong-controller',
  }), { code: 'RUN_AUTHORITY' });

  const first = await runtime.claimHostMain(run.run_id, {
    node_id: 'first', owner: 'root', request_id: 'claim-first', control_token: run.control_token,
  });
  assertWorkerEnvironmentContainsOnlyUsableLocations(first);
  assert.equal(first.constraints.runtime_environment.tools[0].path, firstPath);
  const afterFirst = await completeMain(runtime, run, first);
  assert.equal(afterFirst.nodes.first.status, 'succeeded');
  assert.equal(afterFirst.nodes.first.attempts.length, 1);
  assert.equal(afterFirst.nodes.second.status, 'ready');

  await rm(firstPath);
  await assert.rejects(runtime.claimHostMain(run.run_id, {
    node_id: 'second', owner: 'root', request_id: 'claim-second-before-registration', control_token: run.control_token,
  }), { code: 'ENVIRONMENT_SETUP_REQUIRED' });
  const attention = await runtime.runs.read(run.run_id);
  assert.equal(attention.state.status, 'running');
  assert.equal(attention.state.nodes.first.status, 'succeeded');
  assert.equal(attention.state.nodes.first.attempts.length, 1);
  assert.equal(attention.state.nodes.second.status, 'ready');
  assert.equal(attention.state.nodes.second.attempts.length, 0);
  assert.equal(attention.state.environment_attention.status, 'installation_approval_required');
  assert.deepEqual(attention.state.environment_attention.missing, [executableName]);
  assert(attention.events.some(event => event.kind === 'runtime_environment_attention'));

  const registryBeforeRejectedRegistration = await f.service.call('runtime_dependencies');
  await assert.rejects(f.service.call('register_runtime_dependency', {
    requirement, path: await writeVersionTool(f.secondDirectory, '1.2.0'),
  }), { code: 'HUMAN_CONFIGURATION_REQUIRED' });
  assert.deepEqual(await f.service.call('runtime_dependencies'), registryBeforeRejectedRegistration);

  const secondPath = join(f.secondDirectory, executableName + (process.platform === 'win32' ? '.cmd' : ''));
  const registered = await f.service.call('register_runtime_dependency', { requirement, path: secondPath }, { human: true });
  assert.equal(registered.path, secondPath);
  const registryAfterRegistration = await f.service.call('runtime_dependencies');
  assert.equal(registryAfterRegistration.generation, registryBeforeRejectedRegistration.generation + 1);
  assert.equal(Object.values(registryAfterRegistration.candidates)[0].path, secondPath);

  const resumed = await f.service.call('recheck_runtime_environment', {
    run_id: run.run_id, control_token: run.control_token,
  });
  assert.equal(resumed.environment.status, 'ready');
  assert.equal(resumed.environment.tools[0].path, secondPath);
  const rebound = await runtime.runs.read(run.run_id);
  assert.equal(rebound.state.status, 'running');
  assert.equal(rebound.state.environment_generation, 1);
  assert.equal(rebound.state.runtime_environment.tools[0].path, secondPath);
  assert.deepEqual(rebound.state.constraints, initialConstraints);
  assert.equal(rebound.state.pins_hash, initialPinsHash);
  assert.equal(rebound.pins.root.workflow.requirements.executables[0].name, executableName);
  assert(rebound.events.some(event => event.kind === 'runtime_environment_rebound'));
  assert.equal(rebound.state.nodes.first.status, 'succeeded');
  assert.equal(rebound.state.nodes.first.attempts.length, 1);
  assert.equal(rebound.state.nodes.second.status, 'ready');
  assert.equal(rebound.state.nodes.second.attempts.length, 0);

  const second = await runtime.claimHostMain(run.run_id, {
    node_id: 'second', owner: 'root', request_id: 'claim-second-after-registration', control_token: run.control_token,
  });
  assertWorkerEnvironmentContainsOnlyUsableLocations(second);
  assert.equal(second.constraints.runtime_environment.tools[0].path, secondPath);
  const afterSecondClaim = await runtime.runs.read(run.run_id);
  assert.equal(afterSecondClaim.state.nodes.first.status, 'succeeded');
  assert.equal(afterSecondClaim.state.nodes.first.attempts.length, 1);
  assert.equal(afterSecondClaim.state.nodes.second.status, 'claimed');
  assert.equal(afterSecondClaim.state.nodes.second.attempts.length, 1);
});
