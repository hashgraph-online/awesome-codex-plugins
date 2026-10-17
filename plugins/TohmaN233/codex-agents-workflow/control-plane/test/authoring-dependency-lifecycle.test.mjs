import test from 'node:test';
import assert from 'node:assert/strict';
import { chmod, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { delimiter, join, resolve } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { WorkflowService } from '../lib/workflow-service.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';
import { WorkflowForge } from '../lib/authoring/workflow-forge.mjs';
import { SEMANTIC_BLUEPRINT_CONTRACT } from '../lib/authoring/blueprint-contract.mjs';
import { sourceSectionInventory } from '../lib/skill-import/source-dispositions.mjs';
import { createDraft } from '../lib/workflow-schema.mjs';

const routingRules = {
  version: 1,
  instructions: 'Use the registered fixture providers.',
  selection_mode: 'automatic',
  routes: {
    implementation: { provider_id: 'native-luna', role: 'implementer' },
    complex_implementation: { provider_id: 'native-luna', role: 'implementer' },
    review: { provider_id: 'native-reviewer', role: 'reviewer' },
    planning: { provider_id: 'native-luna', role: 'implementer' },
  },
  generation: { planner_provider_id: 'native-luna', review_provider_id: 'native-reviewer', max_rounds: 2 },
};
const providers = [
  { id: 'native-luna', enabled: true, kind: 'native_agent', capabilities: { read: true, write: true }, config: { role: 'implementer' } },
  { id: 'native-luna', enabled: true, kind: 'native_agent', capabilities: { read: true, write: true }, config: { role: 'implementer' } },
  { id: 'native-reviewer', enabled: true, kind: 'native_agent', capabilities: { read: true, write: false }, config: { role: 'reviewer' } },
];
const authoringContext = { routing_rules: routingRules, routing_catalog: providers, providers };

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'authoring-dependency-lifecycle-'));
  const home = join(root, 'home');
  const workspace = join(root, 'workspace');
  const emptyPath = join(root, 'empty-path');
  await Promise.all([mkdir(home), mkdir(workspace), mkdir(emptyPath)]);
  const configPath = join(root, 'control-plane.json');
  const service = new WorkflowService({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: { USERPROFILE: home, HOME: home, PATH: emptyPath },
    capabilities: { nativeAgentObserver: null, nativeParentVerifier: async () => {} },
  });
  t.after(async () => {
    await Promise.allSettled([...service.attemptAdmission.drainJobs.values()]);
    assert(resolve(root).startsWith(resolve(tmpdir())));
    await rm(root, { recursive: true, maxRetries: 3, retryDelay: 100 });
  });
  await service.call('migrate_v6', {}, { human: true });
  return { root, home, workspace, emptyPath, configPath, service };
}

function compactBlueprint(resources, runtime_dependencies) {
  const sections = sourceSectionInventory(resources);
  assert(sections.length > 0, 'fixture source should have an authoring section');
  const entrypoint = sections[0].source_span.resource;
  const sourceText = Buffer.from(resources[entrypoint]).toString('utf8');
  const sourceLines = sourceText.split('\n');
  const sectionForQuote = quote => {
    const line = sourceLines.findIndex(value => value.includes(quote));
    assert(line >= 0, `evidence quote is not present in ${entrypoint}: ${quote}`);
    const section = sections.find(item => item.source_span.resource === entrypoint
      && item.source_span.start_line <= line + 1 && item.source_span.end_line >= line + 1);
    assert(section, `evidence quote does not fall within a generated source section: ${quote}`);
    return section.section_id;
  };
  const dependencies = runtime_dependencies.map(item => ({
    key: item.key,
    executable: item.executable,
    phase: item.phase,
    trigger: item.trigger ?? '',
    source_section: sectionForQuote(item.quote),
    evidence: { resource: entrypoint, quote: item.quote },
    activity_keys: ['work'],
  }));
  const sectionIds = sections.map(item => item.section_id);
  return {
    contract: SEMANTIC_BLUEPRINT_CONTRACT,
    purpose: 'Apply the pinned source instructions to the supplied task.',
    source_dispositions: sections.map(item => ({
      section_id: item.section_id,
      disposition: 'workflow',
      activity_keys: ['work'],
      note: 'Required source instructions are handled by the compiled work activity.',
    })),
    requirement_assignments: [],
    runtime_dependencies: dependencies,
    records: [], lists: [], enums: [],
    activities: [{
      key: 'work', instructions: 'Perform the source-defined operation on the supplied task.',
      profile: 'main_write', source_sections: sectionIds, inputs: [],
      outputs: [{ name: 'result', kind: 'text', values: [], type_ref: '' }], tool: '',
    }],
    approvals: [], sequences: [], parallels: [], choices: [],
  };
}

async function seedFromBrief(service, workflow_id, brief) {
  return service.call('build_workflow', { workflow_id, name: `Fixture ${workflow_id}`, brief });
}

