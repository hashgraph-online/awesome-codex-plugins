import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import test from 'node:test';
import { GitWorktrees } from '../lib/parallel/git-worktrees.mjs';

import {
  loadConfig,
  ensureConfigFile,
  resolveConfigPath,
  sanitizeConfig,
  saveConfig,
  validateConfig,
} from '../lib/config.mjs';
import { resolveSelection } from '../lib/control.mjs';
import { buildProviderAdapter } from '../lib/providers.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

async function fixture() {
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-config-'));
  const configPath = join(dir, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  return { dir, configPath, config };
}

test('built-in native Providers contain one selectable entry per real model and effort', async () => {
  const { config } = await fixture();
  const providers = Object.fromEntries(config.providers.map(provider => [provider.id, provider]));
  assert.deepEqual(config.providers.filter(provider => provider.kind === 'native_agent').map(provider => provider.id),
    ['native-luna', 'native-sol', 'native-astra']);
  for (const [id, model, effort] of [
    ['native-luna', 'gpt-6-luna', 'max'],
    ['native-sol', 'gpt-6.1-sol', 'high'],
    ['native-astra', 'gpt-6-astra', 'medium'],
  ]) assert.deepEqual([providers[id].config.model, providers[id].config.reasoning_effort], [model, effort]);
  for (const id of ['native-luna', 'native-sol', 'native-astra']) {
    assert.equal(providers[id].config.agent_type, 'default', id);
    assert.equal(providers[id].config.role, 'advisor', id);
  }
  const web = buildProviderAdapter(providers['chatgpt-web-pro'], { access: 'read_only' });
  assert.deepEqual([web.skill, web.review_route, web.packet_format, web.review_role],
    ['chatgpt-agent', 'packet.inspect', 'zip', 'reviewer']);
  assert.equal(providers['grok-local'].config.model, undefined);
  assert.equal(providers['cursor-local'].config.model, undefined);
});

test('existing built-in native Providers migrate to truthful model-only identities', async (t) => {
  const { dir, configPath, config } = await fixture();
  t.after(() => rm(dir, { recursive: true, force: true }));
  const expected = new Map(config.providers
    .filter((provider) => provider.kind === 'native_agent')
    .map((provider) => [provider.id, provider.config.agent_type]));
  for (const provider of config.providers) {
    if (expected.has(provider.id)) {
      provider.config.agent_type = 'default';
      provider.name = 'Legacy alias';
      provider.description = 'Dedicated GPT-6 Astra / Medium planner.';
    }
  }
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`, 'utf8');
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  for (const provider of migrated.providers.filter((provider) => expected.has(provider.id))) {
    assert.equal(provider.config.agent_type, expected.get(provider.id), provider.id);
    assert.match(provider.name, /^GPT-6(?:\.1)? (Luna|Sol|Astra) \/ (Max|High|Medium)$/, provider.id);
  }
  const persisted = JSON.parse(await readFile(configPath, 'utf8'));
  for (const provider of persisted.providers.filter((provider) => expected.has(provider.id))) {
    assert.equal(provider.config.agent_type, expected.get(provider.id), provider.id);
  }
});

test('version-7 active config collapses retired purpose aliases into three model Providers', async (t) => {
  const { dir, configPath, config } = await fixture();
  t.after(() => rm(dir, { recursive: true, force: true }));
  const luna = config.providers.find(provider => provider.id === 'native-luna');
  const sol = config.providers.find(provider => provider.id === 'native-sol');
  for (const retiredId of ['native-terra', 'native-luna-complex', 'native-authoring-astra-low', 'native-astra-solver']) {
    const retired = structuredClone(luna); retired.id = retiredId;
    Object.assign(retired.config, { model: 'gpt-6-astra', reasoning_effort: 'low', fresh_context: false });
    config.providers.unshift(retired);
  }
  for (const retiredId of ['native-reviewer-low', 'native-generation-reviewer']) {
    const retired = structuredClone(sol); retired.id = retiredId;
    Object.assign(retired.config, { model: 'gpt-6-astra', reasoning_effort: 'low' });
    config.providers.unshift(retired);
  }
  config.version = 7;
  sol.config.model = 'gpt-6-sol';
  sol.name = 'GPT-6 Sol / High';
  config.strict_executor = { main_model: 'gpt-6-sol', main_reasoning_effort: 'medium' };
  delete config.task_types;
  config.workflow_store = { schema_version: 1, relative_path: 'workflows-v7' };
  config.legacy_mapping = {};
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`, 'utf8');

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const ids = migrated.providers.map(provider => provider.id);
  for (const retired of ['native-terra', 'native-luna-complex', 'native-luna-planner', 'native-luna-solver', 'native-reviewer-low', 'native-generation-reviewer', 'native-authoring-astra-low', 'native-astra-solver']) {
    assert.equal(ids.includes(retired), false, retired);
  }
  assert.equal(new Set(ids).size, ids.length);
  const providers = Object.fromEntries(migrated.providers.map(provider => [provider.id, provider]));
  assert.deepEqual([providers['native-luna'].config.model, providers['native-luna'].config.reasoning_effort, providers['native-luna'].config.fresh_context],
    ['gpt-6-luna', 'max', true]);
  assert.deepEqual([providers['native-sol'].config.model, providers['native-sol'].config.reasoning_effort], ['gpt-6.1-sol', 'high']);
  assert.deepEqual([providers['native-astra'].config.model, providers['native-astra'].config.reasoning_effort], ['gpt-6-astra', 'medium']);
  assert.equal(providers['native-sol'].name, 'GPT-6.1 Sol / High');
  assert.equal(migrated.strict_executor.main_model, '');
  assert.equal(migrated.strict_executor.main_reasoning_effort, '');
  assert.deepEqual(JSON.parse(await readFile(configPath, 'utf8')), migrated);
});