async function seedFromSkill(f, workflow_id, skillText) {
  const folder = join(f.root, `skill-${workflow_id}`);
  await mkdir(folder);
  await writeFile(join(folder, 'SKILL.md'), skillText, 'utf8');
  const inventory = await f.service.call('skill_inventory', { discovery: 'folders', folder });
  assert.equal(inventory.entries.length, 1);
  return f.service.call('import_skill', {
    discovery: 'folders', folder, skill_id: inventory.entries[0].id, workflow_id,
  });
}

async function compileAndSave(service, pack, blueprint, storedId) {
  const { store } = await service.open();
  const resources = await store.resources(pack.workflow.id, pack.revision_hash);
  const result = new WorkflowForge().compile({ pack, resources, blueprint, context: authoringContext });
  const saved = await store.save(pack.workflow.id, result.compiled.workflow, {
    expected_revision: pack.revision_hash,
    resources,
  });
  const runtimePack = storedId === undefined ? saved : await store.create(
    { ...structuredClone(result.compiled.workflow), id: storedId },
    { resources, provenance: { kind: 'authoring_dependency_test_fixture' }, import_report: {} },
  );
  return { result, saved, runtimePack };
}

async function writeVersionTool(directory, name, version) {
  const path = join(directory, name + (process.platform === 'win32' ? '.cmd' : ''));
  const contents = process.platform === 'win32'
    ? `@echo off\r\necho ${name} ${version}\r\n`
    : `#!/bin/sh\necho ${name} ${version}\n`;
  await writeFile(path, contents, 'utf8');
  if (process.platform !== 'win32') await chmod(path, 0o755);
  return path;
}

function exportableDraft(id, executables) {
  const workflow = createDraft(id, 'Portable runtime dependency export');
  workflow.requirements.executables = structuredClone(executables);
  return workflow;
}