test('current version-6 task routes migrate retired Provider IDs before validation', async (t) => {
  const { dir, configPath, config } = await fixture();
  t.after(() => rm(dir, { recursive: true, force: true }));
  config.providers.find(provider => provider.id === 'native-luna').id = 'native-terra';
  for (const taskType of config.task_types) {
    for (const stage of taskType.stages) {
      if (stage.provider_id === 'native-luna') stage.provider_id = 'native-terra';
    }
  }
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`, 'utf8');
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.providers.some(provider => provider.id === 'native-terra'), false);
  assert.equal(migrated.task_types.flatMap(taskType => taskType.stages)
    .some(stage => stage.provider_id === 'native-terra'), false);
  assert(migrated.task_types.flatMap(taskType => taskType.stages)
    .some(stage => stage.provider_id === 'native-sol'));
});

test('current config validation rejects retired Provider IDs outside the load migration boundary', async () => {
  const { config } = await fixture();
  config.providers.find(provider => provider.id === 'native-luna').id = 'native-terra';
  assert.throws(() => validateConfig(config), /retired native provider id/);
});

test('native models are write-capable by default while each node selects its sandbox', async () => {
  const { config } = await fixture();
  for (const provider of config.providers.filter(item => item.kind === 'native_agent')) {
    assert.equal(provider.capabilities.read, true, provider.id);
    assert.equal(provider.capabilities.write, true, provider.id);
    assert.equal(buildProviderAdapter(provider, { access: 'read_only' }).requested_sandbox, 'read-only', provider.id);
    assert.equal(buildProviderAdapter(provider, { access: 'bounded_write' }).requested_sandbox, 'workspace-write', provider.id);
  }
  assert.equal(new Set(config.providers.map(provider => provider.name)).size, config.providers.length);
});

test('default config path is user-global and independent of the project directory', () => {
  const userHome = join(tmpdir(), 'sol-control-user');
  assert.equal(
    resolveConfigPath({}, userHome),
    join(userHome, '.codex', 'codex-agents-workflow', 'control-plane.json'),
  );
  assert.equal(
    resolveConfigPath({ CODEX_HOME: join(userHome, 'custom-codex-home') }, userHome),
    join(userHome, 'custom-codex-home', 'codex-agents-workflow', 'control-plane.json'),
  );
});

test('legacy SOL_CONTROL_CONFIG paths resolve into the canonical store', () => {
  const userHome = join(tmpdir(), 'sol-control-legacy-path');
  const legacy = join(userHome, '.codex', 'sol-advisor', 'control-plane.json');
  assert.equal(
    resolveConfigPath({ SOL_CONTROL_CONFIG: legacy }, userHome),
    join(userHome, '.codex', 'codex-agents-workflow', 'control-plane.json'),
  );
});

test('Windows legacy store path protection is case-insensitive', { skip: process.platform !== 'win32' }, () => {
  const userHome = join(tmpdir(), 'sol-control-legacy-case');
  for (const directory of ['sol-advisor', 'SOL-ADVISOR', 'Sol-Advisor']) {
    const legacy = join(userHome, directory, 'control-plane.json');
    assert.equal(
      resolveConfigPath({ SOL_CONTROL_CONFIG: legacy }, userHome),
      join(userHome, 'codex-agents-workflow', 'control-plane.json'),
    );
    assert.throws(
      () => resolveConfigPath({ CODEX_WORKFLOW_CONFIG: legacy }, userHome),
      /retired sol-advisor store/,
    );
  }
});

test('legacy store migration refuses to strand owned Git worktrees', async () => {
  const root = await mkdtemp(join(tmpdir(), 'sol-control-worktree-'));
  const legacy = join(root, 'sol-advisor');
  const canonical = join(root, 'codex-agents-workflow', 'control-plane.json');
  await mkdir(join(legacy, 'workflow-worktrees'), { recursive: true });
  await writeFile(join(legacy, 'workflow-worktrees', 'owner-run.json'), '{}');
  await assert.rejects(
    ensureConfigFile({ configPath: canonical, defaultConfigPath: DEFAULT_CONFIG_PATH }),
    /owned Git worktrees exist/,
  );
  await rm(root, { recursive: true, force: true });
});

test('legacy store migration refuses to split data when the canonical directory already exists', async () => {
  const root = await mkdtemp(join(tmpdir(), 'sol-control-store-conflict-'));
  const legacy = join(root, 'sol-advisor');
  const canonical = join(root, 'codex-agents-workflow', 'control-plane.json');
  await mkdir(legacy, { recursive: true });
  await writeFile(join(legacy, 'control-plane.json'), '{}');
  await mkdir(join(root, 'codex-agents-workflow'), { recursive: true });
  await assert.rejects(
    ensureConfigFile({ configPath: canonical, defaultConfigPath: DEFAULT_CONFIG_PATH }),
    /canonical store already exists without its configuration/,
  );
  await rm(root, { recursive: true, force: true });
});

test('bundled defaults use delegate for light work and full for difficult work', async () => {
  const { config } = await fixture();
  assert.equal(config.version, 6);
  assert.equal('scenarios' in config, false);
  assert.ok(config.providers.filter((provider) => provider.kind === 'native_agent')
    .every((provider) => provider.config.inactivity_timeout_ms === 0));
  assert.ok(config.providers.filter((provider) => provider.kind === 'builtin_connector')
    .every((provider) => provider.config.task_timeout_ms === 0));
  const external = config.providers.filter((provider) => provider.kind !== 'native_agent');
  assert.ok(external.length >= 4);
  assert.ok(external.every((provider) => provider.enabled === false));
  const webReview = config.providers.find((provider) => provider.id === 'chatgpt-web-pro');
  assert.equal(webReview.config.model_label, '');
  assert.equal('reasoning_effort' in webReview.config, false);
  assert.equal(sanitizeConfig(config, { env: {} }).providers
    .find((provider) => provider.id === 'chatgpt-web-pro').model_label, null);
  const bounded = config.task_types.find((taskType) => taskType.id === 'bounded-code-change');
  assert.equal(bounded.route, 'delegate');
  assert.deepEqual(bounded.stages.map((stage) => [stage.id, stage.role, stage.provider_id]), [
    ['implementation', 'implementer', 'native-luna'],
  ]);
  const review = config.task_types.find((taskType) => taskType.id === 'cross-review');
  assert.deepEqual(review.stages.map((stage) => [stage.id, stage.role, stage.provider_id]), [
    ['review', 'reviewer', 'grok-local'],
  ]);
  const analysis = config.task_types.find((taskType) => taskType.id === 'repository-analysis');
  assert.deepEqual(analysis.stages.map((stage) => [stage.role, stage.access]), [
    ['implementer', 'read_only'],
  ]);
  const full = config.task_types.find((taskType) => taskType.id === 'implementation-with-review');
  assert.deepEqual(full.stages.map((stage) => [stage.id, stage.role]), [
    ['implementation', 'implementer'], ['review', 'reviewer'],
  ]);
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  assert.equal(difficult.route, 'delegate');
  assert.deepEqual(difficult.stages.map((stage) => stage.id), ['implementation']);
  const solver = config.task_types.find((taskType) => taskType.id === 'hard-problem-solver');
  assert.deepEqual(solver.stages.map((stage) => [stage.provider_id, stage.access]), [['native-astra', 'bounded_write']]);
  const gptReviewer = config.task_types.find((taskType) => taskType.id === 'hard-path-web-advice');
  assert.equal(gptReviewer.name, 'GPT reviewer');
  assert.equal(gptReviewer.stages[0].provider_id, 'chatgpt-web-pro');
  for (const taskType of config.task_types.filter(taskType => taskType.id !== 'hard-path-web-advice')) {
    const providerSpecificText = `${taskType.id} ${taskType.name} ${taskType.description} ${taskType.tags.join(' ')}`;
    assert.doesNotMatch(providerSpecificText, /cursor|grok|chatgpt|luna|terra|openai/i);
  }
});

test('task type route is derived from stages and cannot conflict with them', async () => {
  const { config } = await fixture();
  const bounded = config.task_types.find((taskType) => taskType.id === 'bounded-code-change');
  bounded.route = 'solo';
  assert.equal(validateConfig(config).task_types
    .find((taskType) => taskType.id === 'bounded-code-change').route, 'delegate');
});

test('sanitized status omits templates, endpoints, and credential names', async () => {
  const { config } = await fixture();
  const status = sanitizeConfig(config, { env: {} });
  const text = JSON.stringify(status);
  assert.doesNotMatch(text, /"template"\s*:/);
  assert.doesNotMatch(text, /example\.invalid/);
  assert.doesNotMatch(text, /SOL_CONTROL_CUSTOM_API_KEY/);
  assert.doesNotMatch(text, /CONSTRAINTS AND OWNERSHIP/);
  assert.match(text, /bounded-code-change/);
  assert.match(text, /template_revision/);
  const bounded = status.task_types.find((taskType) => taskType.id === 'bounded-code-change');
  assert.equal(bounded.stages[0].requires_user_approval, false);
});

test('bundled approval gates default off and only explicit provider or stage opt-in requires approval', async () => {
  const { configPath, config } = await fixture();
  assert.equal(config.providers.some((provider) => provider.requires_user_approval), false);
  assert.equal(config.task_types.some((taskType) =>
    taskType.stages.some((stage) => stage.requires_user_approval)), false);

  const unguarded = await resolveSelection({
    task_type_id: 'bounded-code-change',
    task: 'Implement the parser guard.',
  }, { configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
  assert.equal(unguarded.result.stages[0].approval_required, false);

  const bounded = config.task_types.find((taskType) => taskType.id === 'bounded-code-change');
  bounded.stages[0].requires_user_approval = true;
  await saveConfig(config, { configPath });
  await assert.rejects(
    resolveSelection({ task_type_id: 'bounded-code-change', task: 'Implement it.' }, {
      configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    }),
    /requires explicit current-task user approval/,
  );

  bounded.stages[0].requires_user_approval = false;
  config.providers.find((provider) => provider.id === 'native-luna').requires_user_approval = true;
  await saveConfig(config, { configPath });
  await assert.rejects(
    resolveSelection({ task_type_id: 'bounded-code-change', task: 'Implement it.' }, {
      configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    }),
    /requires explicit current-task user approval/,
  );
});

test('resolution returns only the selected compiled prompt and adapter', async () => {
  const { configPath } = await fixture();
  const { result } = await resolveSelection({
    task_type_id: 'bounded-code-change',
    task: 'Implement the parser guard.',
    context: { files: ['src/parser.ts'] },
    constraints: 'Own only src/parser.ts.',
    verification: 'Run npm test.',
    user_approved: true,
  }, { configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
  assert.equal(result.stages[0].adapter.execution, 'native_agent');
  assert.equal(result.stages[0].adapter.agent_type, 'default');
  assert.match(result.stages[0].compiled_prompt, /Implement the parser guard/);
  assert.match(result.stages[0].compiled_prompt, /src\/parser\.ts/);
  assert.doesNotMatch(JSON.stringify(result), /Hard-path ChatGPT/);
  assert.doesNotMatch(result.stages[0].compiled_prompt, /{{task}}/);
});

test('disabled and approval-gated routes fail closed', async () => {
  const { configPath, config } = await fixture();
  await assert.rejects(
    resolveSelection({ task_type_id: 'hard-path-web-advice', task: 'Review the blocker.' }, {
      configPath,
      defaultConfigPath: DEFAULT_CONFIG_PATH,
      env: {},
    }),
    /task type is disabled/,
  );

  config.providers.find((provider) => provider.id === 'chatgpt-web-pro').enabled = true;
  const hardPath = config.task_types.find((taskType) => taskType.id === 'hard-path-web-advice');
  hardPath.enabled = true;
  hardPath.stages[0].requires_user_approval = true;
  await saveConfig(config, { configPath });
  await assert.rejects(
    resolveSelection({ task_type_id: 'hard-path-web-advice', task: 'Review the blocker.' }, {
      configPath,
      defaultConfigPath: DEFAULT_CONFIG_PATH,
      env: {},
    }),
    /requires explicit current-task user approval/,
  );
  const { result } = await resolveSelection({
    task_type_id: 'hard-path-web-advice',
    task: 'Review the blocker.',
    user_approved: true,
  }, { configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
  assert.equal(result.stages[0].adapter.execution, 'packet_review');
  assert.equal(result.stages[0].adapter.model_label, null);
});

test('environment kill switch cannot be bypassed', async () => {
  const { configPath } = await fixture();
  await assert.rejects(
    resolveSelection({ task_type_id: 'bounded-code-change', task: 'Change one file.' }, {
      configPath,
      defaultConfigPath: DEFAULT_CONFIG_PATH,
      env: { SOL_CONTROL_DISABLED: '1' },
    }),
    /disabled by CODEX_WORKFLOW_DISABLED/,
  );
});

test('configuration rejects stored MCP secrets and unknown placeholders', async () => {
  const { config } = await fixture();
  const secretConfig = structuredClone(config);
  secretConfig.providers.find((provider) => provider.id === 'cursor-local').config.api_token = 'bad';
  assert.throws(() => validateConfig(secretConfig), /looks like a stored secret/);

  const placeholderConfig = structuredClone(config);
  placeholderConfig.task_types[0].stages[0].template += '\n{{unknown_field}}';
  assert.throws(() => validateConfig(placeholderConfig), /unsupported placeholder/);

});


function asVersion2(config) {
  return {
    version: 2,
    global: structuredClone(config.global),
    providers: structuredClone(config.providers),
    scenarios: config.task_types.map((taskType) => {
      const stage = taskType.stages[0];
      return {
        id: taskType.id,
        name: taskType.name,
        enabled: taskType.enabled,
        description: taskType.description,
        route: taskType.route,
        provider_id: stage?.provider_id || 'native-luna',
        read_only: stage ? stage.access === 'read_only' : true,
        requires_user_approval: stage?.requires_user_approval || false,
        tags: taskType.tags,
        template: stage?.template || 'Handle {{task}}.',
      };
    }),
  };
}

test('version-2 config migrates task types and removes untouched disabled provider-specific defaults', async () => {
  const { configPath, config } = await fixture();
  const legacy = asVersion2(config);
  const brainstorm = legacy.scenarios.find((scenario) => scenario.id === 'brainstorm');
  brainstorm.description = 'USER CUSTOM DESCRIPTION';
  legacy.scenarios.push({
    id: 'cursor-bounded-change', name: 'Cursor bounded repository change', enabled: false,
    description: 'old bundled task', route: 'delegate', provider_id: 'cursor-local',
    read_only: false, requires_user_approval: true, tags: ['cursor'], template: 'Do {{task}}.',
  });
  await writeFile(configPath, `${JSON.stringify(legacy, null, 2)}\n`);

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.version, 6);
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'brainstorm').description,
    'USER CUSTOM DESCRIPTION');
  assert.equal(migrated.task_types.some((taskType) => taskType.id === 'cursor-bounded-change'), false);
  assert.equal(JSON.parse(await readFile(configPath, 'utf8')).version, 6);
});

test('version-2 full route migrates disabled with a separate read-only reviewer', async () => {
  const { configPath, config } = await fixture();
  const legacy = asVersion2(config);
  legacy.scenarios.push({
    id: 'legacy-full', name: 'Legacy full', enabled: true, description: 'Needs review.',
    route: 'full', provider_id: 'native-luna', read_only: false,
    requires_user_approval: true, tags: ['legacy'], template: 'Implement {{task}}.',
  });
  await writeFile(configPath, `${JSON.stringify(legacy, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const taskType = migrated.task_types.find((item) => item.id === 'legacy-full');
  assert.equal(taskType.enabled, false);
  assert.deepEqual(taskType.stages.map((stage) => [stage.id, stage.provider_id, stage.access]), [
    ['implementation', 'native-luna', 'bounded_write'],
    ['review', 'native-sol', 'read_only'],
  ]);
});

test('version-3 customized difficult implementation preserves its route without injecting a review binding', async () => {
  const { configPath, config } = await fixture();
  config.version = 3;
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  difficult.stages[0].template = 'CUSTOM IMPLEMENTATION {{task}} {{context}} {{constraints}} {{verification}}';
  const crossReview = config.task_types.find((taskType) => taskType.id === 'cross-review');
  crossReview.stages[0].provider_id = 'grok-local';
  config.providers.find((provider) => provider.id === 'grok-local').enabled = true;
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.version, 6);
  assert.deepEqual(migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change')
    .stages.map((stage) => [stage.id, stage.provider_id]), [['implementation', 'native-sol']]);
  assert.match(migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change')
    .stages[0].template, /CUSTOM IMPLEMENTATION/);
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'cross-review')
    .stages[0].provider_id, 'grok-local');
  assert.equal(migrated.providers.find((provider) => provider.id === 'grok-local').enabled, true);
});

test('version-3 customized difficult Task Type keeps its user-owned workflow', async () => {
  const { configPath, config } = await fixture();
  config.version = 3;
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  difficult.description = 'User intentionally keeps this as one implementation Stage.';
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.version, 6);
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change').route,
    'delegate');
});

test('version-4 customized difficult workflow remains unchanged when it is not the pristine historical default', async () => {
  const { configPath, config } = await fixture();
  config.version = 4;
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  difficult.stages[0].template = 'PREVIOUSLY CUSTOMIZED {{task}} {{context}} {{constraints}} {{verification}}';
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const migratedDifficult = migrated.task_types.find(
    (taskType) => taskType.id === 'judgment-heavy-change');
  assert.equal(migrated.version, 6);
  assert.equal(migratedDifficult.route, 'delegate');
  assert.deepEqual(migratedDifficult.stages.map((stage) => stage.id), ['implementation']);
  assert.match(migratedDifficult.stages[0].template, /PREVIOUSLY CUSTOMIZED/);
});

test('version-4 migration never injects a reviewer binding absent from a customized provider set', async () => {
  const { configPath, config } = await fixture();
  config.version = 4;
  config.task_types.find(taskType => taskType.id === 'cross-review').stages[0].provider_id = 'native-sol';
  const reviewer = config.providers.find((provider) => provider.id === 'native-sol');
  reviewer.id = 'my-reviewer';
  for (const taskType of config.task_types) {
    for (const stage of taskType.stages) {
      if (stage.provider_id === 'native-sol') stage.provider_id = 'my-reviewer';
    }
  }
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change').route, 'delegate');
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'cross-review').stages[0].provider_id, 'my-reviewer');
});