test('brief and Skill authoring compile portable dependency phases into runtime preparation without adding a dependency Agent', async t => {
  const f = await fixture(t);

  const briefText = [
    '# Workflow',
    '',
    '## Process',
    '',
    'Always run framecraft >=3.2 to render the requested animation.',
    '',
    '## Optional preview',
    '',
    'When a preview is separately requested, run preview-slicer >=1.4 for the requested preview.',
    '',
    '## Artifact execution',
    '',
    'When the generated Python artifact is explicitly requested, use Python >=3.11 with the yaml module.',
  ].join('\n');
  const briefPack = await seedFromBrief(f.service, 'brief-dependency-arbitrary-cli', briefText);
  const briefSource = await f.service.open().then(({ store }) => store.resources(briefPack.workflow.id, briefPack.revision_hash));
  const briefBlueprint = compactBlueprint(briefSource, [
    { key: 'render_cli', executable: { name: 'framecraft', version: '>=3.2' }, phase: 'unconditional', quote: 'Always run framecraft >=3.2 to render the requested animation.' },
    { key: 'optional_preview', executable: { name: 'preview-slicer', version: '>=1.4' }, phase: 'conditional', trigger: 'only when a preview is separately requested', quote: 'When a preview is separately requested, run preview-slicer >=1.4 for the requested preview.' },
    { key: 'python_artifact', executable: { name: 'python', version: '>=3.11', python_modules: ['yaml'] }, phase: 'artifact_only', trigger: 'only when the generated Python artifact is explicitly requested', quote: 'When the generated Python artifact is explicitly requested, use Python >=3.11 with the yaml module.' },
  ]);
  const briefCompiled = new WorkflowForge().compile({ pack: briefPack, resources: briefSource, blueprint: briefBlueprint, context: authoringContext });
  assert.deepEqual(briefCompiled.compiled.workflow.requirements.executables, [{ name: 'framecraft', version: '>=3.2.0' }]);
  const briefDecisions = briefCompiled.proposal.source_requirements
    .filter(item => item.requirement_kind === 'dependency')
    .map(item => [item.details.executable, item.details.phase]);
  assert(briefDecisions.some(([name, phase]) => name === 'framecraft' && phase === 'unconditional'));
  assert(briefDecisions.some(([name, phase]) => name === 'preview-slicer' && phase === 'conditional'));
  assert(briefDecisions.some(([name, phase]) => name === 'python' && phase === 'artifact_only'));
  assert(!briefCompiled.proposal.required_executables.some(item => item.name === 'python' || item.name === 'preview-slicer'));
  assert.deepEqual(briefCompiled.proposal.required_executables.map(item => item.name), ['framecraft']);
  assert.equal(briefCompiled.proposal.nodes.filter(node => node.type === 'agent').length, 1);
  assert.equal(briefCompiled.compiled.workflow.nodes.filter(node => node.type === 'agent').length, 2,
    'the compiled work and final acceptance agents are sufficient; dependency declaration adds no LLM node');

  const missingPack = await compileAndSave(f.service, briefPack, briefBlueprint, 'compiled-arbitrary-runtime-check');
  const environment = await f.service.call('prepare_environment', { workflow_id: missingPack.runtimePack.workflow.id });
  assert.equal(environment.status, 'installation_approval_required');
  assert.deepEqual(environment.requirements.executables, [{ name: 'framecraft', version: '>=3.2.0' }]);
  assert.deepEqual(environment.missing, ['framecraft'], 'arbitrary CLI names reach the real host runtime detector without a catalog lookup');
  assert.equal(environment.installation_performed, false);
  const startup = await f.service.call('begin_main', {
    workflow_id: missingPack.runtimePack.workflow.id,
    revision_hash: missingPack.runtimePack.revision_hash,
    workspace: f.workspace,
    access: 'read_only',
    main_actor: 'dependency-fixture',
    inputs: { task: 'Exercise the pre-start dependency gate.' },
  });
  assert.equal(startup.status, 'environment_attention');
  assert.deepEqual(startup.environment.missing, ['framecraft']);
  assert.equal((await f.service.call('runs')).length, 0, 'missing dependencies block startup before a Run is created');

  const skillText = [
    '---',
    'name: portable-runtime-fixture',
    'description: Exercise portable dependency declarations.',
    '---',
    '# Workflow',
    '',
    '## Parse',
    '',
    'Use the Python >=3.11 interpreter with the yaml module to parse the supplied manifest.',
  ].join('\n');
  const skillPack = await seedFromSkill(f, 'skill-python-descriptor', skillText);
  const skillSource = await f.service.open().then(({ store }) => store.resources(skillPack.workflow.id, skillPack.revision_hash));
  const pythonQuote = 'Use the Python >=3.11 interpreter with the yaml module to parse the supplied manifest.';
  const skillBlueprint = compactBlueprint(skillSource, [
    { key: 'python_parse', executable: { name: 'python', version: '>=3.11', python_modules: ['yaml'] }, phase: 'unconditional', quote: pythonQuote },
  ]);
  const skillCompiled = new WorkflowForge().compile({ pack: skillPack, resources: skillSource, blueprint: skillBlueprint, context: authoringContext });
  assert.deepEqual(skillCompiled.compiled.workflow.requirements.executables, [
    { name: 'python', version: '>=3.11.0', python_modules: ['yaml'] },
  ]);
  assert(skillCompiled.proposal.source_requirements.some(item => item.requirement_kind === 'dependency'
    && item.details.executable === 'python' && item.details.phase === 'unconditional'));
  assert.deepEqual(skillCompiled.proposal.required_executables.map(item => ({
    name: item.name, version: item.version, python_modules: item.python_modules,
  })), [{ name: 'python', version: '>=3.11.0', python_modules: ['yaml'] }]);
  assert.equal(skillCompiled.proposal.nodes.filter(node => node.type === 'agent').length, 1);

  const emptyPack = await seedFromBrief(f.service, 'brief-no-dependency-gate', '# Workflow\n\n## Inspect\n\nInspect the supplied text and return a concise report.');
  const emptyResources = await f.service.open().then(({ store }) => store.resources(emptyPack.workflow.id, emptyPack.revision_hash));
  const emptyBlueprint = compactBlueprint(emptyResources, []);
  const empty = await compileAndSave(f.service, emptyPack, emptyBlueprint);
  assert.deepEqual(empty.result.compiled.workflow.requirements.executables, []);
  const noGate = await f.service.call('prepare_environment', { workflow_id: empty.saved.workflow.id, revision_hash: empty.saved.revision_hash });
  assert.equal(noGate.status, 'ready');
  assert.deepEqual(noGate.tools, []);

  const bindingDirectory = join(f.root, 'registered-tools');
  await mkdir(bindingDirectory);
  const registeredPath = await writeVersionTool(bindingDirectory, 'framecraft', '3.2.1');
  const candidate = await f.service.call('register_runtime_dependency', {
    requirement: { name: 'framecraft', version: '>=3.2' }, path: registeredPath,
  }, { human: true });
  assert.equal(candidate.path, registeredPath);
  const registeredEnvironment = await f.service.call('prepare_environment', { workflow_id: missingPack.runtimePack.workflow.id });
  assert.equal(registeredEnvironment.status, 'ready');
  assert.equal(registeredEnvironment.tools[0].path, registeredPath);
  // Private source snapshots are intentionally not exportable; carry the exact
  // compiled dependency manifest into a public Draft to test the package boundary.
  const compiledDependencies = briefCompiled.compiled.workflow.requirements.executables;
  const portable = await f.service.call('create', {
    workflow: exportableDraft('portable-runtime-export', compiledDependencies),
  }, { human: true });
  const bundle = await f.service.call('export_workflow_package', {
    workflow_id: portable.workflow.id, revision_hash: portable.revision_hash,
  });
  assert.deepEqual(bundle.dependencies.executables, compiledDependencies);
  const serialized = JSON.stringify(bundle);
  assert.equal(serialized.includes(registeredPath), false, 'host-local dependency binding must not cross the package boundary');
  assert.equal(serialized.includes('host-runtime-registry.json'), false);
});