test('version-4 migration does not inject a reviewer incompatible with a customized provider', async () => {
  const { configPath, config } = await fixture();
  config.version = 4;
  const reviewer = config.providers.find((provider) => provider.id === 'native-sol');
  reviewer.config.role = 'implementer';
  for (const taskType of config.task_types) {
    for (const stage of taskType.stages) {
      if (stage.provider_id === 'native-sol') stage.provider_id = 'grok-local';
    }
  }
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const migratedDifficult = migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  assert.equal(migratedDifficult.route, 'delegate');
  assert.deepEqual(migratedDifficult.stages.map((stage) => stage.id), ['implementation']);
});

test('version-4 migration does not inject a reviewer when the provider kind is customized', async () => {
  const { configPath, config } = await fixture();
  config.version = 4;
  const reviewer = config.providers.find((provider) => provider.id === 'native-sol');
  reviewer.kind = 'builtin_connector';
  reviewer.config = { connector: 'grok_acp', binary_env: 'GROK_BIN', transport: 'leader_acp_stdio' };
  for (const taskType of config.task_types) {
    for (const stage of taskType.stages) {
      if (stage.provider_id === 'native-sol') stage.provider_id = 'grok-local';
    }
  }
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const migratedDifficult = migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  assert.equal(migratedDifficult.route, 'delegate');
  assert.deepEqual(migratedDifficult.stages.map((stage) => stage.id), ['implementation']);
});

test('version-4 migration does not inject a disabled reviewer provider', async () => {
  const { configPath, config } = await fixture();
  config.version = 4;
  const reviewer = config.providers.find((provider) => provider.id === 'native-sol');
  reviewer.enabled = false;
  for (const taskType of config.task_types) {
    for (const stage of taskType.stages) {
      if (stage.provider_id === 'native-sol') stage.provider_id = 'grok-local';
    }
  }
  const difficult = config.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  difficult.route = 'delegate';
  difficult.stages = difficult.stages.slice(0, 1);
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const migratedDifficult = migrated.task_types.find((taskType) => taskType.id === 'judgment-heavy-change');
  assert.equal(migratedDifficult.route, 'delegate');
  assert.deepEqual(migratedDifficult.stages.map((stage) => stage.id), ['implementation']);
});

test('version-5 migration preserves all persisted approval gates and custom opt-ins', async () => {
  const { configPath, config } = await fixture();
  config.version = 5;
  config.providers.find((provider) => provider.id === 'cursor-local').requires_user_approval = true;
  config.providers.find((provider) => provider.id === 'native-luna').requires_user_approval = true;
  config.task_types.find((taskType) => taskType.id === 'hard-path-web-advice')
    .stages[0].requires_user_approval = true;
  config.task_types.push({
    id: 'custom-approval', name: 'Custom approval', enabled: false,
    description: 'User-owned opt-in approval fixture.', route: 'delegate', tags: ['custom'],
    stages: [{
      id: 'implementation', role: 'implementer', provider_id: 'native-luna',
      access: 'read_only', requires_user_approval: true,
      template: 'Inspect {{task}} with {{context}} under {{constraints}} and verify {{verification}}.',
    }],
  });
  await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);

  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.version, 6);
  assert.equal(migrated.providers.find((provider) => provider.id === 'cursor-local')
    .requires_user_approval, true);
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'hard-path-web-advice')
    .stages[0].requires_user_approval, true);
  assert.equal(migrated.providers.find((provider) => provider.id === 'native-luna')
    .requires_user_approval, true);
  assert.equal(migrated.task_types.find((taskType) => taskType.id === 'custom-approval')
    .stages[0].requires_user_approval, true);
});

test('full resolves implementation then review with pinned providers and no fallback', async () => {
  const { configPath, config } = await fixture();
  config.task_types.push({
    id: 'full-fixture', name: 'Full fixture', enabled: true,
    description: 'Two-stage test workflow.', route: 'full', tags: ['fixture'],
    stages: [
      {
        id: 'implementation', role: 'implementer', provider_id: 'native-luna',
        access: 'bounded_write', requires_user_approval: true,
        template: 'Implement {{task}} with {{context}} and {{constraints}}; verify {{verification}}.',
      },
      {
        id: 'review', role: 'reviewer', provider_id: 'native-sol',
        access: 'read_only', requires_user_approval: false,
        template: 'Review {{task}} with {{context}} and {{constraints}}; verify {{verification}}.',
      },
    ],
  });
  await saveConfig(config, { configPath });
  const { result } = await resolveSelection({
    task_type_id: 'full-fixture', task: 'Change and review.', user_approved: true,
  }, { configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {} });
  assert.deepEqual(result.stages.map((stage) => [stage.stage.id, stage.provider.id]), [
    ['implementation', 'native-luna'], ['review', 'native-sol'],
  ]);

  config.providers.find((provider) => provider.id === 'native-sol').enabled = false;
  await saveConfig(config, { configPath });
  await assert.rejects(
    resolveSelection({ task_type_id: 'full-fixture', task: 'Change and review.', user_approved: true }, {
      configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, env: {},
    }),
    /provider is disabled: native-sol/,
  );
});


test('version-1 migration adds both built-in connectors disabled when legacy config has only external descriptors', async () => {
  const { configPath, config } = await fixture();
  const legacy = asVersion2(config);
  legacy.version = 1;
  legacy.providers = legacy.providers.filter((provider) => !['cursor-local', 'grok-local'].includes(provider.id));
  await writeFile(configPath, `${JSON.stringify(legacy, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  for (const providerId of ['cursor-local', 'grok-local']) {
    const provider = migrated.providers.find((item) => item.id === providerId);
    assert.ok(provider);
    assert.equal(provider.enabled, false);
    assert.equal(provider.requires_user_approval, false);
    assert.equal(provider.capabilities.write, true);
  }
  assert.equal(migrated.version, 6);
});

test('version-1 migration preserves an existing Grok write capability policy', async () => {
  const { configPath, config } = await fixture();
  const legacy = asVersion2(config);
  legacy.version = 1;
  legacy.providers.find((provider) => provider.id === 'grok-local').capabilities.write = false;
  await writeFile(configPath, `${JSON.stringify(legacy, null, 2)}\n`);
  const migrated = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  assert.equal(migrated.providers.find((provider) => provider.id === 'grok-local').capabilities.write, false);
});


test('legacy relocation refuses real manager-owned Git worktrees before changing registrations', async t => {
  const root = await mkdtemp(join(tmpdir(), 'workflow-real-relocation-'));
  const workspace = join(root, 'repo'); await mkdir(workspace);
  const legacy = join(root, 'sol-advisor');
  const manager = await new GitWorktrees(join(legacy, 'workflow-worktrees')).initialize();
  await manager.git(workspace, ['init', '-b', 'main']);
  await writeFile(join(workspace, 'file.txt'), 'baseline');
  await manager.git(workspace, ['add', '--all']);
  await manager.git(workspace, ['commit', '-m', 'Fixture']);
  const base = await manager.inspect(workspace);
  const owned = await manager.create(base, 'relocation-fixture');
  t.after(async () => { await manager.remove(owned); await rm(root, { recursive: true }); });
  const before = await manager.git(workspace, ['worktree', 'list', '--porcelain']);
  const registration = await readFile(join(owned.workspace, '.git'), 'utf8');
  await assert.rejects(ensureConfigFile({ configPath: join(root, 'codex-agents-workflow', 'control-plane.json'), defaultConfigPath: DEFAULT_CONFIG_PATH }), /owned Git worktrees exist/);
  assert.deepEqual(await manager.git(workspace, ['worktree', 'list', '--porcelain']), before);
  assert.equal(await readFile(join(owned.workspace, '.git'), 'utf8'), registration);
  await manager.verify(owned);
});
